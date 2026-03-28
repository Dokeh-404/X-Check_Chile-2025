import duckdb
import os
import pandas as pd

# Ruta de la base de datos
DB_PATH = os.path.join("data", "processed", "padron_definitivo.db")

def inspect_data():
    if not os.path.exists(DB_PATH):
        print(f"Error: No se encuentra la base de datos en {DB_PATH}")
        return

    # Conectar en modo lectura (read_only=True) para seguridad
    con = duckdb.connect(DB_PATH, read_only=True)

    print("=== INSPECCIÓN DE BASE DE DATOS PADRÓN 2025 ===\n")

    # 1. Conteo Total
    total = con.execute("SELECT count(*) FROM electores").fetchone()[0]
    print(f"Total de registros en la DB: {total:,}")

    # 2. Resumen por Región y Comuna
    print("\nResumen de carga (Top 10 comunas con más registros):")
    resumen = con.execute("""
        SELECT region, comuna, count(*) as total 
        FROM electores 
        GROUP BY region, comuna 
        ORDER BY total DESC 
        LIMIT 10
    """).df()
    print(resumen.to_string(index=False))

    # 3. Muestra de datos aleatoria
    print("\nMuestra aleatoria de 5 registros:")
    muestra = con.execute("SELECT * FROM electores USING SAMPLE 5").df()
    print(muestra.to_string(index=False))

    con.close()

def search_name(name_query):
    """Busca un nombre parcial en la base de datos."""
    con = duckdb.connect(DB_PATH, read_only=True)
    print(f"\nBuscando: '{name_query}'...")
    
    # Búsqueda con LIKE (insensible a mayúsculas en DuckDB por defecto si usas ILIKE)
    results = con.execute("""
        SELECT * FROM electores 
        WHERE nombre ILIKE ? 
        LIMIT 10
    """, [f"%{name_query}%"]).df()
    
    if results.empty:
        print("No se encontraron coincidencias.")
    else:
        print(results.to_string(index=False))
    
    con.close()

if __name__ == "__main__":
    inspect_data()
    
    # Ejemplo de búsqueda: descomenta la siguiente línea para probar
    # search_name("ABARCA")
