import pandas as pd
from bs4 import BeautifulSoup
import os

# Archivo de entrada y salida
INPUT_FILE = os.path.join("..", "data", "raw", "source.html")
OUTPUT_FILE = os.path.join("..", "data", "processed", "padron_definitivo_2025.csv")

def extract_data():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: El archivo {INPUT_FILE} no existe.")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "lxml")

    data = []

    # 1. Obtener la correspondencia de pestañas (Región ID) y Paneles (Contenido)
    # Las pestañas (nav-tabs) contienen los números romanos/códigos (e.g., XV, I, RM)
    tabs = soup.select('ul#myTab li.nav-item button.nav-link')
    tab_mapping = {tab['data-bs-target'].lstrip('#'): tab.get_text(strip=True) for tab in tabs}

    # 2. Iterar sobre cada panel de contenido (tab-pane)
    panes = soup.select('div.tab-content div.tab-pane')
    
    for pane in panes:
        pane_id = pane['id']
        region_code = tab_mapping.get(pane_id, "N/A")
        
        # 3. Extraer el nombre de la región del primer <strong> dentro del pane
        region_name_tag = pane.find('p').find('strong') if pane.find('p') else None
        region_full_name = region_name_tag.get_text(strip=True) if region_name_tag else "Nombre No Encontrado"
        
        # Formato solicitado: {número} - {nombre} (e.g., I - Tarapacá)
        region_label = f"{region_code} - {region_full_name}"

        # 4. Buscar todas las comunas en el acordeón del pane
        accordion_items = pane.select('div.accordion-item')
        
        for item in accordion_items:
            # Comuna: está en el botón del encabezado (h2)
            comuna_btn = item.select_one('h2.accordion-header button')
            comuna_name = comuna_btn.get_text(strip=True) if comuna_btn else "Desconocida"
            
            # Enlace de descarga: está en el cuerpo del acordeón (accordion-body)
            download_link = item.select_one('div.accordion-body a.color-uc-primary')
            url = download_link['href'] if download_link else "N/A"
            
            data.append({
                "Región": region_label,
                "Comuna": comuna_name,
                "Enlace de Descarga": url
            })

    # Guardar en CSV
    df = pd.DataFrame(data)
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    print(f"Éxito: Se han extraído {len(df)} registros y guardado en {OUTPUT_FILE}")

if __name__ == "__main__":
    extract_data()
