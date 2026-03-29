import duckdb
import pandas as pd
import os
import time

DB_PATH = os.path.join("data", "processed", "padron_matching.db")
BENEFICIARIOS_CSV = os.path.join("data", "processed", "beneficiarios_limpios.csv")
REPORTS_DIR = "reports"

def run_layer_1():
    if not os.path.exists(DB_PATH) or not os.path.exists(BENEFICIARIOS_CSV):
        print("Error: Archivos de entrada no encontrados.")
        return

    if not os.path.exists(REPORTS_DIR):
        os.makedirs(REPORTS_DIR)

    con = duckdb.connect(DB_PATH)
    
    print("Cargando beneficiarios...")
    con.execute(f"CREATE OR REPLACE VIEW beneficiarios_view AS SELECT * FROM read_csv_auto('{BENEFICIARIOS_CSV}')")
    
    # Capa 1: Match Exacto
    print("Ejecutando CAPA 1: MATCH EXACTO...")
    start_time = time.time()
    
    layer_1_query = """
    WITH Matches AS (
        SELECT 
            b.NOMBRE_USUARIO_ALPHA,
            b.NOMBRE_LIMPIO,
            r.nombre as region_full,
            c.nombre as comuna_nombre
        FROM beneficiarios_view b
        JOIN electores e ON b.NOMBRE_LIMPIO = e.nombre
        JOIN comunas c ON e.comuna_id = c.id
        JOIN regiones r ON c.region_id = r.id
    ),
    Aggregated AS (
        SELECT 
            NOMBRE_USUARIO_ALPHA,
            NOMBRE_LIMPIO,
            list_aggregate(list_sort(list_distinct(list_transform(
                list(region_full || ' | ' || comuna_nombre), 
                x -> split_part(x, ' - ', 1) || ' - ' || split_part(x, ' | ', 2)
            ))), 'string_agg', '; ') as COMUNAS,
            count(*) as COINCIDENCIAS
        FROM Matches
        GROUP BY NOMBRE_USUARIO_ALPHA, NOMBRE_LIMPIO
    )
    SELECT 
        NOMBRE_USUARIO_ALPHA,
        NOMBRE_LIMPIO,
        COMUNAS,
        COINCIDENCIAS,
        '1: MATCH EXACTO' as CAPA,
        '100%' as CONFIANZA
    FROM Aggregated
    """
    
    # Exportar a DataFrame para generar ambos formatos
    df_layer_1 = con.execute(layer_1_query).df()
    
    # Rutas de archivos
    base_name = "matching_results_layer_1"
    csv_path = os.path.join(REPORTS_DIR, f"{base_name}.csv")
    xlsx_path = os.path.join(REPORTS_DIR, f"{base_name}.xlsx")
    
    # Guardar CSV
    df_layer_1.to_csv(csv_path, index=False, encoding='utf-8')
    # Guardar Excel
    df_layer_1.to_excel(xlsx_path, index=False)
    
    print(f"CAPA 1 finalizada. Se encontraron {len(df_layer_1)} matches en {time.time() - start_time:.2f}s.")
    print(f"Resultados guardados en CSV y XLSX en la carpeta: {REPORTS_DIR}")
    
    con.close()

if __name__ == "__main__":
    run_layer_1()
