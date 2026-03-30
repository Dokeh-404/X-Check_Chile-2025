# Resumen Metodológico: Procesamiento de Datos Servel

Este documento detalla el proceso técnico para transformar los archivos PDF del Servel en una base de datos estructurada y realizar el cruce de información con el listado de objetivos.

---

## 1. Fases del Desarrollo Técnico

Para garantizar la precisión de los resultados, el trabajo se dividió en dos dimensiones:

* **Investigación y Análisis:** Estudio de la estructura de los documentos, limpieza de inconsistencias y diseño de criterios de búsqueda.
* **Implementación:** Desarrollo del software para la extracción automatizada, almacenamiento y cruce de datos.

### Desglose de Actividades

* **Recolección Automatizada (Scraping):** Programación de un bot para descargar de forma eficiente todos los enlaces del sitio del Servel y centralizarlos en un inventario (`.csv`).
* **Extracción y Conversión:** Transformación de la estructura visual del PDF a datos procesables, identificando patrones para evitar pérdida de información entre páginas.
* **Arquitectura de Datos:** Diseño de una base de datos optimizada para gestionar y consultar rápidamente los **~15 millones de registros** nacionales.
* **Cruce de Información y Verificación:**
    * Limpieza del listado de nombres a buscar.
    * **Algoritmo de búsqueda en cascada:** Se prioriza la coincidencia exacta y se aplican técnicas de búsqueda difusa para capturar nombres con errores de digitación o tildes faltantes.
* **Consolidación de Resultados:** Entrega del Excel original enriquecido con las nuevas columnas de datos encontrados.

---

## 2. Inversión de Tiempo (Desarrollo e Investigación)

| Etapa del Proceso | Análisis y Diseño | Ejecución Técnica | Total |
| :--- | :--- | :--- | :--- |
| **Descarga de archivos** | 1h 00min | 1h 00min | 2h 00min |
| **Extracción de PDFs** | 1h 00min | 2h 00min | 3h 00min |
| **Gestión de Base de Datos** | 0h 30min | 1h 00min | 1h 30min |
| **Cruce de Datos (Matching)** | 0h 30min | 2h 00min | 2h 30min |
| **Generación de Reportes** | 0h 30min | 1h 00min | 1h 30min |
| **TOTAL** | **3h 30min** | **6h 00min** | **10h 30min** |

---

## 3. Rendimiento del Procesamiento (Ejecución del Sistema)

Para evaluar la eficiencia del sistema, es necesario distinguir entre el procesamiento masivo de la fuente original y la búsqueda específica de objetivos.

### A. Extracción y Almacenamiento Maestro
Es el tiempo que el software tarda en leer cada PDF del Servel, extraer los datos y guardarlos de forma organizada en nuestro modelo de datos. Este proceso se realiza **una sola vez** por cada archivo.

| Comuna | Cantidad de Registros | Tiempo de Extracción |
| :--- | :--- | :--- |
| *[Concepción]* | *[X mil]* | *[X min]* |
| *[Comuna 2]* | *[X mil]* | *[X min]* |

### B. Búsqueda y Cruce de Objetivos
Una vez creada la base de datos maestra, estos son los tiempos requeridos para consultar el listado de nombres solicitado por el equipo editorial contra los ~15 millones de registros.

* **Búsqueda Exacta:** Coincidencia de caracteres 1 a 1 (Segundos/Minutos).
* **Búsqueda Difusa (Fuzzy):** Algoritmo que identifica nombres similares, errores de tildes o variaciones ortográficas (Tiempo variable según complejidad).

> **Nota:** La separación de estos procesos permite que, ante nuevas solicitudes de búsqueda de nombres, solo se deba ejecutar la fase B, evitando repetir el procesamiento de los archivos originales.