import pandas as pd
import re
import os

INPUT_PATH = os.path.join("data", "raw", "BENEFICIARIOS SERVEL.xlsx")
OUTPUT_PATH = os.path.join("data", "processed", "beneficiarios_limpios.csv")

def clean_text(text):
    if not isinstance(text, str):
        return ""
    # 1. Mayúsculas y Ñ -> N
    text = text.upper().replace('Ñ', 'N')
    # 2. Quitar conectores (DE, LA, LAS, DEL, LOS, Y) como palabras aisladas
    text = re.sub(r'\b(DE|LA|LAS|DEL|LOS|Y)\b', '', text)
    # 3. Quitar puntuación
    text = re.sub(r'[.,;:]', '', text)
    # 4. Colapsar múltiples espacios y trim
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def process_beneficiarios():
    if not os.path.exists(INPUT_PATH):
        print(f"Error: No se encuentra el archivo en {INPUT_PATH}")
        return

    print("Cargando Excel de beneficiarios...")
    df = pd.read_excel(INPUT_PATH, engine='openpyxl')
    
    col_name = 'NOMBRE_USUARIO_ALPHA'
    if col_name not in df.columns:
        print(f"Error: No se encuentra la columna {col_name}")
        return

    print(f"Normalizando columna {col_name} (incluyendo eliminación de conectores)...")
    df['NOMBRE_LIMPIO'] = df[col_name].apply(clean_text)
    
    print("\nMuestra de normalización:")
    print(df[[col_name, 'NOMBRE_LIMPIO']].head(10))

    print(f"\nGuardando {len(df)} registros en {OUTPUT_PATH}...")
    df.to_csv(OUTPUT_PATH, index=False, encoding='utf-8')
    print("Proceso completado.")

if __name__ == "__main__":
    process_beneficiarios()
