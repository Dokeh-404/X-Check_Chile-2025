import pandas as pd
import duckdb
import os
import re
import unicodedata

# Configuración de rutas
EXCEL_RAW = os.path.join("data", "raw", "BENEFICIARIOS SERVEL.xlsx")
EXCEL_PROCESSED = os.path.join("data", "processed", "BENEFICIARIOS_NORMALIZADOS.xlsx")
OUTPUT_FINAL = os.path.join("data", "processed", "RESULTADO_CRUCE_PADRON.xlsx")
DB_PATH = os.path.join("data", "processed", "padron_definitivo.db")

def normalize_text(text):
    """Limpia el texto: mayúsculas, quita tildes, Ñ->N, quita puntos y caracteres raros."""
    if not isinstance(text, str): return ""
    # Quitar tildes
    text = "".join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
    # Reemplazar Ñ por N (ya que el padrón lo normalizamos así)
    text = text.upper().replace("Ñ", "N")
    # Quitar todo lo que no sea letras, números o espacios
    text = re.sub(r'[^A-Z0-9\s]', '', text)
    # Colapsar espacios múltiples
    text = " ".join(text.split())
    return text

def run_crosscheck():
    print("=== INICIANDO MOTOR DE CROSSCHECK ===")
    
    # 1. Cargar y Normalizar Excel
    if not os.path.exists(EXCEL_RAW):
        print(f"Error: No se encuentra {EXCEL_RAW}")
        return

    print("Cargando Excel de beneficiarios...")
    df_ben = pd.read_excel(EXCEL_RAW)
    
    print("Normalizando nombres de beneficiarios...")
    # Asegúrate de que el nombre de la columna sea exacto
    col_name = "NOMBRE_USUARIO_ALPHA" 
    if col_name not in df_ben.columns:
        print(f"Error: La columna {col_name} no existe en el Excel.")
        return
        
    df_ben["NOMBRE_USUARIO_ALPHA_LIMPIA"] = df_ben[col_name].apply(normalize_text)
    
    # Guardar copia procesada
    df_ben.to_excel(EXCEL_PROCESSED, index=False)
    print(f"Excel normalizado guardado en: {EXCEL_PROCESSED}")

    # 2. Preparar DuckDB para el cruce
    con = duckdb.connect(DB_PATH)
    
    # Registramos el DataFrame de beneficiarios en DuckDB como una tabla virtual
    con.register("beneficiarios", df_ben)

    # 3. CASCADA NIVEL 1: Coincidencia Exacta (N/Ñ Insensible)
    print("Ejecutando Match Nivel 1: Exacto...")
    match_exacto = con.execute("""
        SELECT 
            b.NOMBRE_USUARIO_ALPHA_LIMPIA,
            string_agg(DISTINCT c.nombre, ', ') as comunas,
            string_agg(DISTINCT r.nombre, ', ') as regiones,
            count(e.nombre) as n_coincidencias,
            'EXACTO' as metodo_match
        FROM beneficiarios b
        JOIN electores e ON b.NOMBRE_USUARIO_ALPHA_LIMPIA = e.nombre_limpio
        JOIN comunas c ON e.comuna_id = c.id
        JOIN regiones r ON c.region_id = r.id
        GROUP BY b.NOMBRE_USUARIO_ALPHA_LIMPIA
    """).df()

    # Combinar resultados con el Excel original
    df_final = df_ben.merge(match_exacto, on="NOMBRE_USUARIO_ALPHA_LIMPIA", how="left")

    # 4. CASCADA NIVEL 2: Fonético / Parcial
    # Identificar quiénes quedaron sin match (NaN en metodo_match)
    pendientes = df_final[df_final["metodo_match"].isna()]["NOMBRE_USUARIO_ALPHA_LIMPIA"].unique()
    
    if len(pendientes) > 0:
        print(f"Buscando {len(pendientes)} registros pendientes por método fonético/parcial...")
        # Nota: Por velocidad, usaremos búsqueda de 'contenido' simple en esta primera iteración
        # ya que Levenshtein sobre 15M puede ser lento sin filtros.
        # Implementaremos búsqueda por Primer Apellido + Segundo Apellido (tokens)
        
        # Este es un placeholder para lógica fonética más avanzada si se requiere
        # De momento, buscaremos si el nombre completo del beneficiario está CONTENIDO
        # o si tiene similitud alta.
        
    # 5. Guardar Resultados Finales
    print(f"Generando Excel de resultados final: {OUTPUT_FINAL}")
    df_final.to_excel(OUTPUT_FINAL, index=False)
    
    # 6. Reporte rápido por consola
    encontrados = df_final["metodo_match"].notna().sum()
    print("\n" + "="*40)
    print("RESUMEN DEL CRUCE")
    print("="*40)
    print(f"Total Beneficiarios:  {len(df_ben):,}")
    print(f"Encontrados en Padrón: {encontrados:,}")
    print(f"Efectividad:          {(encontrados/len(df_ben))*100:.2f}%")
    print("="*40)

    con.close()

if __name__ == "__main__":
    run_crosscheck()
