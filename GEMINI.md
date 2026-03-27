# Proyecto: Padrón Electoral 2025 - Chile

Este proyecto automatiza la descarga, desbloqueo, extracción y almacenamiento del Padrón Electoral 2025 del SERVEL.

## Arquitectura del Proyecto

- **Ambiente:** `padron-2025` (Python 3.12, Conda)
- **Base de Datos:** DuckDB (almacenamiento ligero y rápido para ~15M de registros)

### Fases de Ejecución:
1.  **Fase 1 (Scraping):** Obtiene URLs de descarga desde el HTML del SERVEL.
2.  **Fase 2 (Extracción):** Desbloquea PDFs (`pikepdf`) y extrae nombres mediante coordenadas (`PyMuPDF`).
3.  **Fase 3 (Base de Datos):** Almacena la data estructurada en un archivo `.db`.
4.  **Fase 4 (Pipeline):** Orquesta todo el proceso de forma secuencial, descargando y eliminando PDFs para optimizar el espacio.

## Instrucciones para Agentes de IA

1.  **Activación:** `conda activate padron-2025`
2.  **Scripts en `src/`:**
    - `scraper.py`: Genera el CSV inicial de URLs.
    - `extractor.py`: Lógica de procesamiento de PDFs.
    - `database.py`: Gestión de la base de datos DuckDB.
    - `pipeline.py`: Ejecución masiva secuencial.

## Estructura de Directorios

- `data/raw/`: Archivos fuente originales.
- `data/processed/`: Base de datos y archivos CSV finales.
- `data/temp/`: Espacio para procesamiento temporal de PDFs.
- `src/`: Código fuente del proyecto.
