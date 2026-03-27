# Configuración del Proyecto: Padrón 2025

Este proyecto utiliza un ambiente de Miniconda para el procesamiento de datos del Padrón Electoral 2025 de Chile.

## Ambiente Virtual

- **Nombre:** `padron-2025`
- **Python:** 3.12 (estable)
- **Gestor:** Conda/Miniconda
- **Dependencias:** `pandas`, `beautifulsoup4`, `lxml` (Gestionadas vía `environment.yml`)

## Scripts del Proyecto

### 1. Extracción de Datos (`extract_padron.py`)
Este script procesa el archivo HTML del SERVEL para generar un CSV con la región, comuna y enlace de descarga de cada padrón.

## Instrucciones para Agentes de IA

Si eres un agente de IA trabajando en este repositorio, sigue estas directrices:

1.  **Activación:** Antes de ejecutar cualquier script de Python o instalar dependencias, asegúrate de activar el ambiente:
    ```powershell
    conda activate padron-2025
    ```
2.  **Instalación:** Si el ambiente no está configurado, usa:
    ```powershell
    conda env update -n padron-2025 -f environment.yml
    ```
3.  **Extracción:** Para actualizar el archivo CSV (`padron_definitivo_2025.csv`), ejecuta:
    ```powershell
    python extract_padron.py
    ```

## Estructura de Archivos Relevante

- `Padrones Definitivos...html`: Archivo fuente de datos.
- `extract_padron.py`: Script principal de procesamiento.
- `environment.yml`: Configuración del ambiente conda.
