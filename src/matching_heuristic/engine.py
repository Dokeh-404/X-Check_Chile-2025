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

def get_phonetic_code(name):
    """Convierte un nombre en una lista de códigos metaphone por palabra."""
    return [jellyfish.metaphone(w) for w in name.split()]

def is_ordered_phonetic_subset(sub_phonemes, full_phonemes):
    """Verifica si los fonemas del subconjunto aparecen en orden en el conjunto completo."""
    it = iter(full_phonemes)
    return all(p in it for p in sub_phonemes)

def save_layer_results(df, layer_num):
    """Guarda los resultados en CSV y XLSX."""
    if df.empty: return
    base_name = f"matching_results_layer_{layer_num}"
    csv_path = os.path.join(REPORTS_DIR, f"{base_name}.csv")
    xlsx_path = os.path.join(REPORTS_DIR, f"{base_name}.xlsx")
    df.to_csv(csv_path, index=False, encoding='utf-8')
    df.to_excel(xlsx_path, index=False)
    print(f"--> Capa {layer_num} guardada de forma incremental.")

def generate_md_report(df):
    total = len(df)
    matched = df[df['CAPA'].notna()]
    stats = df['CAPA'].value_counts().to_dict()
    
    report = f"""# Reporte de Matching - Padrón Electoral 2025

## Resumen Ejecutivo
- **Total Beneficiarios:** {total:,}
- **Matches Encontrados:** {len(matched):,} ({(len(matched)/total)*100:.2f}%)
- **Pendientes:** {total - len(matched):,}

## Detalle por Capas de Búsqueda
| Capa | Descripción | Cantidad | % del Total |
| :--- | :--- | :--- | :--- |
| 1 | Match Exacto | {stats.get('1: MATCH EXACTO', 0):,} | {(stats.get('1: MATCH EXACTO', 0)/total)*100:.2f}% |
| 2 | Subconjunto Ordenado | {stats.get('2: SUBCONJUNTO ORDENADO', 0):,} | {(stats.get('2: SUBCONJUNTO ORDENADO', 0)/total)*100:.2f}% |
| 3 | Fonética Estricta | {stats.get('3: FONETICA ESTRICTA', 0):,} | {(stats.get('3: FONETICA ESTRICTA', 0)/total)*100:.2f}% |
| 4 | Fonética + Subconjunto | {stats.get('4: FONETICA SUBSET', 0):,} | {(stats.get('4: FONETICA SUBSET', 0)/total)*100:.2f}% |

---
*Reporte generado automáticamente el {time.strftime('%Y-%m-%d %H:%M:%S')}*
"""
    with open(os.path.join(REPORTS_DIR, "matching_summary.md"), "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n[OK] Reporte final generado en: {os.path.join(REPORTS_DIR, 'matching_summary.md')}")

def run_matching_engine():
    if not os.path.exists(REPORTS_DIR): os.makedirs(REPORTS_DIR)
    con = duckdb.connect(DB_PATH)
    
    # 1. Cargar progreso previo o inicializar
    master_df = None
    last_layer = 0
    for i in range(4, 0, -1):
        path = os.path.join(REPORTS_DIR, f"matching_results_layer_{i}.csv")
        if os.path.exists(path):
            print(f"Retomando progreso desde Capa {i} detectada.")
            master_df = pd.read_csv(path)
            last_layer = i
            break
            
    if master_df is None:
        print("Inicializando Reporte Maestro...")
        master_df = pd.read_csv(BENEFICIARIOS_CSV)
        for col in ['COMUNAS', 'COINCIDENCIAS', 'CAPA', 'CONFIANZA']:
            master_df[col] = None

    # --- CAPA 1: MATCH EXACTO ---
    if last_layer < 1:
        print("\nEjecutando CAPA 1: MATCH EXACTO...")
        start_time = time.time()
        con.execute(f"CREATE OR REPLACE VIEW b_v AS SELECT * FROM master_df WHERE CAPA IS NULL")
        query = """
            WITH M AS (
                SELECT b.NOMBRE_USUARIO_ALPHA, r.nombre as reg, c.nombre as com
                FROM b_v b JOIN electores e ON b.NOMBRE_LIMPIO = e.nombre
                JOIN comunas c ON e.comuna_id = c.id JOIN regiones r ON c.region_id = r.id
            ),
            A AS (
                SELECT NOMBRE_USUARIO_ALPHA,
                list_aggregate(list_sort(list_distinct(list_transform(list(reg || '|' || com), 
                x -> split_part(x, ' - ', 1) || ' - ' || split_part(x, '|', 2)))), 'string_agg', '; ') as CM,
                count(*) as CN FROM M GROUP BY 1
            ) SELECT * FROM A
        """
        res = con.execute(query).df()
        if not res.empty:
            master_df = master_df.merge(res, on='NOMBRE_USUARIO_ALPHA', how='left')
            m = master_df['CM'].notna(); master_df.loc[m, 'COMUNAS'] = master_df.loc[m, 'CM']
            master_df.loc[m, 'COINCIDENCIAS'] = master_df.loc[m, 'CN']
            master_df.loc[m, 'CAPA'] = '1: MATCH EXACTO'; master_df.loc[m, 'CONFIANZA'] = '100%'
            master_df.drop(columns=['CM', 'CN'], inplace=True)
        save_layer_results(master_df, 1)

    # --- CAPA 2: SUBCONJUNTO ORDENADO (SQL) ---
    if last_layer < 2:
        print("\nEjecutando CAPA 2: SUBCONJUNTO ORDENADO...")
        start_time = time.time()
        con.execute("CREATE OR REPLACE VIEW b_v2 AS SELECT * FROM master_df WHERE CAPA IS NULL")
        query = """
            WITH M AS (
                SELECT b.NOMBRE_USUARIO_ALPHA, r.nombre as reg, c.nombre as com, e.nombre as e_n
                FROM (SELECT *, str_split(NOMBRE_LIMPIO, ' ')[1] as p_ap FROM b_v2) b
                JOIN electores e ON e.nombre LIKE (b.p_ap || ' %')
                JOIN comunas c ON e.comuna_id = c.id JOIN regiones r ON c.region_id = r.id
                WHERE e.nombre LIKE ('%' || replace(b.NOMBRE_LIMPIO, ' ', '%') || '%')
                QUALIFY ROW_NUMBER() OVER(PARTITION BY b.NOMBRE_LIMPIO, e.nombre) = 1
            ),
            A AS (
                SELECT NOMBRE_USUARIO_ALPHA,
                list_aggregate(list_sort(list_distinct(list_transform(list(reg || '|' || com), 
                x -> split_part(x, ' - ', 1) || ' - ' || split_part(x, '|', 2)))), 'string_agg', '; ') as CM,
                count(*) as CN FROM M GROUP BY 1
            ) SELECT * FROM A
        """
        res = con.execute(query).df()
        if not res.empty:
            master_df = master_df.merge(res, on='NOMBRE_USUARIO_ALPHA', how='left')
            m = master_df['CM'].notna(); master_df.loc[m, 'COMUNAS'] = master_df.loc[m, 'CM']
            master_df.loc[m, 'COINCIDENCIAS'] = master_df.loc[m, 'CN']
            master_df.loc[m, 'CAPA'] = '2: SUBCONJUNTO ORDENADO'; master_df.loc[m, 'CONFIANZA'] = '90%'
            master_df.drop(columns=['CM', 'CN'], inplace=True)
        save_layer_results(master_df, 2)

    # --- CAPAS 3 Y 4: FONÉTICA (PYTHON) ---
    if last_layer < 4:
        print("\nEjecutando CAPAS 3 Y 4: FONÉTICA...")
        start_time = time.time()
        pendientes = master_df[master_df['CAPA'].isna()].copy()
        if not pendientes.empty:
            pendientes['letra'] = pendientes['NOMBRE_LIMPIO'].str[0]
            letras = pendientes['letra'].unique()
            for letra in letras:
                print(f"  Procesando bloque letra: {letra}...")
                candidates = con.execute(f"SELECT e.nombre, r.nombre as r, c.nombre as c FROM electores e JOIN comunas c ON e.comuna_id = c.id JOIN regiones r ON c.region_id = r.id WHERE e.nombre LIKE '{letra}%'").fetchall()
                cand_data = [{'nom': c[0], 'loc': f"{c[1].split(' - ')[0]} - {c[2]}", 'phon': get_phonetic_code(c[0]), 'w': len(c[0].split())} for c in candidates]
                
                for idx, row in pendientes[pendientes['letra'] == letra].iterrows():
                    b_phon = get_phonetic_code(row['NOMBRE_LIMPIO'])
                    b_w = len(b_phon)
                    matches, layer = [], None
                    for c in cand_data:
                        if b_w == c['w'] and b_phon == c['phon']:
                            matches.append(c['loc']); layer = 3
                        elif layer != 3 and is_ordered_phonetic_subset(b_phon, c['phon']):
                            matches.append(c['loc']); layer = 4
                    if matches:
                        master_df.at[idx, 'COMUNAS'] = "; ".join(sorted(list(set(matches))))
                        master_df.at[idx, 'COINCIDENCIAS'] = len(matches)
                        master_df.at[idx, 'CAPA'] = f"{layer}: {'FONETICA ESTRICTA' if layer==3 else 'FONETICA SUBSET'}"
                        master_df.at[idx, 'CONFIANZA'] = f"{80 if layer==3 else 70}%"
        save_layer_results(master_df, 4)

    generate_md_report(master_df)
    con.close()

if __name__ == "__main__":
    run_matching_engine()
