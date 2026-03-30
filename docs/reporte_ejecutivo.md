# Reporte Ejecutivo: Hallazgos y Metodología del Padrón Electoral 2025

**Fecha:** 30 de marzo de 2026
**Responsable:** Diego Prokes Herbage
**Audiencia:** Equipo Editorial / Periodistas de Investigación

---

## 1. Resumen de Hallazgos
Tras procesar los 15.6 millones de registros del Padrón Electoral 2025, hemos logrado identificar al **74.64%** de la lista de beneficiarios (7,147 personas de un total de 9,575). 

Este cruce de datos permite ahora geolocalizar a estos beneficiarios por comuna y región, abriendo la puerta a análisis territoriales sobre la distribución de beneficios públicos.

## 2. ¿Cómo buscamos? El sistema de "Capas"
Para asegurar la mayor precisión posible, no hicimos una búsqueda simple. Utilizamos un sistema de "embudo" o capas, donde cada capa es un poco más flexible que la anterior:

1.  **Capa 1: Identidad Exacta (51% de los casos)**
    *   El nombre coincide letra por letra. Es la certeza absoluta.
2.  **Capa 2: Nombres Incompletos (22.8% de los casos)**
    *   Útil cuando el beneficiario fue registrado sin su segundo apellido o con nombres abreviados. El sistema detecta si el nombre del beneficiario está "contenido" dentro de un elector real.
3.  **Capa 3: Sonidos Similares (0.27% de los casos)**
    *   Captura errores de digitación (ej: "Velasquez" vs "Velásquez" o "Jimenez" con "G"). Se basa en cómo suena el nombre, no solo en cómo se escribe.
4.  **Capa 4: Combinada - El "Último Recurso" (0.58% de los casos)**
    *   Busca nombres que suenan parecido **y además** están incompletos. Es la capa más agresiva.

## 3. Nota Crítica sobre la "Confianza"
En los archivos Excel (`matching_results_layer_4.xlsx`), verán una columna de "Confianza" (70%, 80%, 100%). **Es vital entender que este porcentaje no es una verdad absoluta.**

*   **100% (Capa 1):** Es casi imposible que sea un error, salvo que existan dos personas con el mismo nombre exacto (homonimia).
*   **70-80% (Capas 3 y 4):** Son **sugerencias de búsqueda**. Debido a que se basan en fonética, el sistema podría sugerir a un "Juan Pérez" cuando buscamos a un "Joan Pires". 
*   **Recomendación:** Para cualquier hallazgo en las Capas 3 y 4 que sea crítico para una noticia, **se requiere validación manual o una segunda fuente de datos**. No se debe publicar un nombre de estas capas sin verificar que la comuna o el contexto coincidan.

## 4. Conclusión Técnica
El sistema ha transformado archivos PDF "muertos" en una base de datos viva. El 25% no encontrado probablemente responde a nombres extremadamente mal escritos en la lista de origen o personas que no están inscritas en el padrón electoral actual.

---
*Este documento busca facilitar la interpretación periodística de los datos. Para detalles algorítmicos, consultar el Reporte Técnico.*
