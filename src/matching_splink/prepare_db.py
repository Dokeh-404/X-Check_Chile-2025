import duckdb
import os
import time

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
            print("Error: No se pudo eliminar la DB existente. Asegúrate de cerrar todas las conexiones.")
            return
    
    import shutil
    shutil.copy(ORIGINAL_DB, SPLINK_DB)
    print(f"Copia creada en {SPLINK_DB}")

    con = duckdb.connect(SPLINK_DB)
    
    # 1. Crear ID único (Obligatorio para Splink)
    print("Agregando columna 'elector_id' única...")
    # Creamos una tabla nueva con el ID para evitar el overhead de un ALTER TABLE masivo en una tabla de 15M
    start = time.time()
    con.execute("""
        CREATE TABLE electores_new AS 
        SELECT row_number() OVER () as elector_id, * FROM electores;
    """)
    con.execute("DROP TABLE electores;")
    con.execute("ALTER TABLE electores_new RENAME TO electores;")
    print(f"ID único creado en {time.time() - start:.2f}s")

    # 2. Limpieza Profunda (Ñ, Stopwords, Puntuación)
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

    # 3. Índices
    print("Creando índices de búsqueda...")
    start_idx = time.time()
    con.execute("CREATE INDEX idx_splink_nombre ON electores (nombre);")
    con.execute("CREATE UNIQUE INDEX idx_splink_id ON electores (elector_id);")
    print(f"Índices creados en {time.time() - start_idx:.2f}s")

    con.close()
    print("\nBase de datos preparada para Splink.")

if __name__ == "__main__":
    prepare_splink_database()
