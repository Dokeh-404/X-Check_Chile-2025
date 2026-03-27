import os
import sys
import pandas as pd
import requests
import duckdb

# Asegurar que se puede importar desde src si se ejecuta desde la raíz
sys.path.append("src")

from scraper import extract_data
from extractor import unlock_pdf, extract_names
from database import setup_database, insert_many

# Rutas de Archivos
SOURCE_HTML = os.path.join("data", "raw", "source.html")
CSV_PATH = os.path.join("data", "processed", "padron_definitivo_2025.csv")
DB_PATH = os.path.join("data", "processed", "padron_definitivo.db")
TEMP_RAW = os.path.join("data", "temp", "val_raw.pdf")
TEMP_UNLOCKED = os.path.join("data", "temp", "val_unlocked.pdf")

def validate_pipeline():
    print("=== INICIANDO VALIDACIÓN DEL PIPELINE (1 Comuna) ===\n")

    # --- FASE 1: Scraper ---
    print("[FASE 1] Ejecutando Scraper...")
    if not os.path.exists(SOURCE_HTML):
        print(f"ERROR: No se encuentra {SOURCE_HTML}")
        return
    
    extract_data() # Esto genera el CSV
    
    if not os.path.exists(CSV_PATH):
        print(f"ERROR: No se generó {CSV_PATH}")
        return
    
    df = pd.read_csv(CSV_PATH)
    print(f"OK: Scraper generó CSV con {len(df)} registros.")

    # Tomar la primera comuna para la prueba
    test_row = df.iloc[0]
    region = test_row["Región"]
    comuna = test_row["Comuna"]
    url = test_row["Enlace de Descarga"]
    print(f"Probando con: {comuna} ({region})")

    # --- FASE 2: Descarga y Desbloqueo ---
    print(f"\n[FASE 2] Descargando PDF de: {url}")
    try:
        r = requests.get(url, stream=True)
        r.raise_for_status()
        with open(TEMP_RAW, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"OK: PDF descargado en {TEMP_RAW}")

        print("Desbloqueando PDF...")
        if not unlock_pdf(TEMP_RAW, TEMP_UNLOCKED):
            print("ERROR: Falló el desbloqueo.")
            return
        print(f"OK: PDF desbloqueado en {TEMP_UNLOCKED}")

        # --- EXTRACCIÓN ---
        print("Extrayendo nombres (primeras 5 páginas para validación rápida)...")
        # Usamos los rangos optimizados en extractor.py: X(75-590), Y(350-750)
        nombres = extract_names(TEMP_UNLOCKED, max_pages=5)
        if not nombres:
            print("ERROR: No se extrajeron nombres. Revisa coordenadas en extractor.py")
            return
        print(f"OK: Se extrajeron {len(nombres)} nombres.")
        print(f"Muestra: {nombres[:3]}")

        # --- FASE 3: Base de Datos ---
        print(f"\n[FASE 3] Preparando Base de Datos en {DB_PATH}")
        setup_database()
        
        records = [(n, region, comuna) for n in nombres]
        insert_many(records)
        print(f"OK: {len(records)} registros insertados en DuckDB.")

        # Verificación final en la DB
        con = duckdb.connect(DB_PATH)
        count = con.execute("SELECT count(*) FROM electores WHERE comuna = ?", [comuna]).fetchone()[0]
        con.close()
        
        if count == len(nombres):
            print(f"\n✅ VALIDACIÓN EXITOSA: {count} registros verificados en la DB para {comuna}.")
        else:
            print(f"\n❌ ERROR DE INTEGRIDAD: DB tiene {count} registros, se esperaban {len(nombres)}.")

    except Exception as e:
        print(f"\n❌ ERROR DURANTE LA VALIDACIÓN: {e}")
    finally:
        # Limpieza de archivos de validación (opcional, pero recomendado)
        if os.path.exists(TEMP_RAW): os.remove(TEMP_RAW)
        # Dejamos el unlocked para que el usuario pueda revisarlo si quiere
        # if os.path.exists(TEMP_UNLOCKED): os.remove(TEMP_UNLOCKED)
        print("\nLimpieza de archivos temporales de validación realizada.")

if __name__ == "__main__":
    validate_pipeline()
