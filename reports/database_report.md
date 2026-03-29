# Reporte Ejecutivo: Padrón Electoral Chile 2025

| Métrica | Detalle |
| :--- | :--- |
| **Inicio** | 2026-03-28 21:17:05 |
| **Fin** | 2026-03-29 13:35:18 |
| **Duración Total** | 16.30 horas |

---

## 📊 Integridad Nacional

Resumen del proceso de carga y validación a nivel país.

- **Comunas procesadas:** 346 / 346 (100%)
- **Electores Oficiales:** 15,618,167
- **Electores Extraídos:** 15,617,960
- **Diferencia Total:** -207
- **Porcentaje de Éxito:** **99.9987%**

---

## 🗺️ Detalle por Región

| Región | Oficial | Extraído | Comunas | Diferencia | % Coincidencia |
| :--- | :---: | :---: | :---: | :---: | :---: |
| XV - Arica y Parinacota | 195,604 | 195,604 | 4 | 0 | 100.00% |
| I - Tarapacá | 266,119 | 266,098 | 7 | -21 | 99.99% |
| II - Antofagasta | 500,062 | 500,061 | 9 | -1 | 99.99% |
| III - Atacama | 248,271 | 248,271 | 9 | 0 | 100.00% |
| IV - Coquimbo | 677,000 | 676,994 | 15 | -6 | 99.99% |
| V - Valparaíso | 1,693,743 | 1,693,732 | 38 | -11 | 99.99% |
| RM - Metropolitana | 6,080,386 | 6,080,254 | 52 | -132 | 99.99% |
| VI - O'Higgins | 830,744 | 830,741 | 33 | -3 | 99.99% |
| VII - Maule | 950,226 | 950,223 | 30 | -3 | 99.99% |
| XVI - Ñuble | 451,851 | 451,851 | 21 | 0 | 100.00% |
| VIII - Biobío | 1,379,927 | 1,379,911 | 33 | -16 | 99.99% |
| IX - La Araucanía | 925,402 | 925,394 | 32 | -8 | 99.99% |
| XIV - Los Ríos | 370,100 | 370,100 | 12 | 0 | 100.00% |
| X - Los Lagos | 789,065 | 789,060 | 30 | -5 | 99.99% |
| XI - Aysén | 99,575 | 99,575 | 10 | 0 | 100.00% |
| XII - Magallanes | 160,092 | 160,091 | 11 | -1 | 99.99% |

---

## ⚠️ Alertas: Comunas con Discrepancias

Se listan las 10 comunas con mayor diferencia entre el conteo oficial y los registros extraídos.

| Comuna | Oficial | Extraído | Diferencia |
| :--- | :---: | :---: | :---: |
| Santiago | 386,974 | 386,902 | -72 |
| Iquique | 166,841 | 166,820 | -21 |
| Las Condes | 283,455 | 283,442 | -13 |
| Providencia | 170,044 | 170,033 | -11 |
| Ñuñoa | 216,817 | 216,809 | -8 |
| Lo Barnechea | 92,196 | 92,191 | -5 |
| Concepción | 203,012 | 203,007 | -5 |
| Temuco | 249,546 | 249,542 | -4 |
| Estación Central | 131,570 | 131,567 | -3 |
| Colina | 111,213 | 111,210 | -3 |

---

## 💡 Conclusiones

1. **Tiempo de Procesamiento:** El proceso completo tomó **16.30 horas**, operando sobre más de 15 millones de registros.
2. **Integridad de los Datos:** Se alcanzó una cobertura del **100% de las comunas** (346/346). La pérdida de solo 207 registros sobre un universo de 15.6M demuestra una precisión excepcional.
3. **Análisis por Región:** 
   - 5 regiones obtuvieron una precisión del **100.00%** (Arica, Atacama, Ñuble, Los Ríos y Aysén).
   - La Región Metropolitana concentra el 63% de las discrepancias totales (-132), principalmente en la comuna de Santiago.
4. **Diagnóstico Técnico:** Las discrepancias marginales en comunas de alta densidad se atribuyen a:
   - Nombres extremadamente largos que exceden las coordenadas de captura del PDF.
   - Variaciones mínimas en el renderizado de páginas específicas en archivos de gran volumen.
