import duckdb
import os

# Archivo de la base de datos
DB_FILE = os.path.join("data", "processed", "padron_definitivo.db")

def setup_database():
    """(Fase 3) Configura la base de datos DuckDB inicial."""
    con = duckdb.connect(DB_FILE)
    
    # Crear tabla de electores (optimizada)
    con.execute("""
    CREATE TABLE IF NOT EXISTS electores (
        nombre VARCHAR,
        region VARCHAR,
        comuna VARCHAR
    );
    """)
    
    # Índice para búsquedas rápidas (opcional en DuckDB, pero útil para nombres)
    # DuckDB maneja muy bien las columnas masivas por sí solo.
    
    con.close()
    print(f"Base de datos {DB_FILE} configurada.")

def insert_many(records):
    """(Fase 3) Inserción masiva de registros (electores)."""
    con = duckdb.connect(DB_FILE)
    con.executemany("INSERT INTO electores VALUES (?, ?, ?)", records)
    con.close()

if __name__ == "__main__":
    setup_database()
