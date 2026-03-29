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

def get_expected_count(pdf_path, rect=(45, 50, 50, 105)):
    """(Fase 2) Extrae el número total de registros usando coordenadas precisas y filtro de color negro."""
    doc = fitz.open(pdf_path)
    page = doc[0]
    
    # Obtener contenido detallado del área
    dict_content = page.get_text("dict", clip=fitz.Rect(rect))
    
    found_text = ""
    for block in dict_content["blocks"]:
        if "lines" in block:
            for line in block["lines"]:
                for span in line["spans"]:
                    # Solo color negro (0) para ignorar fondos
                    if span["color"] == 0:
                        found_text += span["text"]
    doc.close()
    
    clean_text = found_text.replace(".", "").strip()
    return int(clean_text) if clean_text.isdigit() else 0

def extract_names(pdf_path, x_range=(75, 590), y_range=(350, 750), max_pages=None):
    """(Fase 2) Extracción quirúrgica de nombres usando coordenadas y color negro."""
    doc = fitz.open(pdf_path)
    names = []
    total_pages = len(doc)
    
    # Palabras clave a excluir (basado en pruebas-fase2)
    EXCLUDE_KEYWORDS = ["NOMBRE", "REPÚBLICA DE CHILE", "SERVICIO ELECTORAL", "COMUNA", "CIRCUNSCRIPCIÓN"]

    pages_to_process = min(total_pages, max_pages) if max_pages else total_pages

    for page_num in range(pages_to_process):
        page = doc[page_num]
        blocks = page.get_text("dict")["blocks"]
        
        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        color = span["color"]
                        x0, y0 = span["bbox"][0], span["bbox"][1]
                        
                        if color == 0 and (x_range[0] <= x0 <= x_range[1]) and (y_range[0] <= y0 <= y_range[1]):
                            if text and text not in EXCLUDE_KEYWORDS and ":" not in text:
                                names.append(text)
    doc.close()
    return names, total_pages

if __name__ == "__main__":
    # Script para prueba individual de extracción
    print("Extractor listo. Úsalo como módulo o importa sus funciones.")
