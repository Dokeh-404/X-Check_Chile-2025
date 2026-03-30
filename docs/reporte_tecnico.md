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
*   **Estandarización:** Se convirtieron todos los nombres a mayúsculas, se eliminaron tildes, caracteres especiales y espacios múltiples y se reemplazaron las N's por Ñ's.
*   **Conectores:** Se implementó una lógica para ignorar conectores comunes ("DE", "DEL", "LA", "LAS") en las capas de matching fonético para evitar falsos positivos.

## III. Arquitectura del Motor de Cruce (Matching Layered)

Se implementó una estrategia de **"embudo" (funnel)** para balancear la precisión (evitar falsos positivos) con la sensibilidad (encontrar casos difíciles). El motor procesa a los beneficiarios de forma secuencial, descartando a los ya identificados en cada paso.

### 1. El Proceso en Capas (Criterios Técnicos)

#### **Capa 1: Coincidencia Exacta (High Precision)**
*   **Lógica:** Comparación `String to String` (normalizada).
*   **Algoritmo:** `JOIN` directo en SQL.
*   **Casos:** Registros sin errores tipográficos ni abreviaturas.
*   **Confianza Asignada:** 100%.

#### **Capa 2: Subconjunto Ordenado (Subset Matching)**
*   **Lógica:** Identifica si el nombre de la lista de entrada está contenido íntegramente dentro de un registro del Padrón, respetando el orden.
*   **Algoritmo:** Expresión regular dinámica (`LIKE` con wildcards). Ej: `JUAN % PEREZ` captura `JUAN ALBERTO PEREZ GOMEZ`.
*   **Casos:** Omisión del segundo apellido o nombres intermedios en la lista de origen.
*   **Confianza Asignada:** 90%.

#### **Capa 3: Fonética Estricta (Phonetic Alignment)**
*   **Lógica:** Busca nombres que suenen idéntico, manteniendo el mismo número de palabras.
*   **Algoritmo:** `Double Metaphone` aplicado a cada palabra. Se requiere que la secuencia de códigos fonéticos sea idéntica.
*   **Casos:** Errores comunes de ortografía (S/C/Z, V/B, H omitida, tildes).
*   **Confianza Asignada:** 80%.

#### **Capa 4: Fonética Subconjunto (Phonetic Subset)**
*   **Lógica:** Combina la flexibilidad de la Capa 2 con la fonética de la Capa 3. Busca si los "sonidos" del nombre del beneficiario existen dentro de un nombre más largo en el Padrón.
*   **Algoritmo:** Secuenciación de fonemas `Metaphone`.
*   **Casos:** Nombres con faltas de ortografía y apellidos faltantes simultáneamente.
*   **Confianza Asignada:** 70%.

### 2. Por qué el enfoque en capas es crucial
1.  **Reducción de Ruido:** Al identificar primero los casos obvios (Capas 1 y 2), reducimos el universo de búsqueda para los algoritmos fonéticos, que son más propensos a errores de "choque" (dos nombres distintos que suenan igual).
2.  **Eficiencia Computacional:** Las capas iniciales se ejecutan en milisegundos mediante índices SQL en la base de datos, mientras que las capas fonéticas requieren procesamiento intensivo en Python palabra por palabra.
3.  **Auditabilidad Periodística:** Cada resultado en el archivo final indica explícitamente en qué capa fue encontrado. Esto permite priorizar su validación: los resultados de Capa 1 son seguros para uso directo, mientras que los de Capa 4 requieren mayor escrutinio.

### 3. Nota Crítica sobre la "Confianza"
En los archivos Excel (`matching_results_layer_4.xlsx`), verán una columna de "Confianza" (70%, 80%, 100%). **Es vital entender que este porcentaje no es una verdad absoluta.**

*   **(Capa 1):** Es casi imposible que sea un error, salvo que existan dos personas con el mismo nombre exacto (homonimia).
*   **(Capa 2):** Podría ser un falso positivo, pero es poco probable. Lo más probable es que en el listado de búsqueda se haya omitido el segundo nombre o algún apellido.
*   **(Capas 3 y 4):** Son **sugerencias de búsqueda**. Debido a que se basan en fonética, el sistema podría sugerir a un "Juan Pérez" cuando buscamos a un "Joan Pires". 
*   **Recomendación:** Para cualquier hallazgo en las Capas 3 y 4 que sea crítico para una noticia, **se requiere validación manual o una segunda fuente de datos**. No se debe publicar un nombre de estas capas sin verificar que la comuna o el contexto coincidan.

## IV. Desglose de Horas Invertidas (20 Horas)

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
    *   Beneficiarios que no pertenecen al padrón.

## VI. Entregables
1.  **Reportes de Cruce:** `matching_results_layer_1-4.xlsx`.
2. **Reporte Técnico**: `reporte_tecnico.pdf`.

---
*Reporte Técnico Final - Diego Prokes Herbage*
