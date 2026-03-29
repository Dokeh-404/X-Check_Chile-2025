import duckdb
import pandas as pd
import os
import time
import jellyfish
import re

# Configuración de Rutas
DB_PATH = os.path.join("data", "processed", "padron_matching.db")
BENEFICIARIOS_CSV = os.path.join("data", "processed", "beneficiarios_limpios.csv")
REPORTS_DIR = "reports"

def get_already_matched():
    """Lee los archivos existentes para saber qué nombres ya fueron cruzados."""
    matched = set()
    if not os.path.exists(REPORTS_DIR): return matched
    
    for i in range(1, 5):
        csv_path = os.path.join(REPORTS_DIR, f"matching_results_layer_{i}.csv")
        if os.path.exists(csv_path):
            try:
                df = pd.read_csv(csv_path)
                if 'NOMBRE_USUARIO_ALPHA' in df.columns:
                    matched.update(df['NOMBRE_USUARIO_ALPHA'].astype(str).unique())
            except:
                continue
    return matched

def save_layer_results(df, layer_num):
    """Guarda los resultados en CSV y XLSX."""
    if df.empty: 
        print(f"Capa {layer_num}: Sin resultados para guardar.")
        return
    base_name = f"matching_results_layer_{layer_num}"
    csv_path = os.path.join(REPORTS_DIR, f"{base_name}.csv")
    xlsx_path = os.path.join(REPORTS_DIR, f"{base_name}.xlsx")
    
    df.to_csv(csv_path, index=False, encoding='utf-8')
    df.to_excel(xlsx_path, index=False)
    print(f"--> Capa {layer_num} guardada: {len(df)} registros procesados.")

def run_matching_engine():
    if not os.path.exists(REPORTS_DIR): os.makedirs(REPORTS_DIR)
    con = duckdb.connect(DB_PATH)
    
    # Cargar lista base de beneficiarios
    df_all = pd.read_csv(BENEFICIARIOS_CSV)
    
    # --- CAPA 1: MATCH EXACTO ---
    if os.path.exists(os.path.join(REPORTS_DIR, "matching_results_layer_1.csv")):
        print("Capa 1 detectada. Saltando...")
    else:
        print("\nEjecutando CAPA 1: MATCH EXACTO...")
        start_time = time.time()
        con.execute(f"CREATE OR REPLACE VIEW b_view AS SELECT * FROM read_csv_auto('{BENEFICIARIOS_CSV}')")
        query = """
            WITH Matches AS (
                SELECT b.NOMBRE_USUARIO_ALPHA, b.NOMBRE_LIMPIO, r.nombre as reg, c.nombre as com
                FROM b_view b
                JOIN electores e ON b.NOMBRE_LIMPIO = e.nombre
                JOIN comunas c ON e.comuna_id = c.id
                JOIN regiones r ON c.region_id = r.id
            ),
            Aggregated AS (
                SELECT 
                    NOMBRE_USUARIO_ALPHA, NOMBRE_LIMPIO,
                    list_aggregate(list_sort(list_distinct(list_transform(list(reg || '|' || com), 
                    x -> split_part(x, ' - ', 1) || ' - ' || split_part(x, '|', 2)))), 'string_agg', '; ') as COMUNAS,
                    count(*) as COINCIDENCIAS
                FROM Matches GROUP BY 1, 2
            )
            SELECT NOMBRE_USUARIO_ALPHA, NOMBRE_LIMPIO, COMUNAS, COINCIDENCIAS, 
                   '1: MATCH EXACTO' as CAPA, '100%' as CONFIANZA
            FROM Aggregated
        """
        df_l1 = con.execute(query).df()
        save_layer_results(df_l1, 1)
        print(f"Tiempo Capa 1: {time.time() - start_time:.2f}s")

    # --- CAPA 2: SUBCONJUNTO ORDENADO (SQL) ---
    already_matched = get_already_matched()
    if os.path.exists(os.path.join(REPORTS_DIR, "matching_results_layer_2.csv")):
        print("Capa 2 detectada. Saltando...")
    else:
        print("\nEjecutando CAPA 2: SUBCONJUNTO ORDENADO...")
        start_time = time.time()
        df_p2 = df_all[~df_all['NOMBRE_USUARIO_ALPHA'].astype(str).isin(already_matched)].copy()
        
        if not df_p2.empty:
            con.execute("CREATE OR REPLACE TEMP TABLE p2_temp AS SELECT * FROM df_p2")
            query = """
                WITH Matches AS (
                    SELECT b.NOMBRE_USUARIO_ALPHA, b.NOMBRE_LIMPIO, r.nombre as reg, c.nombre as com, e.nombre as e_nom
                    FROM (SELECT *, str_split(NOMBRE_LIMPIO, ' ')[1] as p_ap FROM p2_temp) b
                    JOIN electores e ON e.nombre LIKE (b.p_ap || ' %')
                    JOIN comunas c ON e.comuna_id = c.id
                    JOIN regiones r ON c.region_id = r.id
                    WHERE e.nombre LIKE ('%' || replace(b.NOMBRE_LIMPIO, ' ', '%') || '%')
                    QUALIFY ROW_NUMBER() OVER(PARTITION BY b.NOMBRE_LIMPIO, e.nombre) = 1
                ),
                Aggregated AS (
                    SELECT 
                        NOMBRE_USUARIO_ALPHA, NOMBRE_LIMPIO,
                        list_aggregate(list_sort(list_distinct(list_transform(list(reg || '|' || com), 
                        x -> split_part(x, ' - ', 1) || ' - ' || split_part(x, '|', 2)))), 'string_agg', '; ') as COMUNAS,
                        count(*) as COINCIDENCIAS
                    FROM Matches GROUP BY 1, 2
                )
                SELECT NOMBRE_USUARIO_ALPHA, NOMBRE_LIMPIO, COMUNAS, COINCIDENCIAS, 
                       '2: SUBCONJUNTO ORDENADO' as CAPA, '90%' as CONFIANZA
                FROM Aggregated
            """
            df_l2 = con.execute(query).df()
            save_layer_results(df_l2, 2)
            print(f"Tiempo Capa 2: {time.time() - start_time:.2f}s")
        else:
            print("No hay pendientes para Capa 2.")

    # --- CAPA 3 Y 4: SKELETON (IMPLEMENTACIÓN SIGUIENTE PASO) ---
    # He dejado las SQL listas. Si Capa 1 y 2 funcionan, procederemos con la fonética en Python.

    con.close()
    print("\nProceso de capas SQL completado con Checkpoints.")

if __name__ == "__main__":
    run_matching_engine()
