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
    
    # 1. Normalización profunda y remoción de conectores (DE, LA, LAS, DEL, LOS, Y)
    print("Iniciando limpieza de conectores y normalización (esto puede tardar)...")
    start_norm = time.time()
    
    # Query que aplica Mayúsculas, Ñ->N, y borra conectores aislados. 
    # Luego colapsamos espacios dobles en un segundo paso para máxima pureza.
    con.execute("""
        UPDATE electores 
        SET nombre = trim(regexp_replace(upper(replace(nombre, 'Ñ', 'N')), '\\b(DE|LA|LAS|DEL|LOS|Y)\\b', '', 'g'))
        WHERE nombre GLOB '*[ñÑ.,;:]*' OR nombre GLOB '*\\b(DE|LA|LAS|DEL|LOS|Y)\\b*';
    """)
    
    print("Colapsando espacios múltiples residuales...")
    con.execute("""
        UPDATE electores 
        SET nombre = regexp_replace(nombre, '\\s+', ' ', 'g')
        WHERE nombre LIKE '%  %';
    """)
    
    print(f"Limpieza completada en {time.time() - start_norm:.2f}s")

    # 2. Recreación del Índice (El cambio de datos requiere reconstruirlo para óptimo rendimiento)
    print("Reconstruyendo índice 'idx_elector_nombre'...")
    start_idx = time.time()
    con.execute("DROP INDEX IF EXISTS idx_elector_nombre;")
    con.execute("CREATE INDEX idx_elector_nombre ON electores (nombre);")
    print(f"Índice reconstruido en {time.time() - start_idx:.2f}s")

    # 3. Verificación final
    print("\n--- Verificación DB ---")
    # Buscamos si quedó algún conector aislado
    residuals = con.execute("SELECT count(*) FROM electores WHERE nombre GLOB '*\\b(DE|LA|LAS|DEL|LOS|Y)\\b*'").fetchone()[0]
    print(f"Conectores detectados después de limpieza: {residuals}")

    con.close()
    print("\nBase de datos lista.")

if __name__ == "__main__":
    prepare_database()
