# Proyecto: Padrón Electoral 2025 - Chile

Este proyecto automatiza la descarga, desbloqueo, extracción y almacenamiento del Padrón Electoral 2025 del SERVEL en una base de datos relacional de alto rendimiento, junto con un sistema de cruce de datos (matching) para identificar beneficiarios específicos.

## Arquitectura de Datos (DuckDB)

- **`regiones`**: Maestros de las 16 regiones.
- **`comunas`**: Maestros de las 346 comunas vinculadas a su región.
- **`electores`**: ~15.6M de registros vinculados por `comuna_id`.
- **`log_procesamiento`**: Tabla de auditoría que registra el éxito de cada extracción.

## Robustez y Validación de Integridad

El sistema está diseñado para una ejecución masiva con garantías de seguridad:

- **Validación Cruzada (Double Check):** El script extrae el número de "Registros" oficial desde un área específica del PDF `(45, 50, 50, 105)`. Este dato se compara en tiempo real con la cantidad de nombres extraídos.
- **Sistema de Checkpoints:** Permite reanudar el proceso desde la última comuna exitosa.
- **Atomicidad:** Las comunas se procesan íntegramente en memoria y se insertan en la DB solo al finalizar con éxito.

## Estado del Proyecto

### Fase 1: Extracción y Matching Heurístico (Completado)
- **Extracción:** 100% de las comunas procesadas (346/346) con un **99.9987%** de precisión (15.6M registros).
- **Metodología de Matching:** Embudo de 4 capas (Exacto, Subconjunto Ordenado, Fonética Estricta, Fonética + Subconjunto).
- **Resultados:** **74.64%** de matches encontrados (7,147 coincidencias sobre 9,575).

### Fase 2: Matching Probabilístico con Splink (En Desarrollo / Experimental)
- **Objetivo:** Implementar el modelo Fellegi-Sunter para mejorar el hallazgo de casos complejos.
- **Estado:** Fase incompleta. Se ha explorado la integración de Splink con DuckDB para generar un ranking de candidatos por probabilidad, pero los resultados definitivos aún no han sido consolidados en los reportes finales.

## Instrucciones de Uso

1.  **Ambiente:** `conda activate padron-2025`
2.  **Scripts de Extracción:**
    - `python src/extraction/scraper.py`
    - `python src/extraction/pipeline.py`
3.  **Scripts de Matching Heurístico:**
    - `python src/matching_heuristic/engine.py`
4.  **Scripts de Matching Splink (Experimental):**
    - `python src/matching_splink/engine.py`

## Consultas de Auditoría (SQL)
```sql
-- Verificar diferencias entre conteo oficial del PDF y extracción real
SELECT 
    c.nombre as comuna, 
    l.registros_oficiales as oficial, 
    l.registros_extraidos as extraidos,
    (l.registros_extraidos - l.registros_oficiales) as diferencia
FROM log_procesamiento l
JOIN comunas c ON l.comuna_id = c.id
WHERE diferencia != 0;
```
