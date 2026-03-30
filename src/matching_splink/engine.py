import duckdb
import pandas as pd
import os
import time
from splink import Linker, DuckDBAPI, SettingsCreator, block_on
import splink.comparison_library as cl

# Rutas
DB_PATH = os.path.join("data", "processed", "padron_splink.db")
BENEFICIARIOS_CSV = os.path.join("data", "processed", "beneficiarios_limpios.csv")
REPORTS_DIR = "reports_splink"

def run_splink_engine():
    if not os.path.exists(REPORTS_DIR): os.makedirs(REPORTS_DIR)
    
    con = duckdb.connect(DB_PATH)
    db_api = DuckDBAPI(connection=con)
    
    print("Preparando tablas de entrada (Split de Apellidos y Nombres)...")
    
    # Lógica de Split:
    # ape1: Primera palabra
    # ape2: Segunda palabra
    # noms: El resto de la cadena
    split_logic = """
        unique_id,
        nombre as nombre_completo,
        str_split(nombre, ' ')[1] as ape1,
        CASE WHEN length(str_split(nombre, ' ')) >= 2 THEN str_split(nombre, ' ')[2] ELSE NULL END as ape2,
        CASE WHEN length(str_split(nombre, ' ')) >= 3 THEN array_to_string(list_slice(str_split(nombre, ' '), 3, 100), ' ') ELSE NULL END as noms
    """
    
    con.execute(f"""
        CREATE OR REPLACE TABLE beneficiarios_matching AS 
        SELECT row_number() OVER () as unique_id, NOMBRE_LIMPIO as nombre, NOMBRE_USUARIO_ALPHA
        FROM read_csv_auto('{BENEFICIARIOS_CSV}');
    """)
    
    # Creamos versiones con los campos separados para Splink
    con.execute(f"CREATE OR REPLACE TABLE b_split AS SELECT {split_logic} FROM beneficiarios_matching")
    con.execute(f"CREATE OR REPLACE TABLE e_split AS SELECT {split_logic} FROM electores")

    print("Configurando Modelo Probabilístico Multidimensional...")
    
    settings = SettingsCreator(
        link_type="link_only",
        unique_id_column_name="unique_id",
        comparisons=[
            cl.LevenshteinAtThresholds("ape1", [1, 2]),
            cl.LevenshteinAtThresholds("ape2", [1, 2]),
            cl.LevenshteinAtThresholds("noms", [1, 2]),
        ],
        blocking_rules_to_generate_predictions=[
            block_on("ape1", "ape2"), # Ambos apellidos iguales
            block_on("ape1", "noms"), # Paterno y nombres iguales
            "l.ape1 = r.ape1 AND substring(l.ape2, 1, 1) = substring(r.ape2, 1, 1)" # Paterno e inicial materno
        ],
        retain_matching_columns=True,
        retain_intermediate_calculation_columns=False,
    )

    linker = Linker(["b_split", "e_split"], settings, db_api)

    # 3. Estimación de Pesos (Triangulación)
    print("Estimando parámetros del modelo (EM)...")
    linker.training.estimate_u_using_random_sampling(max_pairs=5e6)

    # Entrenamos las probabilidades de los nombres/materno bloqueando por el paterno
    linker.training.estimate_parameters_using_expectation_maximisation(block_on("ape1"))
    # Entrenamos las probabilidades del paterno/nombres bloqueando por el materno
    linker.training.estimate_parameters_using_expectation_maximisation(block_on("ape2"))

    # 4. Ejecutar Matching
    print("Ejecutando Matching masivo...")
    start_time = time.time()
    df_predictions = linker.inference.predict(threshold_match_probability=0.85)
    
    # 5. Formatear Resultados
    print("Procesando Reporte Maestro...")
    con.execute(f"CREATE OR REPLACE TABLE predictions_raw AS SELECT * FROM {df_predictions.physical_name}")
    
    report_query = """
    WITH CandidateInfo AS (
        SELECT 
            p.unique_id_l as b_id,
            p.match_probability,
            r.nombre as region_full,
            c.nombre as comuna_nombre
        FROM predictions_raw p
        JOIN electores e ON p.unique_id_r = e.unique_id
        JOIN comunas c ON e.comuna_id = c.id
        JOIN regiones r ON c.region_id = r.id
    ),
    TopCandidates AS (
        SELECT 
            b_id,
            split_part(region_full, ' - ', 1) || ' - ' || comuna_nombre || ' (' || round(match_probability * 100, 1) || '%)' as loc_prob,
            match_probability,
            ROW_NUMBER() OVER(PARTITION BY b_id ORDER BY match_probability DESC) as rank
        FROM CandidateInfo
    ),
    Aggregated AS (
        SELECT 
            b_id,
            list_aggregate(list(loc_prob), 'string_agg', '; ') as COMUNAS,
            count(*) as COINCIDENCIAS,
            max(match_probability) as max_conf
        FROM TopCandidates
        WHERE rank <= 3
        GROUP BY b_id
    )
    SELECT 
        bi.NOMBRE_USUARIO_ALPHA,
        bi.nombre as NOMBRE_LIMPIO,
        a.COMUNAS,
        a.COINCIDENCIAS,
        round(a.max_conf * 100, 1) || '%' as CONFIANZA
    FROM beneficiarios_matching bi
    LEFT JOIN Aggregated a ON bi.unique_id = a.b_id
    ORDER BY bi.unique_id
    """
    
    final_df = con.execute(report_query).df()
    final_df.to_csv(os.path.join(REPORTS_DIR, "matching_results_splink.csv"), index=False)
    final_df.to_excel(os.path.join(REPORTS_DIR, "matching_results_splink.xlsx"), index=False)
    
    # Reporte MD
    matched_count = final_df[final_df['CONFIANZA'].notna()].shape[0]
    total = len(final_df)
    
    summary_md = f"""# 📊 Reporte Ejecutivo: Matching Probabilístico (Splink Multidimensional)

## 1. Resumen de Hallazgos
- **Universo Total:** {total:,} registros.
- **Matches Identificados (>85%):** {matched_count:,} ({(matched_count/total)*100:.2f}% de éxito).
- **Pendientes:** {total - matched_count:,} registros.

## 2. Notas Técnicas
- El modelo fue entrenado mediante **triangulación de campos** (Apellido Paterno, Materno y Nombres).
- Este enfoque es más preciso que el heurístico ya que pondera de forma independiente los errores en cada parte del nombre.
- El umbral de corte del 85% asegura una alta calidad en los hallazgos probabilísticos.

---
*Generado por Splink Engine v4*
"""
    with open(os.path.join(REPORTS_DIR, "matching_summary_splink.md"), "w", encoding="utf-8") as f:
        f.write(summary_md)

    print(f"\n[OK] Proceso completado exitosamente.")
    con.close()

if __name__ == "__main__":
    run_splink_engine()
