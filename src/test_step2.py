import pandas as pd
import os
import requests
import sys

# Añadir src al path para poder importar módulos locales si fuera necesario
sys.path.append("src")
from extractor import unlock_pdf

# Configuración de rutas
CSV_FILE = os.path.join("..","data", "processed", "padron_definitivo_2025.csv")
TEMP_RAW = os.path.join("..","data", "temp", "test_raw.pdf")
TEMP_UNLOCKED = os.path.join("..","data", "temp", "test_unlocked.pdf")

def run_test():
    if not os.path.exists(CSV_FILE):
        print(f"Error: No se encuentra el archivo {CSV_FILE}. Ejecuta 'python src/scraper.py' primero.")
        return

    # 1. Leer el primer registro
    df = pd.read_csv(CSV_FILE)
    if df.empty:
        print("El CSV está vacío.")
        return

    primera_fila = df.iloc[0]
    comuna = primera_fila["Comuna"]
    url = primera_fila["Enlace de Descarga"]

    print(f"Prueba para comuna: {comuna}")
    print(f"URL: {url}")

    # 2. Descargar
    try:
        print(f"Descargando en {TEMP_RAW}...")
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(TEMP_RAW, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print("Descarga completada.")

        # 3. Desbloquear
        print(f"Desbloqueando en {TEMP_UNLOCKED}...")
        if unlock_pdf(TEMP_RAW, TEMP_UNLOCKED):
            print("\n¡ÉXITO! El PDF ha sido descargado y desbloqueado.")
            print(f"Archivo desbloqueado: {TEMP_UNLOCKED}")
            print(f"Tamaño: {os.path.getsize(TEMP_UNLOCKED) / (1024*1024):.2f} MB")
        else:
            print("\nFallo en el desbloqueo del PDF.")

    except Exception as e:
        print(f"Ocurrió un error: {e}")

if __name__ == "__main__":
    run_test()
