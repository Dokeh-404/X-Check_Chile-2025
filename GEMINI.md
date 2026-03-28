# Proyecto: Padrón Electoral 2025 - Chile

Este proyecto automatiza la descarga, desbloqueo, extracción y almacenamiento del Padrón Electoral 2025 del SERVEL en una base de datos relacional.

## Arquitectura de Datos

- **Ambiente:** `padron-2025` (Python 3.12, Conda)
- **Base de Datos:** DuckDB (`data/processed/padron_definitivo.db`)

### Modelo Relacional (3 Tablas):
1.  **`regiones`**: Almacena las 16 regiones de Chile.
2.  **`comunas`**: Almacena las 346 comunas, vinculadas a su región.
3.  **`electores`**: Almacena los nombres de los electores, vinculados a su comuna (`comuna_id`).

Este esquema permite realizar consultas complejas (ej: conteos por región, búsquedas por comuna) de forma extremadamente eficiente sobre los ~15M de registros.

## Instrucciones para Agentes de IA

1.  **Activación:** `conda activate padron-2025`
2.  **Scripts en `src/`:**
    - `python src/scraper.py`: Extrae URLs del HTML.
    - `python src/database.py`: Inicializa y puebla tablas maestras.
    - `python src/extractor.py`: Procesa PDFs (desbloqueo y extracción).
    - `python src/pipeline.py`: Orquestador masivo relacional.
    - `python src/validate_all.py`: Valida el flujo completo para una comuna.

## Consultas de Ejemplo (SQL):
Para validar datos en la consola de DuckDB:
```sql
-- ¿Cuántos electores hay en la Región de Valparaíso?
SELECT count(*) 
FROM electores e 
JOIN comunas c ON e.comuna_id = c.id 
JOIN regiones r ON c.region_id = r.id 
WHERE r.nombre LIKE '%Valparaíso%';

-- ¿Está Juan Pérez en San Antonio?
SELECT e.nombre, c.nombre 
FROM electores e 
JOIN comunas c ON e.comuna_id = c.id 
WHERE e.nombre ILIKE '%JUAN PEREZ%' AND c.nombre = 'San Antonio';
```
