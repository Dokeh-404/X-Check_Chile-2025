import duckdb
import os
import time

DB_PATH = os.path.join("data", "processed", "padron_matching.db")
BENEFICIARIOS_CSV = os.path.join("data", "processed", "beneficiarios_limpios.csv")
RESULTS_CSV = os.path.join("reports", "matching_results.csv")

def run_matching_engine():
    if not os.path.exists(DB_PATH) or not os.path.exists(BENEFICIARIOS_CSV):
        print("Error: Archivos de entrada no encontrados.")
        return

    con = duckdb.connect(DB_PATH)
    
    print("Cargando datos de beneficiarios...")
    con.execute(f"CREATE OR REPLACE VIEW beneficiarios_view AS SELECT * FROM read_csv_auto('{BENEFICIARIOS_CSV}')")
    
    # Tabla para consolidar resultados
    con.execute("""
        CREATE OR REPLACE TABLE matching_final (
            NOMBRE_USUARIO_ALPHA VARCHAR,
            NOMBRE_LIMPIO VARCHAR,
            match_nombre_padron VARCHAR,
            comuna_id INTEGER,
            capa_match INTEGER,
            confianza VARCHAR
        )
    """)

    # --- CAPA 1: MATCH EXACTO ---
    print("Ejecutando Capa 1: Match Exacto...")
    start = time.time()
    con.execute("""
        INSERT INTO matching_final
        SELECT b.NOMBRE_USUARIO_ALPHA, b.NOMBRE_LIMPIO, e.nombre, e.comuna_id, 1, 'ALTA'
        FROM beneficiarios_view b
        JOIN electores e ON b.NOMBRE_LIMPIO = e.nombre
    """)
    c1_count = con.execute("SELECT count(*) FROM matching_final WHERE capa_match = 1").fetchone()[0]
    print(f"Capa 1 completada: {c1_count} matches en {time.time()-start:.2f}s")

    # --- CAPA 2 OPTIMIZADA: SUBCONJUNTO ORDENADO CON BLOQUEO ---
    print("Ejecutando Capa 2: Subconjunto Ordenado (Optimizado con Índice)...")
    start = time.time()
    # Usamos string_split para sacar el primer apellido y filtrar rápido usando el índice idx_elector_nombre
    con.execute("""
        INSERT INTO matching_final
        SELECT 
            b.NOMBRE_USUARIO_ALPHA, 
            b.NOMBRE_LIMPIO, 
            e.nombre, 
            e.comuna_id, 
            2, 
            'MEDIA-ALTA'
        FROM (
            SELECT *, string_split(NOMBRE_LIMPIO, ' ')[1] as p_apellido 
            FROM beneficiarios_view 
            WHERE NOMBRE_LIMPIO NOT IN (SELECT NOMBRE_LIMPIO FROM matching_final)
        ) b
        JOIN electores e ON e.nombre LIKE (b.p_apellido || ' %')
        WHERE e.nombre LIKE ('%' || replace(b.NOMBRE_LIMPIO, ' ', '%') || '%')
        QUALIFY ROW_NUMBER() OVER(PARTITION BY b.NOMBRE_LIMPIO ORDER BY e.nombre) = 1
    """)
    c2_count = con.execute("SELECT count(*) FROM matching_final WHERE capa_match = 2").fetchone()[0]
    print(f"Capa 2 completada: {c2_count} matches en {time.time()-start:.2f}s")

    # --- REPORTE FINAL ---
    total_b = con.execute("SELECT count(*) FROM beneficiarios_view").fetchone()[0]
    total_m = con.execute("SELECT count(*) FROM matching_final").fetchone()[0]
    
    print("\n" + "="*40)
    print("REPORTE DE MATCHING (CAPAS 1 Y 2)")
    print("="*40)
    print(f"Total Beneficiarios:  {total_b:,}")
    print(f"Matches Encontrados:  {total_m:,} ({(total_m/total_b)*100:.2f}%)")
    print("-" * 40)
    print(f"Capa 1 (Exacto):      {c1_count:,}")
    print(f"Capa 2 (Subconjunto): {c2_count:,}")
    print(f"Pendientes:           {total_b - total_m:,}")
    print("="*40)

    if not os.path.exists("reports"): os.makedirs("reports")
    con.execute(f"COPY (SELECT * FROM matching_final) TO '{RESULTS_CSV}' (HEADER, DELIMITER ',')")
    con.close()

if __name__ == "__main__":
    run_matching_engine()
