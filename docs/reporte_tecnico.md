# Reporte Técnico Detallado: Proyecto X-Check Chile 2025

Este documento detalla la metodología, los procesos técnicos y el desglose de esfuerzos invertidos en el desarrollo del sistema de extracción y cruce del Padrón Electoral 2025.

## I. Introducción y Contexto
El proyecto surgió de la necesidad de consolidar y analizar la información del Padrón Electoral de Chile (SERVEL), un conjunto de datos masivo (~15.6M de registros) distribuido originalmente en 346 archivos PDF protegidos. El objetivo fue transformar esta información en una base de datos analítica estructurada y realizar un cruce de datos con un listado específico de 9,575 beneficiarios.

## II. Metodología (Pipeline de Datos)

### 1. Extracción (ETL)
*   **Herramientas:** Python, `PyMuPDF (fitz)` para extracción espacial, `pikepdf` para desbloqueo de restricciones y `pandas` para gestión de metadatos.
*   **Técnica:** Se implementó una lógica de lectura por coordenadas específicas para capturar nombres y el conteo oficial de cada página. Para garantizar la pureza de los datos, se aplicaron filtros de color (negro) y exclusión de áreas no deseadas (encabezados/pies de página).
*   **Gestión de Base de Datos:** Se utilizó **DuckDB** como motor de almacenamiento columnar por su eficiencia extrema en consultas analíticas masivas sobre millones de filas.

### 2. Limpieza y Normalización
*   **Estandarización:** Se convirtieron todos los nombres a mayúsculas, se eliminaron tildes, caracteres especiales y espacios múltiples.
*   **Conectores:** Se implementó una lógica para ignorar conectores comunes ("DE", "DEL", "LA", "LAS") en las capas de matching fonético para evitar falsos positivos.

### 3. Lógica de Cruce (Matching Heurístico)
Se diseñó un sistema de búsqueda en "embudo" de 4 capas:
*   **Capa 1 (Exacta):** Comparación directa de cadenas normalizadas (51% de éxito).
*   **Capa 2 (Subconjunto):** Identificación de nombres completos contenidos dentro de otros registros, útil para casos de segundos apellidos omitidos (22.8% de éxito).
*   **Capa 3 (Fonética):** Aplicación de algoritmos `Soundex` y `Double Metaphone` para capturar errores de digitación (0.27% de éxito).
*   **Capa 4 (Fonética + Subconjunto):** Combinación de ambas técnicas para casos complejos (0.58% de éxito).

## III. Desglose de Horas Invertidas (20 Horas)

| Etapa | Actividad | Horas |
| :--- | :--- | :---: |
| **Investigación y Scripting** | Análisis de estructura PDF, desarrollo de scraper inicial y orquestador con checkpoints. | 8h |
| **Procesamiento y Limpieza** | Ejecución de la extracción nacional, normalización de la DB de 15.6M de filas y optimización de índices. | 6h |
| **Validación y Matching** | Desarrollo del motor de cruce de 4 capas, depuración de falsos positivos y control de calidad. | 4h |
| **Reportes Finales** | Generación de resúmenes de integridad, exportación de resultados y documentación técnica. | 2h |
| **TOTAL** | | **20h** |

## IV. Resultados y Hallazgos
*   **Estadísticas de la Data:** Se capturaron **15,617,960** electores. La diferencia con el conteo oficial fue de solo 207 registros (0.0013% de error marginal).
*   **Calidad del Cruce:** Se identificó que el 25% de los beneficiarios restantes (no encontrados) corresponden a:
    *   Errores ortográficos críticos en el origen de datos de entrada.
    *   Casos de homonimia parcial que no superaron los umbrales de confianza configurados.
    *   Nombres extremadamente truncados en el listado de origen.

## V. Alcances y Limitaciones
*   **Incluye:** Sistema automatizado de descarga, procesamiento completo nacional, base de datos DuckDB optimizada y reportes de matching exportables a Excel/CSV.
*   **No incluye:** Actualización automática del padrón tras nuevas publicaciones del SERVEL (requiere ejecución manual del pipeline). Limitado a los campos de nombre y comuna de inscripción.

## VI. Entregables
1.  **Base de Datos:** `data/processed/padron_definitivo_2025.db` (DuckDB).
2.  **Reportes de Cruce:** `reports/matching_results_layer_1-4.xlsx`.
3.  **Scripts de Procesamiento:** Carpeta `src/`.
4.  **Documentación:** Carpeta `docs/`.

---
*Reporte Técnico Final - Diego Prokes Herbage*
