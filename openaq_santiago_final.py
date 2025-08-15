#!/usr/bin/env python3
"""
Script final para obtener datos de calidad del aire de Santiago de Chile
Usa los sensores disponibles en las ubicaciones de Chile
"""

from openaq import OpenAQ
import pandas as pd
from datetime import datetime
import time

def get_locations_and_filter_chile(client, max_batches=20):
    """Obtener ubicaciones en lotes y filtrar las de Chile"""
    print("=== OBTENIENDO UBICACIONES DISPONIBLES ===\n")
    
    all_locations = []
    chile_locations = []
    santiago_locations = []
    
    try:
        # Obtener ubicaciones en lotes pequeños
        batch_size = 50
        
        for batch_num in range(max_batches):
            print(f"Obteniendo lote {batch_num + 1}/{max_batches}...")
            
            try:
                locations = client.locations.list(limit=batch_size)
                
                if not locations or not hasattr(locations, 'results') or len(locations.results) == 0:
                    print("  ⚠ No se obtuvieron más ubicaciones")
                    break
                
                batch_locations = locations.results
                all_locations.extend(batch_locations)
                
                # Filtrar ubicaciones de Chile
                for location in batch_locations:
                    if (hasattr(location, 'country') and location.country and 
                        hasattr(location.country, 'code') and location.country.code == 'CL'):
                        chile_locations.append(location)
                        
                        # Filtrar específicamente ubicaciones de Santiago
                        location_name = location.name.lower() if location.name else ""
                        city_name = ""
                        if hasattr(location, 'city') and location.city and location.city.name:
                            city_name = location.city.name.lower()
                        
                        if ("santiago" in location_name or "santiago" in city_name or 
                            "metropolitana" in city_name or "rm" in city_name or
                            "providencia" in city_name or "las condes" in city_name or
                            "ñuñoa" in city_name or "maipu" in city_name or
                            "puente alto" in city_name or "la florida" in city_name):
                            santiago_locations.append(location)
                
                print(f"  ✓ Procesadas {len(batch_locations)} ubicaciones")
                print(f"  ✓ Total acumulado: {len(all_locations)} ubicaciones")
                print(f"  ✓ Ubicaciones de Chile encontradas: {len(chile_locations)}")
                print(f"  ✓ Ubicaciones de Santiago encontradas: {len(santiago_locations)}")
                
                # Si ya encontramos suficientes ubicaciones de Chile, podemos parar
                if len(chile_locations) >= 20:
                    print("  ✓ Se encontraron suficientes ubicaciones de Chile, deteniendo búsqueda")
                    break
                
                # Pausa para no sobrecargar la API
                time.sleep(0.5)
                
            except Exception as e:
                print(f"  ✗ Error al obtener lote: {e}")
                break
        
        print(f"\n=== RESUMEN DE UBICACIONES ===")
        print(f"Total de ubicaciones procesadas: {len(all_locations)}")
        print(f"Ubicaciones de Chile: {len(chile_locations)}")
        print(f"Ubicaciones de Santiago: {len(santiago_locations)}")
        
        # Mostrar información de las ubicaciones de Chile
        if chile_locations:
            print(f"\n=== UBICACIONES DE CHILE ENCONTRADAS ===")
            for i, location in enumerate(chile_locations):
                print(f"\nUbicación {i+1}:")
                print(f"  ID: {location.id}")
                print(f"  Nombre: {location.name}")
                if hasattr(location, 'city') and location.city:
                    print(f"  Ciudad: {location.city.name}")
                if hasattr(location, 'country') and location.country:
                    print(f"  País: {location.country.name} ({location.country.code})")
                if hasattr(location, 'coordinates') and location.coordinates:
                    print(f"  Coordenadas: {location.coordinates.latitude}, {location.coordinates.longitude}")
                if hasattr(location, 'parameters') and location.parameters:
                    print(f"  Parámetros: {', '.join([p.name for p in location.parameters])}")
        
        return chile_locations, santiago_locations
        
    except Exception as e:
        print(f"✗ Error al obtener ubicaciones: {e}")
        return [], []

def get_sensors_from_locations(client, locations):
    """Obtener sensores disponibles en las ubicaciones"""
    print(f"\n=== OBTENIENDO SENSORES DE {len(locations)} UBICACIONES ===\n")
    
    all_sensors = []
    
    for i, location in enumerate(locations):
        print(f"Obteniendo sensores de ubicación {i+1}/{len(locations)}: {location.name}")
        
        try:
            # Obtener sensores de esta ubicación
            sensors = client.locations.sensors(location.id)
            
            if sensors and hasattr(sensors, 'results') and len(sensors.results) > 0:
                print(f"  ✓ Se encontraron {len(sensors.results)} sensores")
                
                for sensor in sensors.results:
                    sensor.location_id = location.id
                    sensor.location_name = location.name
                    # Verificar si location tiene atributo city antes de acceder
                    try:
                        sensor.city_name = location.city.name if hasattr(location, 'city') and location.city else None
                    except:
                        sensor.city_name = None
                    try:
                        sensor.country_code = location.country.code if hasattr(location, 'country') and location.country else None
                    except:
                        sensor.country_code = None
                    all_sensors.append(sensor)
                
                # Mostrar información de los primeros sensores
                for j, sensor in enumerate(sensors.results[:3]):
                    print(f"    Sensor {j+1}: ID {sensor.id}")
                    if hasattr(sensor, 'name') and sensor.name:
                        print(f"      Nombre: {sensor.name}")
                    if hasattr(sensor, 'parameter') and sensor.parameter:
                        print(f"      Parámetro: {sensor.parameter.name}")
                
                if len(sensors.results) > 3:
                    print(f"    ... y {len(sensors.results) - 3} sensores más")
            else:
                print(f"  ⚠ No se encontraron sensores")
            
            # Pausa breve para no sobrecargar la API
            time.sleep(0.5)
            
        except Exception as e:
            print(f"  ✗ Error al obtener sensores: {e}")
    
    print(f"\n✓ Total de sensores encontrados: {len(all_sensors)}")
    return all_sensors

def get_measurements_from_sensors(client, sensors, limit_per_sensor=1000):
    """Obtener mediciones de los sensores especificados"""
    print(f"\n=== OBTENIENDO MEDICIONES DE {len(sensors)} SENSORES ===\n")
    
    all_measurements = []
    
    for i, sensor in enumerate(sensors):
        print(f"Obteniendo mediciones del sensor {i+1}/{len(sensors)}: ID {sensor.id}")
        
        try:
            # Obtener mediciones de este sensor
            measurements = client.measurements.list(sensors_id=sensor.id, limit=limit_per_sensor)
            
            if measurements and hasattr(measurements, 'results') and len(measurements.results) > 0:
                print(f"  ✓ Se encontraron {len(measurements.results)} mediciones")
                
                # Agregar información de ubicación a cada medición
                for measurement in measurements.results:
                    measurement.location_id = sensor.location_id
                    measurement.location_name = sensor.location_name
                    measurement.city_name = sensor.city_name
                    measurement.country_code = sensor.country_code
                
                all_measurements.extend(measurements.results)
                
                # Mostrar información de las primeras mediciones
                for j, measurement in enumerate(measurements.results[:3]):
                    print(f"    Medición {j+1}: {measurement.parameter.name} = {measurement.value} {measurement.parameter.units}")
                    print(f"      Fecha: {measurement.period.datetime_from.utc}")
                
                if len(measurements.results) > 3:
                    print(f"    ... y {len(measurements.results) - 3} mediciones más")
            else:
                print(f"  ⚠ No se encontraron mediciones")
            
            # Pausa breve para no sobrecargar la API
            time.sleep(1)
            
        except Exception as e:
            print(f"  ✗ Error al obtener mediciones: {e}")
    
    print(f"\n✓ Total de mediciones obtenidas: {len(all_measurements)}")
    return all_measurements

def convert_measurements_to_dataframe(measurements):
    """Convertir mediciones a DataFrame de pandas"""
    if not measurements:
        return None
    
    print("\n=== CONVIRTIENDO DATOS A DATAFRAME ===\n")
    
    data_list = []
    for measurement in measurements:
        data_dict = {
            'parameter_name': measurement.parameter.name,
            'parameter_id': measurement.parameter.id,
            'value': measurement.value,
            'unit': measurement.parameter.units,
            'date_from_utc': measurement.period.datetime_from.utc,
            'date_from_local': measurement.period.datetime_from.local,
            'date_to_utc': measurement.period.datetime_to.utc,
            'date_to_local': measurement.period.datetime_to.local,
            'coverage_percent': measurement.coverage.percent_complete if measurement.coverage else None,
            'sensor_id': measurement.sensor.id if hasattr(measurement, 'sensor') and measurement.sensor else None,
            'location_id': getattr(measurement, 'location_id', None),
            'location_name': getattr(measurement, 'location_name', None),
            'city_name': getattr(measurement, 'city_name', None),
            'country_code': getattr(measurement, 'country_code', None)
        }
        data_list.append(data_dict)
    
    df = pd.DataFrame(data_list)
    
    # Mostrar resumen del DataFrame
    print("Resumen del DataFrame:")
    print(f"  - Total de mediciones: {len(df)}")
    print(f"  - Parámetros disponibles: {', '.join(df['parameter_name'].unique())}")
    print(f"  - Ubicaciones: {', '.join(df['location_name'].unique()) if 'location_name' in df.columns else 'N/A'}")
    print(f"  - Rango de fechas: {df['date_from_utc'].min()} a {df['date_from_utc'].max()}")
    
    return df

def save_santiago_data(df, filename_prefix="santiago_openaq"):
    """Guardar datos de Santiago en CSV"""
    if df is None or df.empty:
        print("⚠ No hay datos para guardar")
        return
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{filename_prefix}_{timestamp}.csv"
    
    df.to_csv(filename, index=False, encoding='utf-8')
    print(f"\n✓ Datos de Santiago guardados en: {filename}")
    print(f"  - Tamaño del archivo: {len(df)} mediciones")
    print(f"  - Columnas: {', '.join(df.columns)}")
    
    return filename

def main():
    """Función principal"""
    
    # Tu API key
    API_KEY = "e339b925427e28d956e41ab1c33b6f19816e32ef924a91de2243f327beba180a"
    
    print("=== COLECTOR FINAL DE DATOS DE CALIDAD DEL AIRE - SANTIAGO DE CHILE ===\n")
    
    try:
        # Crear cliente de OpenAQ
        print("1. Conectando a OpenAQ...")
        client = OpenAQ(api_key=API_KEY)
        print("✓ Conexión exitosa")
        
        # 2. Obtener ubicaciones y filtrar las de Chile/Santiago
        chile_locations, santiago_locations = get_locations_and_filter_chile(client)
        
        # 3. Decidir qué ubicaciones usar
        target_locations = santiago_locations if santiago_locations else chile_locations
        
        if not target_locations:
            print("\n✗ No se encontraron ubicaciones en Chile")
            return
        
        print(f"\n✓ Usando {len(target_locations)} ubicaciones para obtener sensores")
        
        # 4. Obtener sensores de las ubicaciones
        all_sensors = get_sensors_from_locations(client, target_locations)
        
        if not all_sensors:
            print("\n⚠ No se encontraron sensores")
            return
        
        print(f"\n✓ Se encontraron {len(all_sensors)} sensores")
        
        # 5. Obtener todas las mediciones disponibles de los sensores
        all_measurements = get_measurements_from_sensors(client, all_sensors)
        
        if not all_measurements:
            print("\n⚠ No se obtuvieron mediciones")
            return
        
        # 6. Convertir a DataFrame
        df = convert_measurements_to_dataframe(all_measurements)
        
        if df is not None:
            # 7. Guardar en CSV
            save_santiago_data(df)
            
            # 8. Mostrar estadísticas adicionales
            print("\n=== ESTADÍSTICAS ADICIONALES ===")
            
            # Estadísticas por parámetro
            print("\nMediciones por parámetro:")
            param_counts = df['parameter_name'].value_counts()
            for param, count in param_counts.items():
                print(f"  - {param}: {count} mediciones")
            
            # Estadísticas por ubicación
            if 'location_name' in df.columns:
                print("\nMediciones por ubicación:")
                location_counts = df['location_name'].value_counts()
                for location, count in location_counts.items():
                    print(f"  - {location}: {count} mediciones")
            
            # Fechas más recientes
            print(f"\nFecha más reciente: {df['date_from_utc'].max()}")
            print(f"Fecha más antigua: {df['date_from_utc'].min()}")
            
            # Estadísticas por país
            if 'country_code' in df.columns:
                print(f"\nMediciones por país:")
                country_counts = df['country_code'].value_counts()
                for country, count in country_counts.items():
                    print(f"  - {country}: {count} mediciones")
        
        # 9. Cerrar conexión
        print("\n9. Cerrando conexión...")
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
