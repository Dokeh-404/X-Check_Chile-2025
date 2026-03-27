# Proyecto: Padrón Electoral 2025 - Chile

Este proyecto automatiza la descarga, desbloqueo, extracción y almacenamiento del Padrón Electoral 2025 del SERVEL.

## Arquitectura del Proyecto

- **Ambiente:** `padron-2025` (Python 3.12, Conda)
- **Base de Datos:** DuckDB (almacenamiento ligero y rápido para ~15M de registros)

### Estructura de Directorios:
- `data/raw/source.html`: Archivo fuente original del SERVEL.
- `data/processed/`: Base de datos `.db` y archivos CSV finales.
- `data/temp/`: Espacio para procesamiento temporal de PDFs.
- `src/`: Código fuente del proyecto.

## Instrucciones para Agentes de IA

1.  **Activación:** `conda activate padron-2025`
2.  **Scripts en `src/`:**
    - `python src/scraper.py`: Procesa el HTML y genera `data/processed/padron_definitivo_2025.csv`.
    - `python src/extractor.py`: Contiene la lógica de desbloqueo y extracción quirúrgica.
    - `python src/database.py`: Inicializa y gestiona la base de datos DuckDB.
    - `python src/pipeline.py`: Orquestador de descarga y extracción masiva.

## Notas Técnicas
- El desbloqueo utiliza `pikepdf` para eliminar restricciones de copia.
- La extracción utiliza `PyMuPDF` (fitz) con coordenadas específicas para la columna "Nombre".
- El pipeline descarga, procesa y elimina cada PDF para minimizar el uso de disco.
