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

## Instrucciones de Uso

1.  **Ambiente:** `conda activate padron-2025`
2.  **Scripts Principales:**
    - `python src/scraper.py`: Genera el listado de URLs desde el HTML.
    - `python src/pipeline.py`: Inicia la carga masiva (Revisar filtros de región en el código antes de ejecutar).
    - `python src/db_shell.py`: Consola interactiva para consultas SQL.
    - `python src/inspect_db.py`: Reporte rápido de salud de la base de datos.

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
