#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ejemplos de uso del Extractor de OpenAQ
======================================

Este archivo contiene varios ejemplos prácticos de cómo usar
el extractor de datos de calidad del aire de OpenAQ.
"""
#%%
from openaq_extractor import OpenAQExtractor
from datetime import datetime, timedelta
import pandas as pd


def ejemplo_basico():
    """
    Ejemplo básico: obtener datos de PM2.5 de Madrid en la última semana
    """
    print("=== Ejemplo 1: Datos de Madrid ===")
    
    # Inicializar (reemplaza con tu API key)
    api_key = "91eab8b4c15ab8e5eda9712fa803abe4bb45e5a6c8ee961d295de18b0b15722a"
    extractor = OpenAQExtractor(api_key)
    
    # Fechas
    fecha_fin = datetime.now().strftime('%Y-%m-%d')
    fecha_inicio = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    # Obtener datos
    datos = extractor.get_measurements(
        country='ES',
        city='Madrid',
        parameter='pm25',
        date_from=fecha_inicio,
        date_to=fecha_fin,
        limit=1000
    )
    
    if not datos.empty:
        print(f"✅ Obtenidos {len(datos)} registros de PM2.5 en Madrid")
        extractor.save_to_csv(datos, 'madrid_pm25.csv')
        
        # Mostrar estadísticas básicas
        print(f"Valor promedio: {datos['value'].mean():.2f} µg/m³")
        print(f"Valor máximo: {datos['value'].max():.2f} µg/m³")
        print(f"Valor mínimo: {datos['value'].min():.2f} µg/m³")
    else:
        print("❌ No se encontraron datos")


def ejemplo_multiples_ciudades():
    """
    Ejemplo: obtener datos de múltiples ciudades españolas
    """
    print("\n=== Ejemplo 2: Múltiples ciudades españolas ===")
    
    api_key = "91eab8b4c15ab8e5eda9712fa803abe4bb45e5a6c8ee961d295de18b0b15722a"
    extractor = OpenAQExtractor(api_key)
    
    ciudades = ['Madrid', 'Barcelona', 'Valencia', 'Sevilla']
    fecha_fin = datetime.now().strftime('%Y-%m-%d')
    fecha_inicio = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
    
    datos_consolidados = []
    
    for ciudad in ciudades:
        print(f"Obteniendo datos de {ciudad}...")
        
        datos = extractor.get_measurements(
            country='ES',
            city=ciudad,
            parameter=['pm25', 'pm10'],
            date_from=fecha_inicio,
            date_to=fecha_fin,
            limit=500
        )
        
        if not datos.empty:
            datos_consolidados.append(datos)
            print(f"  ✅ {len(datos)} registros de {ciudad}")
        else:
            print(f"  ❌ Sin datos de {ciudad}")
    
    if datos_consolidados:
        # Consolidar todos los datos
        df_final = pd.concat(datos_consolidados, ignore_index=True)
        extractor.save_to_csv(df_final, 'ciudades_espanolas.csv')
        
        # Resumen por ciudad
        resumen = df_final.groupby(['city', 'parameter'])['value'].agg(['count', 'mean', 'std'])
        print("\nResumen por ciudad:")
        print(resumen)


def ejemplo_pais_completo():
    """
    Ejemplo: análisis de un país completo
    """
    print("\n=== Ejemplo 3: Análisis de México ===")
    
    api_key = "91eab8b4c15ab8e5eda9712fa803abe4bb45e5a6c8ee961d295de18b0b15722a"
    extractor = OpenAQExtractor(api_key)
    
    # Obtener ciudades disponibles en México
    print("Obteniendo ciudades disponibles en México...")
    ciudades = extractor.get_cities(country_code='MX')
    print(f"Ciudades encontradas: {len(ciudades)}")
    
    for ciudad in ciudades[:5]:  # Mostrar solo las primeras 5
        print(f"  - {ciudad.get('city', 'N/A')} ({ciudad.get('count', 0)} mediciones)")
    
    # Obtener datos recientes de México
    fecha_fin = datetime.now().strftime('%Y-%m-%d')
    fecha_inicio = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
    
    datos_mexico = extractor.get_measurements(
        country='MX',
        parameter=['pm25', 'o3'],
        date_from=fecha_inicio,
        date_to=fecha_fin,
        limit=2000,
        max_pages=5
    )
    
    if not datos_mexico.empty:
        extractor.save_to_csv(datos_mexico, 'mexico_calidad_aire.csv')
        
        # Análisis por ciudad
        analisis_ciudades = datos_mexico.groupby('city')['value'].agg(['count', 'mean'])
        analisis_ciudades = analisis_ciudades.sort_values('count', ascending=False)
        
        print(f"\nTop 10 ciudades con más mediciones:")
        print(analisis_ciudades.head(10))


def ejemplo_contaminantes_especificos():
    """
    Ejemplo: análisis de contaminantes específicos
    """
    print("\n=== Ejemplo 4: Análisis de contaminantes ===")
    
    api_key = "91eab8b4c15ab8e5eda9712fa803abe4bb45e5a6c8ee961d295de18b0b15722a"
    extractor = OpenAQExtractor(api_key)
    
    # Obtener todos los parámetros disponibles
    parametros = extractor.get_parameters()
    print("Parámetros disponibles:")
    for param in parametros:
        print(f"  - {param.get('displayName', 'N/A')} ({param.get('id', 'N/A')})")
    
    # Análisis de múltiples contaminantes en una ciudad
    fecha_fin = datetime.now().strftime('%Y-%m-%d')
    fecha_inicio = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
    
    contaminantes = ['pm25', 'pm10', 'o3', 'no2', 'so2', 'co']
    
    datos_completos = extractor.get_measurements(
        country='US',
        city='Los Angeles',
        parameter=contaminantes,
        date_from=fecha_inicio,
        date_to=fecha_fin,
        limit=1500
    )
    
    if not datos_completos.empty:
        extractor.save_to_csv(datos_completos, 'los_angeles_todos_contaminantes.csv')
        
        # Crear tabla pivot para análisis
        tabla_pivot = datos_completos.pivot_table(
            values='value',
            index='fecha',
            columns='parameter',
            aggfunc='mean'
        )
        
        print("\nPromedios diarios por contaminante:")
        print(tabla_pivot.head())
        
        # Guardar tabla pivot
        tabla_pivot.to_csv('los_angeles_promedios_diarios.csv')


def ejemplo_exportar_excel():
    """
    Ejemplo: exportar datos a Excel con múltiples hojas
    """
    print("\n=== Ejemplo 5: Exportar a Excel ===")
    
    api_key = "91eab8b4c15ab8e5eda9712fa803abe4bb45e5a6c8ee961d295de18b0b15722a"
    extractor = OpenAQExtractor(api_key)
    
    fecha_fin = datetime.now().strftime('%Y-%m-%d')
    fecha_inicio = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    # Obtener datos de diferentes países
    paises = ['ES', 'FR', 'IT']
    
    with pd.ExcelWriter('calidad_aire_europa.xlsx', engine='openpyxl') as writer:
        for pais in paises:
            print(f"Procesando {pais}...")
            
            datos = extractor.get_measurements(
                country=pais,
                parameter='pm25',
                date_from=fecha_inicio,
                date_to=fecha_fin,
                limit=1000
            )
            
            if not datos.empty:
                # Guardar en hoja separada
                datos.to_excel(writer, sheet_name=pais, index=False)
                print(f"  ✅ {len(datos)} registros guardados en hoja '{pais}'")
            else:
                print(f"  ❌ Sin datos para {pais}")
    
    print("Archivo Excel creado: calidad_aire_europa.xlsx")


def ejemplo_santiago_chile():
    """
    Ejemplo específico: obtener datos completos de Santiago de Chile
    """
    print("=== Extrayendo datos de Santiago de Chile ===")
    
    # API key configurada
    api_key = "91eab8b4c15ab8e5eda9712fa803abe4bb45e5a6c8ee961d295de18b0b15722a"
    extractor = OpenAQExtractor(api_key)
    
    # Primero, exploremos qué datos están disponibles para Chile
    print("1. Explorando ciudades disponibles en Chile...")
    ciudades_chile = extractor.get_cities(country_code='CL')
    print(f"   Ciudades encontradas en Chile: {len(ciudades_chile)}")
    
    # Mostrar todas las ciudades disponibles
    for ciudad in ciudades_chile:
        print(f"   - {ciudad.get('city', 'N/A')} ({ciudad.get('count', 0)} mediciones)")
    
    # Obtener parámetros disponibles
    print("\n2. Verificando parámetros disponibles...")
    parametros = extractor.get_parameters()
    parametros_disponibles = [p['id'] for p in parametros[:10]]
    print(f"   Parámetros principales: {', '.join(parametros_disponibles)}")
    
    # Fechas para análisis (último mes)
    fecha_fin = datetime.now().strftime('%Y-%m-%d')
    fecha_inicio = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    print(f"\n3. Obteniendo datos de Santiago desde {fecha_inicio} hasta {fecha_fin}...")
    
    # Intentar obtener datos de Santiago con varios parámetros
    contaminantes = ['pm25', 'pm10', 'o3', 'no2', 'so2', 'co']
    
    datos_santiago = extractor.get_measurements(
        country='CL',
        city='Santiago',
        parameter=contaminantes,
        date_from=fecha_inicio,
        date_to=fecha_fin,
        limit=5000,
        max_pages=10
    )
    
    if not datos_santiago.empty:
        print(f"✅ ¡Éxito! Obtenidos {len(datos_santiago)} registros de Santiago")
        
        # Guardar datos principales
        extractor.save_to_csv(datos_santiago, 'santiago_chile_calidad_aire.csv')
        
        # Análisis detallado
        resumen = extractor.get_data_summary(datos_santiago)
        print(f"\n📊 Resumen de datos:")
        print(f"   - Período: {resumen['fechas']['fecha_inicio']} a {resumen['fechas']['fecha_fin']}")
        print(f"   - Ubicaciones: {len(resumen['ubicaciones'])} estaciones")
        print(f"   - Contaminantes encontrados: {', '.join(resumen['parametros'])}")
        
        # Estadísticas por contaminante
        print(f"\n📈 Estadísticas por contaminante:")
        for param, stats in resumen['estadisticas_por_parametro'].items():
            print(f"   {param.upper()}:")
            print(f"     - Promedio: {stats['mean']:.2f}")
            print(f"     - Máximo: {stats['max']:.2f}")
            print(f"     - Mínimo: {stats['min']:.2f}")
            print(f"     - Registros: {stats['count']}")
        
        # Análisis por ubicación
        print(f"\n🗺️  Análisis por ubicación:")
        analisis_ubicaciones = datos_santiago.groupby('location')['value'].agg(['count', 'mean'])
        analisis_ubicaciones = analisis_ubicaciones.sort_values('count', ascending=False)
        print(analisis_ubicaciones.head(10))
        
        # Crear tabla pivot por días
        if 'fecha' in datos_santiago.columns:
            tabla_diaria = datos_santiago.pivot_table(
                values='value',
                index='fecha',
                columns='parameter',
                aggfunc='mean'
            )
            tabla_diaria.to_csv('santiago_promedios_diarios.csv')
            print(f"\n📅 Promedios diarios guardados en 'santiago_promedios_diarios.csv'")
            print("Últimos 5 días:")
            print(tabla_diaria.tail())
    
    else:
        print("❌ No se encontraron datos para Santiago")
        
        # Intentar búsqueda más amplia en Chile
        print("\n🔍 Intentando búsqueda más amplia en Chile...")
        datos_chile = extractor.get_measurements(
            country='CL',
            parameter=['pm25', 'pm10'],
            date_from=fecha_inicio,
            date_to=fecha_fin,
            limit=3000,
            max_pages=5
        )
        
        if not datos_chile.empty:
            print(f"✅ Encontrados {len(datos_chile)} registros en Chile")
            extractor.save_to_csv(datos_chile, 'chile_calidad_aire.csv')
            
            # Mostrar ciudades con datos
            ciudades_con_datos = datos_chile['city'].value_counts()
            print("\nCiudades con datos disponibles:")
            print(ciudades_con_datos.head(10))


def main():
    """
    Ejecutar todos los ejemplos
    """
    print("🌍 Ejemplos de uso del Extractor de OpenAQ\n")
    
    # Ejecutar ejemplo de Santiago de Chile
    ejemplo_santiago_chile()
    
    print("\n📚 Otros ejemplos disponibles:")
    print("- ejemplo_basico() - Datos de Madrid")
    print("- ejemplo_multiples_ciudades() - Varias ciudades españolas")
    print("- ejemplo_pais_completo() - Análisis de México")
    print("- ejemplo_contaminantes_especificos() - Análisis detallado")
    print("- ejemplo_exportar_excel() - Exportar a Excel")


if __name__ == "__main__":
    main()

# %%
# Extracción específica de datos para 2 ciudades de Chile
def extraer_datos_dos_ciudades_chile():
    """
    Extrae datos de calidad del aire de 2 ciudades principales de Chile
    """
    print("🇨🇱 === EXTRACCIÓN DE DATOS DE 2 CIUDADES DE CHILE ===\n")
    
    # Configurar API
    api_key = "91eab8b4c15ab8e5eda9712fa803abe4bb45e5a6c8ee961d295de18b0b15722a"
    extractor = OpenAQExtractor(api_key)
    
    # Explorar ciudades disponibles en Chile
    print("1️⃣ Explorando ciudades disponibles en Chile...")
    ciudades_chile = extractor.get_cities(country_code='CL')
    print(f"   📍 Total ciudades encontradas: {len(ciudades_chile)}\n")
    
    # Mostrar todas las ciudades disponibles con sus conteos
    print("   Ciudades disponibles:")
    for i, ciudad in enumerate(ciudades_chile, 1):
        ciudad_nombre = ciudad.get('city', 'N/A')
        mediciones = ciudad.get('count', 0)
        print(f"   {i:2d}. {ciudad_nombre:20} - {mediciones:,} mediciones")
    
    # Seleccionar las 2 ciudades con más datos
    if len(ciudades_chile) >= 2:
        # Ordenar por número de mediciones y tomar las 2 primeras
        ciudades_ordenadas = sorted(ciudades_chile, key=lambda x: x.get('count', 0), reverse=True)
        ciudad1 = ciudades_ordenadas[0]['city']
        ciudad2 = ciudades_ordenadas[1]['city']
    else:
        # Ciudades predeterminadas si no hay suficientes datos
        ciudad1 = 'Santiago'
        ciudad2 = 'Valparaíso'
    
    print(f"\n2️⃣ Ciudades seleccionadas para análisis:")
    print(f"   🏙️ Ciudad 1: {ciudad1}")
    print(f"   🏙️ Ciudad 2: {ciudad2}")
    
    # Configurar fechas (últimos 2 meses para obtener más datos)
    fecha_fin = datetime.now().strftime('%Y-%m-%d')
    fecha_inicio = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d')
    
    print(f"\n3️⃣ Período de análisis: {fecha_inicio} a {fecha_fin}")
    
    # Contaminantes principales a buscar
    contaminantes = ['pm25', 'pm10', 'o3', 'no2', 'so2', 'co']
    print(f"   🧪 Contaminantes: {', '.join(contaminantes)}")
    
    # Extraer datos para cada ciudad
    datos_ciudades = {}
    
    for i, ciudad in enumerate([ciudad1, ciudad2], 1):
        print(f"\n{i+2}️⃣ Extrayendo datos de {ciudad}...")
        
        datos = extractor.get_measurements(
            country='CL',
            city=ciudad,
            parameter=contaminantes,
            date_from=fecha_inicio,
            date_to=fecha_fin,
            limit=10000,
            max_pages=15
        )
        
        if not datos.empty:
            print(f"   ✅ {len(datos):,} registros obtenidos de {ciudad}")
            datos_ciudades[ciudad] = datos
            
            # Guardar datos individuales
            filename = f"{ciudad.lower().replace(' ', '_')}_chile_calidad_aire.csv"
            extractor.save_to_csv(datos, filename)
            print(f"   💾 Datos guardados en: {filename}")
            
            # Estadísticas rápidas
            contaminantes_encontrados = datos['parameter'].unique()
            ubicaciones = datos['location'].nunique()
            print(f"   📊 Contaminantes encontrados: {', '.join(contaminantes_encontrados)}")
            print(f"   📍 Estaciones de medición: {ubicaciones}")
            
        else:
            print(f"   ❌ No se encontraron datos para {ciudad}")
    
    # Análisis comparativo si tenemos datos de ambas ciudades
    if len(datos_ciudades) >= 2:
        print(f"\n6️⃣ === ANÁLISIS COMPARATIVO ===")
        
        # Combinar datos de ambas ciudades
        todos_los_datos = []
        for ciudad, datos in datos_ciudades.items():
            todos_los_datos.append(datos)
        
        df_combinado = pd.concat(todos_los_datos, ignore_index=True)
        
        # Guardar datos combinados
        extractor.save_to_csv(df_combinado, 'chile_dos_ciudades_combinado.csv')
        print(f"   💾 Datos combinados guardados en: chile_dos_ciudades_combinado.csv")
        
        # Análisis por ciudad
        print(f"\n   📈 Resumen por ciudad:")
        resumen_ciudades = df_combinado.groupby('city').agg({
            'value': ['count', 'mean', 'min', 'max', 'std'],
            'parameter': 'nunique',
            'location': 'nunique'
        }).round(2)
        print(resumen_ciudades)
        
        # Análisis por contaminante
        print(f"\n   🧪 Análisis por contaminante:")
        for parametro in df_combinado['parameter'].unique():
            datos_param = df_combinado[df_combinado['parameter'] == parametro]
            if not datos_param.empty:
                print(f"\n   {parametro.upper()}:")
                stats_param = datos_param.groupby('city')['value'].agg(['count', 'mean', 'min', 'max']).round(2)
                print(stats_param)
        
        # Crear tabla pivot para comparación
        tabla_comparativa = df_combinado.pivot_table(
            values='value',
            index='city',
            columns='parameter',
            aggfunc=['mean', 'count']
        ).round(2)
        
        # Guardar tabla comparativa
        tabla_comparativa.to_csv('chile_comparacion_ciudades.csv')
        print(f"\n   💾 Tabla comparativa guardada en: chile_comparacion_ciudades.csv")
        
        # Análisis temporal si hay datos suficientes
        if 'fecha' in df_combinado.columns:
            tendencias_diarias = df_combinado.groupby(['fecha', 'city', 'parameter'])['value'].mean().reset_index()
            tendencias_pivot = tendencias_diarias.pivot_table(
                values='value',
                index=['fecha', 'parameter'],
                columns='city',
                aggfunc='mean'
            )
            tendencias_pivot.to_csv('chile_tendencias_diarias.csv')
            print(f"   📅 Tendencias diarias guardadas en: chile_tendencias_diarias.csv")
    
    print(f"\n✅ === EXTRACCIÓN COMPLETADA ===")
    print(f"📂 Archivos generados:")
    print(f"   • Datos individuales por ciudad")
    print(f"   • Datos combinados de ambas ciudades")
    print(f"   • Tabla comparativa entre ciudades")
    print(f"   • Tendencias diarias (si hay datos suficientes)")
    
    return datos_ciudades

# Ejecutar la extracción
if __name__ == "__main__":
    resultado = extraer_datos_dos_ciudades_chile()

# %%
