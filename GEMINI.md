# Proyecto: Padrón Electoral 2025 - Chile

Este proyecto automatiza la descarga, desbloqueo, extracción y almacenamiento del Padrón Electoral 2025 del SERVEL en una base de datos relacional.

## Arquitectura de Datos

- **Ambiente:** `padron-2025` (Python 3.12, Conda)
- **Base de Datos:** DuckDB (`data/processed/padron_definitivo.db`)

### Modelo Relacional (3 Tablas):
1.  **`regiones`**: Almacena las 16 regiones de Chile.
2.  **`comunas`**: Almacena las 346 comunas, vinculadas a su región.
3.  **`electores`**: Almacena los nombres de los electores, vinculados a su comuna (`comuna_id`).

## Robustez y Recuperación de Fallos

El pipeline (`src/pipeline.py`) incluye mecanismos de seguridad para procesos largos:

- **Sistema de Checkpoints:** Antes de procesar una comuna, el script verifica si ya existen registros para ella en la base de datos. Si es así, la salta (`[SKIP]`), permitiendo reanudar el proceso desde donde quedó tras una interrupción.
- **Atomicidad por Comuna:** La inserción en la base de datos se realiza en bloque solo después de que el PDF ha sido procesado por completo. Si el proceso falla a la mitad de un PDF, no se guarda información parcial, evitando datos corruptos.
- **Gestión de Espacio:** Cada PDF se descarga, se procesa y se elimina inmediatamente para mantener un uso de disco mínimo.

## Instrucciones para Agentes de IA

1.  **Activación:** `conda activate padron-2025`
2.  **Scripts en `src/`:**
    - `python src/scraper.py`: Extrae URLs del HTML.
    - `python src/database.py`: Inicializa y puebla tablas maestras.
    - `python src/extractor.py`: Procesa PDFs (desbloqueo y extracción).
    - `python src/pipeline.py`: Orquestador masivo con soporte para reanudación.
    - `python src/validate_all.py`: Valida el flujo completo para una comuna.

## Consultas de Ejemplo (SQL):
```sql
-- ¿Cuántos electores hay en total?
SELECT count(*) FROM electores;

-- ¿Cuántos electores hay por región?
SELECT r.nombre, count(e.nombre) as total
FROM electores e
JOIN comunas c ON e.comuna_id = c.id
JOIN regiones r ON c.region_id = r.id
GROUP BY r.nombre
ORDER BY total DESC;
```
