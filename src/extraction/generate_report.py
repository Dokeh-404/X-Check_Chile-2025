import duckdb
import os
import pandas as pd
from datetime import datetime

DB_PATH = os.path.join("data", "processed", "padron_definitivo.db")

def generate_full_report():
    if not os.path.exists(DB_PATH):
        print("Error: Base de datos no encontrada.")
        return

    con = duckdb.connect(DB_PATH, read_only=True)

    print("="*60)
    print("REPORTE EJECUTIVO: PADRÓN ELECTORAL CHILE 2025")
    print("="*60)

    # 1. TIEMPOS DE PROCESAMIENTO
    # Calculamos la diferencia entre el primer y último registro procesado
    time_info = con.execute("""
        SELECT 
            min(fecha_procesado) as inicio, 
            max(fecha_procesado) as fin,
            epoch(max(fecha_procesado) - min(fecha_procesado)) as segundos_totales
        FROM log_procesamiento
    """).fetchone()
    
    if time_info[0]:
        inicio = time_info[0]
        fin = time_info[1]
        total_horas = time_info[2] / 3600
        print(f"Inicio: {inicio}")
        print(f"Fin:    {fin}")
        print(f"Duración Total: {total_horas:.2f} horas")
    else:
        print("No hay datos de tiempo en el log.")

    # 2. RESUMEN NACIONAL (INTEGRIDAD)
    nacional = con.execute("""
        SELECT 
            sum(registros_oficiales) as oficial,
            sum(registros_extraidos) as extraido,
            count(*) as comunas_procesadas
        FROM log_procesamiento
    """).fetchone()

    oficial = nacional[0] or 0
    extraido = nacional[1] or 0
    comunas = nacional[2]
    
    print("\n" + "-"*30)
    print("INTEGRIDAD NACIONAL")
    print("-"*30)
    print(f"Comunas procesadas:  {comunas} / 346")
    print(f"Electores Oficiales: {oficial:,}")
    print(f"Electores Extraídos: {extraido:,}")
    print(f"Diferencia Total:    {extraido - oficial:,}")
    print(f"Porcentaje de Éxito: {(extraido/oficial)*100 if oficial > 0 else 0:.4f}%")

    # 3. RESUMEN POR REGIÓN
    print("\n" + "-"*30)
    print("DETALLE POR REGIÓN")
    print("-"*30)
    region_stats = con.execute("""
        SELECT 
            r.nombre as region,
            sum(l.registros_oficiales) as oficial,
            sum(l.registros_extraidos) as extraido,
            count(l.comuna_id) as n_comunas,
            r.id
        FROM log_procesamiento l
        JOIN comunas c ON l.comuna_id = c.id
        JOIN regiones r ON c.region_id = r.id
        GROUP BY r.nombre, r.id
        ORDER BY r.id
    """).df()
    
    # Eliminar columna id del dataframe final para que no ensucie
    region_stats = region_stats.drop(columns=['id'])
    
    region_stats['Diferencia'] = region_stats['extraido'] - region_stats['oficial']
    region_stats['% Coincidencia'] = (region_stats['extraido'] / region_stats['oficial'] * 100).round(4)
    
    # Formatear números con comas para la consola
    pd.options.display.float_format = '{:,.4f}'.format
    print(region_stats.to_string(index=False))

    # 4. TOP 10 COMUNAS CON DIFERENCIAS (Si las hay)
    print("\n" + "-"*30)
    print("ALERTAS: COMUNAS CON DISCREPANCIAS")
    print("-"*30)
    alertas = con.execute("""
        SELECT 
            c.nombre as comuna,
            l.registros_oficiales as oficial,
            l.registros_extraidos as extraido,
            (l.registros_extraidos - l.registros_oficiales) as diferencia
        FROM log_procesamiento l
        JOIN comunas c ON l.comuna_id = c.id
        WHERE diferencia != 0
        ORDER BY abs(diferencia) DESC
        LIMIT 10
    """).df()

    if alertas.empty:
        print("✅ ¡Perfecto! No se encontraron discrepancias en ninguna comuna.")
    else:
        print(alertas.to_string(index=False))

    con.close()

if __name__ == "__main__":
    generate_full_report()
