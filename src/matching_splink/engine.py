import duckdb
import pandas as pd
import os
import time
from splink.duckdb.linker import DuckDBLinker
import splink.duckdb.comparison_library as cl
import splink.duckdb.comparison_template_library as ctl

# Rutas
DB_PATH = os.path.join("data", "processed", "padron_splink.db")
BENEFICIARIOS_CSV = os.path.join("data", "processed", "beneficiarios_limpios.csv")
REPORTS_DIR = "reports_splink"

def run_splink_engine():
    if not os.path.exists(REPORTS_DIR): os.makedirs(REPORTS_DIR)
    
    # 1. Preparar datos en DuckDB
    con = duckdb.connect(DB_PATH)
    
    print("Cargando beneficiarios...")
    # Agregamos un ID único a los beneficiarios para Splink
    con.execute(f"""
        CREATE OR REPLACE TABLE beneficiarios AS 
        SELECT row_number() OVER () as beneficiario_id, * 
        FROM read_csv_auto('{BENEFICIARIOS_CSV}');
    """)

    # 2. Configuración de Splink
    print("Configurando Modelo Probabilístico...")
    
    settings = {
        "link_type": "link_only",
        "comparisons": [
            cl.levenshtein_at_thresholds("nombre", 2),
        ],
        "blocking_rules_to_generate_predictions": [
            "l.nombre = r.nombre", # Match exacto
            "substring(l.nombre, 1, 4) = substring(r.nombre, 1, 4)", # Primeras 4 letras
            "str_split(l.nombre, ' ')[1] = str_split(r.nombre, ' ')[1]" # Primer apellido exacto
        ],
        "retain_matching_columns": True,
        "retain_intermediate_calculation_columns": False,
    }

    # Inicializar Linker
    linker = DuckDBLinker(
        [con.table("beneficiarios"), con.table("electores")],
        settings,
        connection=con,
        input_table_aliases=["beneficiarios", "electores"]
    )

    # 3. Estimación de Pesos (U y M)
    print("Estimando parámetros del modelo (EM)...")
    # Estimamos U (coincidencias por azar)
    linker.estimate_u_using_random_sampling(max_pairs=1e6)
    
    # Estimamos M (probabilidad de error en match real) usando bloqueos
    linker.estimate_parameters_using_expectation_maximisation("l.nombre = r.nombre")
    linker.estimate_parameters_using_expectation_maximisation("str_split(l.nombre, ' ')[1] = str_split(r.nombre, ' ')[1]")

    # 4. Ejecutar Matching
    print("Ejecutando Matching masivo...")
    start_time = time.time()
    df_predictions = linker.predict(threshold_match_probability=0.85)
    
    # 5. Formatear Resultados (Top 3 Comunas y Agregación)
    print("Procesando Reporte Maestro...")
    
    # Registramos las predicciones como tabla para SQL final
    con.execute("CREATE OR REPLACE TABLE predictions AS SELECT * FROM df_predictions")
    
    report_query = """
    WITH CandidateInfo AS (
        SELECT 
            p.beneficiario_id,
            p.match_probability,
            r.nombre as region_full,
            c.nombre as comuna_nombre
        FROM predictions p
        JOIN electores e ON p.elector_id = e.elector_id
        JOIN comunas c ON e.comuna_id = c.id
        JOIN regiones r ON c.region_id = r.id
    ),
    TopCandidates AS (
        SELECT 
            beneficiario_id,
            split_part(region_full, ' - ', 1) || ' - ' || comuna_nombre || ' (' || round(match_probability * 100, 1) || '%)' as loc_prob,
            match_probability,
            ROW_NUMBER() OVER(PARTITION BY beneficiario_id ORDER BY match_probability DESC) as rank
        FROM CandidateInfo
    ),
    Aggregated AS (
        SELECT 
            beneficiario_id,
            list_aggregate(list(loc_prob), 'string_agg', '; ') as COMUNAS,
            count(*) as COINCIDENCIAS,
            max(match_probability) as max_conf
        FROM TopCandidates
        WHERE rank <= 3
        GROUP BY beneficiario_id
    )
    SELECT 
        b.NOMBRE_USUARIO_ALPHA,
        b.NOMBRE_LIMPIO,
        a.COMUNAS,
        a.COINCIDENCIAS,
        round(a.max_conf * 100, 1) || '%' as CONFIANZA
    FROM beneficiarios b
    LEFT JOIN Aggregated a ON b.beneficiario_id = a.beneficiario_id
    ORDER BY b.beneficiario_id
    """
    
    final_df = con.execute(report_query).df()
    
    # Guardar Reportes
    csv_path = os.path.join(REPORTS_DIR, "matching_results_splink.csv")
    xlsx_path = os.path.join(REPORTS_DIR, "matching_results_splink.xlsx")
    
    final_df.to_csv(csv_path, index=False)
    final_df.to_excel(xlsx_path, index=False)
    
    # Generar Resumen MD
    total = len(final_df)
    matched = final_df[final_df['CONFIANZA'].notna()].shape[0]
    
    summary_md = f"""# Reporte de Matching Probabilístico (Splink)

## Resumen Ejecutivo
- **Total Beneficiarios:** {total:,}
- **Matches Encontrados (>85%):** {matched:,} ({(matched/total)*100:.2f}%)
- **Pendientes:** {total - matched:,}
- **Tiempo de ejecución:** {time.time() - start_time:.2f}s

---
*Generado automáticamente por Splink Engine v4*
"""
    with open(os.path.join(REPORTS_DIR, "matching_summary_splink.md"), "w", encoding="utf-8") as f:
        f.write(summary_md)

    print(f"\n[OK] Proceso completado.")
    print(f"Reporte MD: {os.path.join(REPORTS_DIR, 'matching_summary_splink.md')}")
    print(f"Excel final: {xlsx_path}")

    con.close()

if __name__ == "__main__":
    run_splink_engine()
