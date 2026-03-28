import duckdb
import os
import pandas as pd

# Archivo de la base de datos
DB_FILE = os.path.join("data", "processed", "padron_definitivo.db")

def setup_database(csv_source=None):
    """(Fase 3) Configura el esquema relacional de 3 tablas."""
    con = duckdb.connect(DB_FILE)
    
    # 1. Crear tabla de Regiones
    con.execute("""
    CREATE TABLE IF NOT EXISTS regiones (
        id INTEGER PRIMARY KEY,
        nombre VARCHAR UNIQUE
    );
    """)

    # 2. Crear tabla de Comunas
    con.execute("""
    CREATE TABLE IF NOT EXISTS comunas (
        id INTEGER PRIMARY KEY,
        nombre VARCHAR,
        region_id INTEGER,
        FOREIGN KEY (region_id) REFERENCES regiones(id)
    );
    """)

    # 3. Crear tabla de Electores (Relacionada a Comunas)
    con.execute("""
    CREATE TABLE IF NOT EXISTS electores (
        nombre VARCHAR,
        comuna_id INTEGER,
        FOREIGN KEY (comuna_id) REFERENCES comunas(id)
    );
    """)

    # Si se provee el CSV del scraper, poblamos las tablas maestras
    if csv_source and os.path.exists(csv_source):
        print("Poblando tablas maestras (Regiones y Comunas)...")
        df = pd.read_csv(csv_source)
        
        # Insertar Regiones únicas
        regiones_unicas = df["Región"].unique()
        for i, reg in enumerate(regiones_unicas, 1):
            con.execute("INSERT OR IGNORE INTO regiones VALUES (?, ?)", [i, reg])
        
        # Insertar Comunas relacionadas
        # Usamos el índice del CSV como ID único para las comunas
        for idx, row in df.iterrows():
            # Obtener el ID de la región recién insertada
            res = con.execute("SELECT id FROM regiones WHERE nombre = ?", [row["Región"]]).fetchone()
            region_id = res[0]
            con.execute("INSERT OR IGNORE INTO comunas VALUES (?, ?, ?)", [idx + 1, row["Comuna"], region_id])
            
    con.close()
    print(f"Esquema relacional configurado en {DB_FILE}")

def get_comuna_id(comuna_name, region_name):
    """Obtiene el ID de una comuna basándose en su nombre y región."""
    con = duckdb.connect(DB_FILE)
    res = con.execute("""
        SELECT c.id 
        FROM comunas c 
        JOIN regiones r ON c.region_id = r.id 
        WHERE c.nombre = ? AND r.nombre = ?
    """, [comuna_name, region_name]).fetchone()
    con.close()
    return res[0] if res else None

def insert_electores_batch(records):
    """Inserción masiva de electores vinculados por comuna_id."""
    con = duckdb.connect(DB_FILE)
    con.executemany("INSERT INTO electores VALUES (?, ?)", records)
    con.close()

if __name__ == "__main__":
    # Prueba local
    csv_path = os.path.join("data", "processed", "padron_definitivo_2025.csv")
    setup_database(csv_path)
