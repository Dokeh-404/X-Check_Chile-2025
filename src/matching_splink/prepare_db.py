import duckdb
import os
import time
import shutil

ORIGINAL_DB = os.path.join("data", "processed", "padron_definitivo.db")
SPLINK_DB = os.path.join("data", "processed", "padron_splink.db")

def prepare_splink_database():
    if not os.path.exists(ORIGINAL_DB):
        print(f"Error: No se encuentra la base de datos original en {ORIGINAL_DB}")
        return

    print(f"Copiando base de datos para Splink...")
    if os.path.exists(SPLINK_DB):
        try:
            os.remove(SPLINK_DB)
        except PermissionError:
            print("Error: No se pudo eliminar la DB existente. Cierra conexiones activas.")
            return
    
    shutil.copy(ORIGINAL_DB, SPLINK_DB)
    print(f"Copia creada en {SPLINK_DB}")

    con = duckdb.connect(SPLINK_DB)
    
    # 1. Crear ID único con el nombre estándar de Splink
    print("Agregando columna 'unique_id' única...")
    start = time.time()
    con.execute("""
        CREATE TABLE electores_new AS 
        SELECT row_number() OVER () as unique_id, * FROM electores;
    """)
    con.execute("DROP TABLE electores;")
    con.execute("ALTER TABLE electores_new RENAME TO electores;")
    print(f"ID único 'unique_id' creado en {time.time() - start:.2f}s")

    # 2. Limpieza Profunda
    print("Iniciando limpieza profunda de nombres...")
    start_norm = time.time()
    con.execute("""
        UPDATE electores 
        SET nombre = trim(regexp_replace(upper(replace(nombre, 'Ñ', 'N')), '\\b(DE|LA|LAS|DEL|LOS|Y)\\b', '', 'g'))
        WHERE nombre GLOB '*[ñÑ.,;:]*' OR nombre GLOB '*\\b(DE|LA|LAS|DEL|LOS|Y)\\b*';
    """)
    con.execute("""
        UPDATE electores 
        SET nombre = regexp_replace(nombre, '\\s+', ' ', 'g')
        WHERE nombre LIKE '%  %';
    """)
    print(f"Limpieza completada en {time.time() - start_norm:.2f}s")

    # 3. Índices (Usando el nuevo nombre de columna)
    print("Creando índices de búsqueda...")
    start_idx = time.time()
    con.execute("CREATE INDEX idx_splink_nombre ON electores (nombre);")
    con.execute("CREATE UNIQUE INDEX idx_splink_id ON electores (unique_id);")
    print(f"Índices creados en {time.time() - start_idx:.2f}s")

    con.close()
    print("\n[OK] Base de datos padron_splink.db lista.")

if __name__ == "__main__":
    prepare_splink_database()
