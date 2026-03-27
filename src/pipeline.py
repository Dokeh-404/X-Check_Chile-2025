import pandas as pd
import os
import requests
import time
from scraper import extract_data as run_scraper
from extractor import unlock_pdf, extract_names
from database import setup_database, insert_many

# Directorios de trabajo
TEMP_RAW = os.path.join("data", "temp", "current_raw.pdf")
TEMP_UNLOCKED = os.path.join("data", "temp", "current_unlocked.pdf")
CSV_SOURCE = os.path.join("padron_definitivo_2025.csv")

def run_pipeline():
    """(Fase 4) Orquestador principal de descargas y extracción secuencial."""
    
    # Asegurar base de datos inicializada
    setup_database()

    # Cargar CSV con URLs
    if not os.path.exists(CSV_SOURCE):
        print(f"No existe el archivo de URLs {CSV_SOURCE}. Ejecuta scraper.py primero.")
        return

    df = pd.read_csv(CSV_SOURCE)
    
    for idx, row in df.iterrows():
        region = row["Región"]
        comuna = row["Comuna"]
        url = row["Enlace de Descarga"]
        
        print(f"--- PROCESANDO: {idx + 1}/{len(df)} ---")
        print(f"Región: {region} | Comuna: {comuna}")
        
        try:
            # 1. Descargar
            print(f"Descargando {url}...")
            r = requests.get(url, stream=True)
            r.raise_for_status()
            with open(TEMP_RAW, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # 2. Desbloquear
            print("Desbloqueando PDF...")
            if unlock_pdf(TEMP_RAW, TEMP_UNLOCKED):
                
                # 3. Extraer Nombres
                print("Extrayendo nombres...")
                names = extract_names(TEMP_UNLOCKED)
                
                # 4. Insertar en DB
                print(f"Cargando {len(names)} registros en la base de datos...")
                records = [(n, region, comuna) for n in names]
                insert_many(records)
                
                # 5. Limpieza (Fase 4: borrar PDF para ahorrar espacio)
                os.remove(TEMP_RAW)
                os.remove(TEMP_UNLOCKED)
                print("¡Limpieza de archivos temporales completada!")
                
            else:
                print(f"Fallo al desbloquear PDF de {comuna}")

        except Exception as e:
            print(f"Error procesando {comuna}: {e}")
            # Continuar con el siguiente para no detener el proceso
            continue
        
        # Pausa pequeña para no saturar el servidor del Servel
        time.sleep(1)

    print("--- PIPELINE FINALIZADO ---")

if __name__ == "__main__":
    # run_pipeline() # Descomentar para ejecutar el proceso masivo
    print("Pipeline configurado. Ejecuta run_pipeline() para comenzar la carga masiva.")
