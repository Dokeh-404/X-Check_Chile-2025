import pandas as pd
import os
import requests
import time
import duckdb
from scraper import extract_data as run_scraper
from extractor import unlock_pdf, extract_names
from database import setup_database, insert_electores_batch, get_comuna_id, DB_FILE

# Directorios de trabajo
TEMP_RAW = os.path.join("data", "temp", "current_raw.pdf")
TEMP_UNLOCKED = os.path.join("data", "temp", "current_unlocked.pdf")
CSV_SOURCE = os.path.join("data", "processed", "padron_definitivo_2025.csv")

def is_comuna_processed(comuna_id):
    """Verifica si la comuna ya tiene registros en la base de datos."""
    if not os.path.exists(DB_FILE):
        return False
    con = duckdb.connect(DB_FILE)
    count = con.execute("SELECT count(*) FROM electores WHERE comuna_id = ?", [comuna_id]).fetchone()[0]
    con.close()
    return count > 0

def run_pipeline():
    """(Fase 4) Orquestador con Sistema de Checkpoints."""
    
    if not os.path.exists(CSV_SOURCE):
        run_scraper()
    
    setup_database(CSV_SOURCE)
    df = pd.read_csv(CSV_SOURCE)
    
    print(f"Estado inicial: {len(df)} comunas detectadas.")

    for idx, row in df.iterrows():
        region = row["Región"]
        comuna = row["Comuna"]
        url = row["Enlace de Descarga"]
        comuna_id = get_comuna_id(comuna, region)
        
        # --- LÓGICA DE CHECKPOINT ---
        if is_comuna_processed(comuna_id):
            print(f"--- [SKIP] {idx + 1}/{len(df)}: {comuna} ya procesada. Pasando a la siguiente...")
            continue
        
        print(f"--- [START] {idx + 1}/{len(df)}: {comuna} (ID: {comuna_id}) ---")
        
        try:
            # 1. Descargar
            print(f"Descargando {url}...")
            r = requests.get(url, stream=True, timeout=30)
            r.raise_for_status()
            with open(TEMP_RAW, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192): f.write(chunk)
            
            # 2. Desbloquear
            if unlock_pdf(TEMP_RAW, TEMP_UNLOCKED):
                # 3. Extraer Nombres
                print("Extrayendo nombres...")
                names = extract_names(TEMP_UNLOCKED)
                
                # 4. Insertar en DB (Transacción Atómica)
                if names:
                    print(f"Cargando {len(names)} registros...")
                    records = [(n, comuna_id) for n in names]
                    insert_electores_batch(records)
                    print(f"¡Éxito! Comuna {comuna} guardada.")
                
                # 5. Limpieza inmediata
                if os.path.exists(TEMP_RAW): os.remove(TEMP_RAW)
                if os.path.exists(TEMP_UNLOCKED): os.remove(TEMP_UNLOCKED)
                
            else:
                print(f"Fallo al desbloquear PDF de {comuna}")

        except Exception as e:
            print(f"Error procesando {comuna}: {e}")
            # Si falló, aseguramos limpieza para el siguiente intento
            if os.path.exists(TEMP_RAW): os.remove(TEMP_RAW)
            continue
        
        time.sleep(1) # Cortesía con el servidor del SERVEL

    print("\n--- PROCESO FINALIZADO ---")

if __name__ == "__main__":
    run_pipeline()
