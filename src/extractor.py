import fitz  # PyMuPDF
import pikepdf
import pandas as pd
import os

def unlock_pdf(input_path, output_path):
    """(Fase 2) Desbloquea el PDF eliminando restricciones de copia."""
    try:
        with pikepdf.open(input_path) as pdf:
            pdf.save(output_path)
        return True
    except Exception as e:
        print(f"Error al desbloquear: {e}")
        return False

def extract_names(pdf_path, x_range=(75, 590), y_range=(350, 750)):
    """(Fase 2) Extracción quirúrgica de nombres usando coordenadas y color negro."""
    doc = fitz.open(pdf_path)
    names = []
    
    # Palabras clave a excluir (basado en pruebas-fase2)
    EXCLUDE_KEYWORDS = ["NOMBRE", "REPÚBLICA DE CHILE", "SERVICIO ELECTORAL", "COMUNA", "CIRCUNSCRIPCIÓN"]

    # for page_num in range(1):
    for page_num in range(len(doc)):
        page = doc[page_num]
        blocks = page.get_text("dict")["blocks"]
        
        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        color = span["color"]
                        x0, y0 = span["bbox"][0], span["bbox"][1]
                        
                        # Filtros definidos en las pruebas exitosas:
                        # 1. Color negro (0)
                        # 2. Rango X (columna nombres)
                        # 3. Rango Y (evitar cabeceras/pies)
                        if color == 0 and (x_range[0] <= x0 <= x_range[1]) and (y_range[0] <= y0 <= y_range[1]):
                            if text and text not in EXCLUDE_KEYWORDS and ":" not in text:
                                names.append(text)
    doc.close()
    return names

if __name__ == "__main__":
    # Script para prueba individual de extracción
    print("Extractor listo. Úsalo como módulo o importa sus funciones.")
