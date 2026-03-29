import pandas as pd
import os
import requests
import time
import duckdb
from scraper import extract_data as run_scraper
from extractor import unlock_pdf, extract_names, get_expected_count
from database import setup_database, insert_electores_batch, get_comuna_id, log_extraction_status, DB_FILE

# Directorios de trabajo
TEMP_RAW = os.path.join("data", "temp", "current_raw.pdf")
TEMP_UNLOCKED = os.path.join("data", "temp", "current_unlocked.pdf")
CSV_SOURCE = os.path.join("data", "processed", "padron_definitivo_2025.csv")

def is_comuna_processed(comuna_id):
    if not os.path.exists(DB_FILE): return False
    con = duckdb.connect(DB_FILE)
    count = con.execute("SELECT count(*) FROM log_procesamiento WHERE comuna_id = ?", [comuna_id]).fetchone()[0]
    con.close()
    return count > 0

def run_pipeline():
    if not os.path.exists(CSV_SOURCE): run_scraper()
    setup_database(CSV_SOURCE)
    df = pd.read_csv(CSV_SOURCE)
    
    # FILTRO: Solo región de Arica y Parinacota (excluyendo la ciudad de Arica por ahora si lo deseas)
    # Para carga masiva TOTAL, simplemente comenta la siguiente línea
    # df = df[df["Región"].str.contains("Arica", case=False) & (df["Comuna"] != "Arica")]
    
    print(f"=== INICIANDO PIPELINE: {len(df)} comunas detectadas ===")

    for idx, row in df.iterrows():
        region, comuna, url = row["Región"], row["Comuna"], row["Enlace de Descarga"]
        comuna_id = get_comuna_id(comuna, region)
        
        if is_comuna_processed(comuna_id):
            print(f"--- [SKIP] {idx + 1}/{len(df)}: {comuna} ya procesada.")
            continue
        
        print(f"\n--- [START] {idx + 1}/{len(df)}: {comuna} ---")
        
        try:
            # 1. Descarga
            print(f"Descargando...")
            r = requests.get(url, stream=True, timeout=120)
            r.raise_for_status()
            with open(TEMP_RAW, "wb") as f:
                for chunk in r.iter_content(chunk_size=16384): f.write(chunk)
            
            # 2. Desbloqueo
            if unlock_pdf(TEMP_RAW, TEMP_UNLOCKED):
                # 3. Obtener Conteo Oficial (Validación)
                oficial = get_expected_count(TEMP_UNLOCKED)
                
                # 4. Extraer Nombres
                print(f"Extrayendo (Esperados: {oficial:,})...")
                names, n_pages = extract_names(TEMP_UNLOCKED)
                
                # 5. Inserción y Auditoría
                if names:
                    records = [(n, comuna_id) for n in names]
                    insert_electores_batch(records)
                    log_extraction_status(comuna_id, n_pages, len(names), oficial)
                    
                    diff = abs(len(names) - oficial)
                    status = "✅ OK" if diff == 0 else f"⚠ DIF: {diff}"
                    print(f"Guardado: {len(names):,} / {oficial:,} {status}")
                
                if os.path.exists(TEMP_RAW): os.remove(TEMP_RAW)
                if os.path.exists(TEMP_UNLOCKED): os.remove(TEMP_UNLOCKED)
                
            else:
                print(f"Fallo al desbloquear PDF de {comuna}")

        except Exception as e:
            print(f"Error en {comuna}: {e}")
            if os.path.exists(TEMP_RAW): os.remove(TEMP_RAW)
            continue
        
        time.sleep(1)

    print("\n--- PROCESO FINALIZADO ---")

if __name__ == "__main__":
    run_pipeline()
