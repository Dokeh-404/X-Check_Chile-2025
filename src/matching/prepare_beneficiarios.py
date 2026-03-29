import pandas as pd
import re
import os

INPUT_PATH = os.path.join("data", "raw", "BENEFICIARIOS SERVEL.xlsx")
OUTPUT_PATH = os.path.join("data", "processed", "beneficiarios_limpios.csv")

def clean_text(text):
    if not isinstance(text, str):
        return ""
    # Convertir a mayúsculas
    text = text.upper()
    # Reemplazar Ñ por N
    text = text.replace('Ñ', 'N')
    # Quitar puntos, comas y otros signos de puntuación
    text = re.sub(r'[.,;:]', '', text)
    # Reemplazar múltiples espacios por uno solo y trim
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def process_beneficiarios():
    if not os.path.exists(INPUT_PATH):
        print(f"Error: No se encuentra el archivo en {INPUT_PATH}")
        return

    print("Cargando Excel de beneficiarios...")
    # Usamos openpyxl como motor por defecto para .xlsx
    df = pd.read_excel(INPUT_PATH, engine='openpyxl')
    
    col_name = 'NOMBRE_USUARIO_ALPHA'
    if col_name not in df.columns:
        print(f"Error: No se encuentra la columna {col_name}")
        print(f"Columnas disponibles: {df.columns.tolist()}")
        return

    print(f"Normalizando columna {col_name}...")
    df['NOMBRE_LIMPIO'] = df[col_name].apply(clean_text)
    
    print("\nMuestra de normalización:")
    print(df[[col_name, 'NOMBRE_LIMPIO']].head())

    print(f"\nGuardando {len(df)} registros en {OUTPUT_PATH}...")
    df.to_csv(OUTPUT_PATH, index=False, encoding='utf-8')
    print("Proceso completado.")

if __name__ == "__main__":
    process_beneficiarios()
