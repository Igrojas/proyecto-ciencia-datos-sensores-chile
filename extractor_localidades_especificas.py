#!/usr/bin/env python3
"""
Script específico para obtener datos de calidad del aire de localidades específicas de Chile:
- Bocatoma
- ENAP Price
- JUNJI
- Indura

Usa la API de OpenAQ para obtener la mayor cantidad de datos posible
"""

from openaq import OpenAQ
import pandas as pd
from datetime import datetime, timedelta
import time
import os

def buscar_localidades_especificas(client, localidades_buscar):
    """
    Buscar específicamente las localidades mencionadas
    """
    print("=== BUSCANDO LOCALIDADES ESPECÍFICAS ===\n")
    
    localidades_encontradas = []
    
    for localidad in localidades_buscar:
        print(f"Buscando: {localidad}")
        
        try:
            # Buscar por nombre exacto
            locations = client.locations.list(name=localidad, country='CL', limit=100)
            
            if locations and hasattr(locations, 'results') and len(locations.results) > 0:
                print(f"  ✓ Encontradas {len(locations.results)} ubicaciones para '{localidad}'")
                
                for location in locations.results:
                    if location.country.code == 'CL':  # Verificar que sea de Chile
                        location.localidad_buscada = localidad
                        localidades_encontradas.append(location)
                        
                        print(f"    - ID: {location.id}")
                        print(f"      Nombre: {location.name}")
                        if hasattr(location, 'city') and location.city:
                            print(f"      Ciudad: {location.city.name}")
                        if hasattr(location, 'coordinates') and location.coordinates:
                            print(f"      Coordenadas: {location.coordinates.latitude}, {location.coordinates.longitude}")
            else:
                print(f"  ⚠ No se encontraron ubicaciones para '{localidad}'")
                
        except Exception as e:
            print(f"  ✗ Error al buscar '{localidad}': {e}")
        
        time.sleep(0.5)  # Pausa para no sobrecargar la API
    
    # Si no encontramos por nombre exacto, buscar por términos similares
    if len(localidades_encontradas) < len(localidades_buscar):
        print("\n=== BUSCANDO POR TÉRMINOS SIMILARES ===")
        
        for localidad in localidades_buscar:
            if not any(loc.localidad_buscada == localidad for loc in localidades_encontradas):
                print(f"\nBuscando términos similares a: {localidad}")
                
                # Buscar por partes del nombre
                terminos_busqueda = localidad.split()
                
                for termino in terminos_busqueda:
                    if len(termino) > 2:  # Solo términos de más de 2 caracteres
                        try:
                            locations = client.locations.list(name=termino, country='CL', limit=50)
                            
                            if locations and hasattr(locations, 'results') and len(locations.results) > 0:
                                for location in locations.results:
                                    if (location.country.code == 'CL' and 
                                        not any(loc.id == location.id for loc in localidades_encontradas)):
                                        
                                        # Verificar si el nombre contiene la localidad buscada
                                        if any(localidad.lower() in location.name.lower() for localidad in localidades_buscar):
                                            location.localidad_buscada = localidad
                                            localidades_encontradas.append(location)
                                            
                                            print(f"    ✓ Encontrada por término '{termino}': {location.name}")
                                            print(f"      ID: {location.id}")
                                            
                        except Exception as e:
                            print(f"      ✗ Error al buscar término '{termino}': {e}")
                        
                        time.sleep(0.3)
    
    print(f"\n=== RESUMEN DE BÚSQUEDA ===")
    print(f"Localidades buscadas: {', '.join(localidades_buscar)}")
    print(f"Localidades encontradas: {len(localidades_encontradas)}")
    
    for localidad in localidades_buscar:
        encontradas = [loc for loc in localidades_encontradas if loc.localidad_buscada == localidad]
        print(f"  - {localidad}: {len(encontradas)} ubicaciones")
    
    return localidades_encontradas

def obtener_sensores_completos(client, localidades):
    """
    Obtener todos los sensores disponibles en las localidades encontradas
    """
    print(f"\n=== OBTENIENDO SENSORES DE {len(localidades)} LOCALIDADES ===\n")
    
    todos_sensores = []
    
    for i, localidad in enumerate(localidades):
        print(f"Procesando localidad {i+1}/{len(localidades)}: {localidad.name}")
        
        try:
            # Obtener sensores de esta localidad
            sensors = client.locations.sensors(localidad.id)
            
            if sensors and hasattr(sensors, 'results') and len(sensors.results) > 0:
                print(f"  ✓ Encontrados {len(sensors.results)} sensores")
                
                for sensor in sensors.results:
                    # Agregar información de la localidad al sensor
                    sensor.localidad_id = localidad.id
                    sensor.localidad_nombre = localidad.name
                    sensor.localidad_buscada = localidad.localidad_buscada
                    sensor.ciudad = localidad.city.name if hasattr(localidad, 'city') and localidad.city else None
                    sensor.coordenadas = localidad.coordinates if hasattr(localidad, 'coordinates') else None
                    
                    todos_sensores.append(sensor)
                
                # Mostrar información de los sensores
                for j, sensor in enumerate(sensors.results[:5]):  # Mostrar primeros 5
                    print(f"    Sensor {j+1}: ID {sensor.id}")
                    if hasattr(sensor, 'name') and sensor.name:
                        print(f"      Nombre: {sensor.name}")
                    if hasattr(sensor, 'parameter') and sensor.parameter:
                        print(f"      Parámetro: {sensor.parameter.name}")
                
                if len(sensors.results) > 5:
                    print(f"    ... y {len(sensors.results) - 5} sensores más")
            else:
                print(f"  ⚠ No se encontraron sensores")
            
            time.sleep(0.5)
            
        except Exception as e:
            print(f"  ✗ Error al obtener sensores: {e}")
    
    print(f"\n✓ Total de sensores encontrados: {len(todos_sensores)}")
    return todos_sensores

def obtener_mediciones_maximas(client, sensores, max_mediciones_por_sensor=5000):
    """
    Obtener la máxima cantidad de mediciones posible de cada sensor
    """
    print(f"\n=== OBTENIENDO MÁXIMAS MEDICIONES DE {len(sensores)} SENSORES ===\n")
    
    todas_mediciones = []
    
    for i, sensor in enumerate(sensores):
        print(f"Obteniendo mediciones del sensor {i+1}/{len(sensores)}: ID {sensor.id}")
        
        try:
            # Intentar obtener el máximo de mediciones
            mediciones = client.measurements.list(
                sensors_id=sensor.id, 
                limit=max_mediciones_por_sensor
            )
            
            if mediciones and hasattr(mediciones, 'results') and len(mediciones.results) > 0:
                print(f"  ✓ Obtenidas {len(mediciones.results)} mediciones")
                
                # Agregar información del sensor a cada medición
                for medicion in mediciones.results:
                    medicion.localidad_id = sensor.localidad_id
                    medicion.localidad_nombre = sensor.localidad_nombre
                    medicion.localidad_buscada = sensor.localidad_buscada
                    medicion.ciudad = sensor.ciudad
                    medicion.coordenadas = sensor.coordenadas
                
                todas_mediciones.extend(mediciones.results)
                
                # Mostrar información de las primeras mediciones
                for j, medicion in enumerate(mediciones.results[:3]):
                    print(f"    Medición {j+1}: {medicion.parameter.name} = {medicion.value} {medicion.parameter.units}")
                    print(f"      Fecha: {medicion.period.datetime_from.utc}")
                
                if len(mediciones.results) > 3:
                    print(f"    ... y {len(mediciones.results) - 3} mediciones más")
            else:
                print(f"  ⚠ No se encontraron mediciones")
            
            time.sleep(1)  # Pausa para no sobrecargar la API
            
        except Exception as e:
            print(f"  ✗ Error al obtener mediciones: {e}")
    
    print(f"\n✓ Total de mediciones obtenidas: {len(todas_mediciones)}")
    return todas_mediciones

def convertir_a_dataframe(mediciones):
    """
    Convertir todas las mediciones a un DataFrame de pandas
    """
    if not mediciones:
        return None
    
    print("\n=== CONVIRTIENDO DATOS A DATAFRAME ===\n")
    
    datos_lista = []
    for medicion in mediciones:
        datos_dict = {
            'parametro_nombre': medicion.parameter.name,
            'parametro_id': medicion.parameter.id,
            'valor': medicion.value,
            'unidad': medicion.parameter.units,
            'fecha_desde_utc': medicion.period.datetime_from.utc,
            'fecha_desde_local': medicion.period.datetime_from.local,
            'fecha_hasta_utc': medicion.period.datetime_to.utc,
            'fecha_hasta_local': medicion.period.datetime_to.local,
            'cobertura_porcentaje': medicion.coverage.percent_complete if medicion.coverage else None,
            'sensor_id': medicion.sensor.id if hasattr(medicion, 'sensor') and medicion.sensor else None,
            'localidad_id': getattr(medicion, 'localidad_id', None),
            'localidad_nombre': getattr(medicion, 'localidad_nombre', None),
            'localidad_buscada': getattr(medicion, 'localidad_buscada', None),
            'ciudad': getattr(medicion, 'ciudad', None),
            'coordenadas_lat': getattr(medicion, 'coordenadas', None).latitude if getattr(medicion, 'coordenadas', None) else None,
            'coordenadas_lon': getattr(medicion, 'coordenadas', None).longitude if getattr(medicion, 'coordenadas', None) else None
        }
        datos_lista.append(datos_dict)
    
    df = pd.DataFrame(datos_lista)
    
    # Mostrar resumen del DataFrame
    print("Resumen del DataFrame:")
    print(f"  - Total de mediciones: {len(df)}")
    print(f"  - Parámetros disponibles: {', '.join(df['parametro_nombre'].unique())}")
    print(f"  - Localidades encontradas: {', '.join(df['localidad_buscada'].unique())}")
    print(f"  - Rango de fechas: {df['fecha_desde_utc'].min()} a {df['fecha_desde_utc'].max()}")
    
    return df

def guardar_datos_completos(df, prefijo_archivo="localidades_especificas"):
    """
    Guardar todos los datos en CSV con timestamp
    """
    if df is None or df.empty:
        print("⚠ No hay datos para guardar")
        return None
    
    # Crear directorio data si no existe
    if not os.path.exists('data'):
        os.makedirs('data')
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    nombre_archivo = f"data/{prefijo_archivo}_{timestamp}.csv"
    
    df.to_csv(nombre_archivo, index=False, encoding='utf-8')
    print(f"\n✓ Datos guardados en: {nombre_archivo}")
    print(f"  - Tamaño del archivo: {len(df)} mediciones")
    print(f"  - Columnas: {', '.join(df.columns)}")
    
    return nombre_archivo

def mostrar_estadisticas_detalladas(df):
    """
    Mostrar estadísticas detalladas de los datos obtenidos
    """
    if df is None or df.empty:
        return
    
    print("\n=== ESTADÍSTICAS DETALLADAS ===")
    
    # Estadísticas por localidad buscada
    print("\n📊 Mediciones por localidad buscada:")
    localidad_counts = df['localidad_buscada'].value_counts()
    for localidad, count in localidad_counts.items():
        print(f"  - {localidad}: {count} mediciones")
    
    # Estadísticas por parámetro
    print("\n📊 Mediciones por parámetro:")
    parametro_counts = df['parametro_nombre'].value_counts()
    for parametro, count in parametro_counts.items():
        print(f"  - {parametro}: {count} mediciones")
    
    # Estadísticas por ciudad
    if 'ciudad' in df.columns and df['ciudad'].notna().any():
        print("\n📊 Mediciones por ciudad:")
        ciudad_counts = df['ciudad'].value_counts()
        for ciudad, count in ciudad_counts.items():
            if pd.notna(ciudad):
                print(f"  - {ciudad}: {count} mediciones")
    
    # Fechas
    print(f"\n📅 Rango temporal:")
    print(f"  - Fecha más reciente: {df['fecha_desde_utc'].max()}")
    print(f"  - Fecha más antigua: {df['fecha_desde_utc'].min()}")
    
    # Estadísticas por sensor
    if 'sensor_id' in df.columns:
        print(f"\n📊 Sensores únicos: {df['sensor_id'].nunique()}")
    
    # Estadísticas por localidad
    if 'localidad_id' in df.columns:
        print(f"📊 Localidades únicas: {df['localidad_id'].nunique()}")

def main():
    """
    Función principal del extractor
    """
    # API Key de OpenAQ
    API_KEY = "e339b925427e28d956e41ab1c33b6f19816e32ef924a91de2243f327beba180a"
    
    # Localidades específicas a buscar
    LOCALIDADES_BUSCAR = ["Bocatoma", "ENAP Price", "JUNJI", "Indura"]
    
    print("=== EXTRACTOR DE DATOS DE CALIDAD DEL AIRE - LOCALIDADES ESPECÍFICAS DE CHILE ===\n")
    print(f"Localidades objetivo: {', '.join(LOCALIDADES_BUSCAR)}\n")
    
    try:
        # 1. Conectar a OpenAQ
        print("1. 🔌 Conectando a OpenAQ...")
        client = OpenAQ(api_key=API_KEY)
        print("✓ Conexión exitosa")
        
        # 2. Buscar las localidades específicas
        localidades_encontradas = buscar_localidades_especificas(client, LOCALIDADES_BUSCAR)
        
        if not localidades_encontradas:
            print("\n✗ No se encontraron localidades de las especificadas")
            return
        
        print(f"\n✓ Se encontraron {len(localidades_encontradas)} localidades")
        
        # 3. Obtener todos los sensores disponibles
        todos_sensores = obtener_sensores_completos(client, localidades_encontradas)
        
        if not todos_sensores:
            print("\n⚠ No se encontraron sensores")
            return
        
        print(f"\n✓ Se encontraron {len(todos_sensores)} sensores")
        
        # 4. Obtener la máxima cantidad de mediciones posible
        todas_mediciones = obtener_mediciones_maximas(client, todos_sensores)
        
        if not todas_mediciones:
            print("\n⚠ No se obtuvieron mediciones")
            return
        
        # 5. Convertir a DataFrame
        df = convertir_a_dataframe(todas_mediciones)
        
        if df is not None:
            # 6. Guardar datos
            archivo_guardado = guardar_datos_completos(df)
            
            # 7. Mostrar estadísticas detalladas
            mostrar_estadisticas_detalladas(df)
            
            # 8. Información adicional
            print(f"\n💾 Archivo guardado: {archivo_guardado}")
            print(f"📁 Tamaño del archivo: {os.path.getsize(archivo_guardado) / 1024:.2f} KB")
        
        # 9. Cerrar conexión
        print("\n9. 🔌 Cerrando conexión...")
        client.close()
        print("✓ Conexión cerrada")
        
    except Exception as e:
        print(f"✗ Error general: {e}")
        print("\nPosibles soluciones:")
        print("1. Verificar que la API key sea válida")
        print("2. Verificar la conexión a internet")
        print("3. Consultar la documentación oficial de OpenAQ")
    
    print("\n=== FIN DEL PROCESO ===")

if __name__ == "__main__":
    main()
