import os
import sys
import pandas as pd
import requests
import duckdb

# Asegurar que se puede importar desde src si se ejecuta desde la raíz
sys.path.append("src")

from scraper import extract_data
from extractor import unlock_pdf, extract_names
from database import setup_database, insert_electores_batch, get_comuna_id

# Rutas de Archivos
CSV_PATH = os.path.join("data", "processed", "padron_definitivo_2025.csv")
DB_PATH = os.path.join("data", "processed", "padron_definitivo.db")
TEMP_RAW = os.path.join("data", "temp", "val_raw.pdf")
TEMP_UNLOCKED = os.path.join("data", "temp", "val_unlocked.pdf")

def validate_relational_pipeline():
    print("=== VALIDACIÓN PIPELINE RELACIONAL (3 Tablas) ===\n")

    # 1. Eliminar DB previa para empezar de cero
    if os.path.exists(DB_PATH): os.remove(DB_PATH)

    # 2. Scraper y Setup DB
    extract_data()
    setup_database(CSV_PATH)
    
    con = duckdb.connect(DB_PATH)
    num_regiones = con.execute("SELECT count(*) FROM regiones").fetchone()[0]
    num_comunas = con.execute("SELECT count(*) FROM comunas").fetchone()[0]
    con.close()
    
    print(f"OK: Tablas maestras pobladas ({num_regiones} regiones, {num_comunas} comunas).")

    # 3. Procesar Primera Comuna
    df = pd.read_csv(CSV_PATH)
    test_row = df.iloc[0]
    region, comuna, url = test_row["Región"], test_row["Comuna"], test_row["Enlace de Descarga"]
    comuna_id = get_comuna_id(comuna, region)

    print(f"\nProbando extracción para: {comuna} (ID: {comuna_id})")
    
    r = requests.get(url, stream=True)
    with open(TEMP_RAW, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192): f.write(chunk)
    
    unlock_pdf(TEMP_RAW, TEMP_UNLOCKED)
    nombres = extract_names(TEMP_UNLOCKED, max_pages=2) # Solo 2 páginas para validar
    
    records = [(n, comuna_id) for n in nombres]
    insert_electores_batch(records)
    
    # 4. Verificación de Integridad Relacional
    con = duckdb.connect(DB_PATH)
    # Consulta curiosa: ¿Cuántos hay en la región de la primera comuna?
    result = con.execute("""
        SELECT r.nombre, c.nombre, count(e.nombre) 
        FROM electores e
        JOIN comunas c ON e.comuna_id = c.id
        JOIN regiones r ON c.region_id = r.id
        WHERE c.id = ?
        GROUP BY r.nombre, c.nombre
    """, [comuna_id]).fetchone()
    con.close()

    if result and result[2] == len(nombres):
        print(f"\n✅ VALIDACIÓN EXITOSA")
        print(f"Región: {result[0]} | Comuna: {result[1]} | Electores: {result[2]}")
    else:
        print(f"\n❌ ERROR DE INTEGRIDAD RELACIONAL")

    # Limpieza
    if os.path.exists(TEMP_RAW): os.remove(TEMP_RAW)
    print("\nLimpieza de temporales realizada.")

if __name__ == "__main__":
    validate_relational_pipeline()
