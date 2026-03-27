import pandas as pd
import requests
import os

# Archivo de entrada
CSV_FILE = "padron_definitivo_2025.csv"
DOWNLOAD_FOLDER = "padrones_descargados"

def test_single_download():
    # 1. Leer el CSV
    if not os.path.exists(CSV_FILE):
        print(f"Error: No se encuentra el archivo {CSV_FILE}")
        return

    df = pd.DataFrame(pd.read_csv(CSV_FILE))
    
    if df.empty:
        print("Error: El CSV está vacío.")
        return

    # 2. Obtener el primer registro
    primera_fila = df.iloc[0]
    region = primera_fila["Región"]
    comuna = primera_fila["Comuna"]
    url = primera_fila["Enlace de Descarga"]

    print(f"Iniciando descarga de prueba:")
    print(f"Región: {region}")
    print(f"Comuna: {comuna}")
    print(f"URL: {url}")

    # 3. Crear carpeta si no existe
    if not os.path.exists(DOWNLOAD_FOLDER):
        os.makedirs(DOWNLOAD_FOLDER)

    # 4. Descargar el archivo
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status() # Lanza error si la descarga falla
        
        # Nombre del archivo (reemplazando espacios y caracteres conflictivos)
        file_name = f"{region.replace(' ', '_')}_{comuna.replace(' ', '_')}.pdf"
        file_path = os.path.join(DOWNLOAD_FOLDER, file_name)

        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"\nÉxito: Archivo guardado en: {file_path}")
        print(f"Tamaño: {os.path.getsize(file_path) / 1024:.2f} KB")

    except Exception as e:
        print(f"\nError al descargar: {e}")

if __name__ == "__main__":
    test_single_download()
