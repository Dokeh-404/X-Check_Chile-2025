import duckdb
import os
import time

DB_PATH = os.path.join("data", "processed", "padron_matching.db")

def prepare_database():
    if not os.path.exists(DB_PATH):
        print(f"Error: No se encuentra la base de datos en {DB_PATH}")
        return

    print(f"Conectando a {DB_PATH}...")
    con = duckdb.connect(DB_PATH)
    
    # 1. Normalización Exhaustiva
    print("Iniciando normalización exhaustiva (limpieza total)...")
    start_norm = time.time()
    
    # SQL reforzado: 
    # - replace('Ñ', 'N')
    # - regexp_replace para quitar puntuación
    # - regexp_replace con \s+ para colapsar CUALQUIER cantidad de espacios en blanco a uno solo
    # - trim para quitar espacios en los extremos
    con.execute("""
        UPDATE electores 
        SET nombre = trim(regexp_replace(upper(replace(nombre, 'Ñ', 'N')), '[.,;:]', '', 'g'))
        WHERE nombre GLOB '*[ñÑ.,;:]*' OR nombre LIKE '%  %';
    """)
    
    # Refuerzo para espacios dobles que regexp_replace a veces no colapsa en una pasada
    con.execute("""
        UPDATE electores 
        SET nombre = regexp_replace(nombre, '\\s+', ' ', 'g')
        WHERE nombre LIKE '%  %';
    """)
    
    print(f"Normalización terminada en {time.time() - start_norm:.2f}s")

    # 2. Creación del Índice
    print("Creando índice de búsqueda 'idx_elector_nombre'...")
    start_idx = time.time()
    con.execute("DROP INDEX IF EXISTS idx_elector_nombre;")
    con.execute("CREATE INDEX idx_elector_nombre ON electores (nombre);")
    print(f"Índice creado en {time.time() - start_idx:.2f}s")

    # 3. Verificación final
    print("\n--- Verificación ---")
    idx_exists = con.execute("SELECT count(*) FROM duckdb_indexes WHERE index_name = 'idx_elector_nombre'").fetchone()[0]
    print(f"¿Índice existe en catálogo?: {'SÍ' if idx_exists > 0 else 'NO'}")
    
    residuals = con.execute("SELECT count(*) FROM electores WHERE nombre LIKE '%Ñ%' OR nombre LIKE '%  %'").fetchone()[0]
    print(f"Registros con basura pendiente: {residuals}")

    con.close()
    print("\nBase de datos optimizada.")

if __name__ == "__main__":
    prepare_database()
