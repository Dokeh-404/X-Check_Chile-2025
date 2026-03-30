# Proyecto: Padrón Electoral 2025 - Chile

Este proyecto automatiza la descarga, desbloqueo, extracción y almacenamiento del Padrón Electoral 2025 del SERVEL en una base de datos relacional de alto rendimiento.

## Arquitectura de Datos (DuckDB)

- **`regiones`**: Maestros de las 16 regiones.
- **`comunas`**: Maestros de las 346 comunas vinculadas a su región.
- **`electores`**: ~15M de registros vinculados por `comuna_id`.
- **`log_procesamiento`**: Tabla de auditoría que registra el éxito de cada extracción.

## Robustez y Validación de Integridad

El sistema está diseñado para una ejecución única y masiva con garantías de seguridad:

- **Validación Cruzada (Double Check):** El script extrae el número de "Registros" oficial desde un área específica del PDF `(45, 50, 50, 105)` usando filtros de color negro. Este dato se compara en tiempo real con la cantidad de nombres extraídos.
- **Sistema de Checkpoints:** Permite reanudar el proceso desde la última comuna exitosa en caso de interrupción.
- **Atomicidad:** Las comunas se procesan íntegramente en memoria y se insertan en la DB solo al finalizar con éxito, evitando datos parciales.
- **Gestión de Espacio:** Descarga, procesa y elimina cada PDF secuencialmente.

## Estado del Proyecto

### Fase 1: Matching Heurístico (Completado)
- **Metodología:** Embudo de 4 capas (Exacto, Subconjunto, Fonética, Fonética Subset).
- **Resultados:** ~78% de matches encontrados sobre 9,575 registros.
- **Logros:** Limpieza profunda de la DB (15.6M filas), indexación y normalización de conectores.

### Fase 2: Matching Probabilístico (En Progreso)
- **Objetivo:** Superar el 78% de éxito utilizando **Splink** (Modelo Fellegi-Sunter).
- **Estrategia:** 
  - Implementación de modelo probabilístico en DuckDB.
  - Reporte basado en umbrales de confianza (>85%).
  - Top 3 de candidatos probables por cada registro no exacto.

## Instrucciones de Uso

1.  **Ambiente:** `conda activate padron-2025`
2.  **Scripts de Extracción:**
    - `python src/extraction/scraper.py`
    - `python src/extraction/pipeline.py`
3.  **Scripts de Matching (Fase 1):**
    - `python src/matching/prepare_db.py`
    - `python src/matching/prepare_beneficiarios.py`
    - `python src/matching/engine.py`
4.  **Scripts de Matching (Fase 2 - Splink):**
    - `python src/matching_splink/engine.py` (Próximamente)


## Consultas de Auditoría (SQL)
Para verificar la calidad de la extracción tras la carga:
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
