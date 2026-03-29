import duckdb
import os
import time

DB_PATH = os.path.join("data", "processed", "padron_definitivo.db")

def prepare_for_matching():
    if not os.path.exists(DB_PATH):
        print("Error: Base de datos no encontrada.")
        return

    con = duckdb.connect(DB_PATH)
    
    print("Iniciando preparación de la base de datos para el cruce...")
    start_time = time.time()

    # 1. Añadir columna nombre_limpio si no existe
    # Esta columna tendrá: Mayúsculas, Sin Tildes, Ñ reemplazada por N
    print("Creando columna 'nombre_limpio' (N/Ñ insensible)...")
    
    # Verificamos si la columna existe
    cols = con.execute("PRAGMA table_info('electores')").fetchall()
    col_names = [c[1] for c in cols]
    
    if "nombre_limpio" not in col_names:
        con.execute("ALTER TABLE electores ADD COLUMN nombre_limpio VARCHAR;")
    
    # 2. Poblar nombre_limpio usando funciones nativas de DuckDB para velocidad
    # Nota: DuckDB no tiene una función simple para quitar tildes, pero como el Padrón
    # ya viene mayormente limpio o con caracteres estándar, aplicaremos REPLACE masivos.
    print("Normalizando 15.6 millones de registros (esto puede tardar unos minutos)...")
    con.execute("""
        UPDATE electores 
        SET nombre_limpio = UPPER(
            REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(nombre, 
            'Ñ', 'N'), 
            'Á', 'A'), 'É', 'E'), 'Í', 'I'), 'Ó', 'O'), 'Ú', 'U')
        );
    """)

    # 3. Crear Índice para que el cruce sea instantáneo
    print("Creando índice sobre 'nombre_limpio'...")
    con.execute("CREATE INDEX IF NOT EXISTS idx_nombre_limpio ON electores (nombre_limpio);")

    duration = time.time() - start_time
    print(f"✅ Base de datos preparada con éxito en {duration:.2f} segundos.")
    con.close()

if __name__ == "__main__":
    prepare_for_matching()
