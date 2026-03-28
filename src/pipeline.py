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
    if not os.path.exists(DB_FILE): return False
    con = duckdb.connect(DB_FILE)
    count = con.execute("SELECT count(*) FROM electores WHERE comuna_id = ?", [comuna_id]).fetchone()[0]
    con.close()
    return count > 0

def run_pipeline():
    if not os.path.exists(CSV_SOURCE): run_scraper()
    setup_database(CSV_SOURCE)
    df = pd.read_csv(CSV_SOURCE)
    
    # FILTRO: Solo comunas pequeñas de Arica y Parinacota para benchmark rápido
    df = df[df["Región"].str.contains("Arica", case=False)]
    
    print(f"=== INICIANDO BENCHMARK: Región de Arica y Parinacota ({len(df)} comunas) ===")
    
    total_start = time.time()
    stats = []

    for idx, row in df.iterrows():
        region, comuna, url = row["Región"], row["Comuna"], row["Enlace de Descarga"]
        comuna_id = get_comuna_id(comuna, region)
        
        if is_comuna_processed(comuna_id): continue
        
        print(f"\n> Procesando: {comuna}")
        
        try:
            # 1. Descarga
            t0 = time.time()
            r = requests.get(url, stream=True, timeout=60)
            r.raise_for_status()
            with open(TEMP_RAW, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192): f.write(chunk)
            t_download = time.time() - t0
            
            # 2. Desbloqueo y Extracción
            t0 = time.time()
            unlock_pdf(TEMP_RAW, TEMP_UNLOCKED)
            names = extract_names(TEMP_UNLOCKED)
            t_extract = time.time() - t0
            
            # 3. Inserción
            t0 = time.time()
            if names:
                records = [(n, comuna_id) for n in names]
                insert_electores_batch(records)
            t_insert = time.time() - t0
            
            stats.append({
                "comuna": comuna,
                "n_registros": len(names),
                "t_download": t_download,
                "t_extract": t_extract,
                "t_insert": t_insert,
                "t_total": t_download + t_extract + t_insert
            })
            
            print(f"  - Registros: {len(names):,}")
            print(f"  - Descarga:  {t_download:.2f}s")
            print(f"  - Extracción:{t_extract:.2f}s")
            print(f"  - Inserción: {t_insert:.2f}s")
            
            if os.path.exists(TEMP_RAW): os.remove(TEMP_RAW)
            if os.path.exists(TEMP_UNLOCKED): os.remove(TEMP_UNLOCKED)
            
        except Exception as e:
            print(f"  - Error en {comuna}: {e}")
            continue

    total_time = time.time() - total_start
    total_regs = sum(s["n_registros"] for s in stats)
    
    print("\n" + "="*50)
    print("REPORTE DE BENCHMARK REGIONAL")
    print("="*50)
    print(f"Total Registros: {total_regs:,}")
    print(f"Tiempo Total:    {total_time/60:.2f} minutos")
    print(f"Velocidad Media: {total_regs / total_time:.0f} registros/segundo")
    print("-" * 50)
    print(f"ESTIMACIÓN PARA CHILE (15,000,000 electores):")
    est_segundos = (total_time / total_regs) * 15000000
    print(f"Tiempo Estimado: {est_segundos/3600:.2f} horas")
    print("="*50)

if __name__ == "__main__":
    run_pipeline()
