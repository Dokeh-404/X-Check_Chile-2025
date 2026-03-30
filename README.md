# 🗳️ X-Check Chile 2025: Extracción y Cruce de Datos Padrón SERVEL

Este proyecto automatiza la descarga, desbloqueo y extracción de datos del **Padrón Electoral Definitivo 2025** de Chile, consolidando 15.6 millones de registros y realizando un cruce inteligente con listados específicos de beneficiarios.

## 📋 Resumen del Proyecto
1.  **Extracción Masiva:** Procesamiento de 346 comunas (100% del territorio nacional).
2.  **Integridad de Datos:** Precisión del **99.9987%** en la captura de electores.
3.  **Matching Heurístico:** Algoritmo de 4 capas con un **74.64%** de efectividad.
4.  **Matching Probabilístico (Splink):** Fase experimental en desarrollo para capturar casos complejos mediante el modelo Fellegi-Sunter.

## 📊 Arquitectura del Sistema
El proyecto utiliza **DuckDB** como motor analítico por su alto rendimiento sobre millones de filas, operando con un modelo relacional de 3 tablas (Regiones, Comunas, Electores) y un sistema de auditoría en tiempo real.

## 📂 Flujo de Trabajo (Pipeline)
1.  **Scraping:** Obtención de URLs oficiales desde el portal SERVEL.
2.  **Extracción PDF:** Desbloqueo y lectura espacial de nombres por coordenadas y filtros de color.
3.  **Matching Heurístico:** Capas Exacta, Subconjunto Ordenado, Fonética Estricta y Mixta.
4.  **Matching Probabilístico (Splink - *Incompleto*):** Integración en curso para mejorar la precisión en registros con múltiples errores de escritura.

## 📈 Resultados Finales
- **Electores procesados:** 15,618,167
- **Precisión de extracción:** Solo 207 discrepancias a nivel nacional.
- **Beneficiarios buscados:** 9,575
- **Matches confirmados (Heurístico):** 7,147

## 🚀 Instalación y Uso
1.  **Configurar entorno:**
    ```bash
    conda env create -f environment.yml
    conda activate padron-2025
    ```
2.  **Extracción:** `python src/extraction/pipeline.py`
3.  **Cruce de Datos:** `python src/matching_heuristic/engine.py`

## 🛡️ Robustez
- **Checkpoints:** Reanudación automática tras interrupciones.
- **Atomicidad:** Inserciones en DB solo tras éxito total por comuna.
- **Double-Check:** Validación contra el "Conteo Oficial" del encabezado del PDF original.

---
Hecho con 🦾 por Diego Prokes Herbage
