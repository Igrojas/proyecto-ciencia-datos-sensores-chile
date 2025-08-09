# -*- coding: utf-8 -*-
"""
EXTRACTOR DE UBICACIONES CON 6 SENSORES - CHILE
=============================================
Extrae datos únicamente de las ubicaciones que tienen exactamente 6 sensores
(máximo disponible) para obtener el conjunto de datos más completo.
"""

import urllib.request
import urllib.parse
import json
import ssl
import pandas as pd
from datetime import datetime, timedelta
import time
import os

# Configuración
API_KEY = "91eab8b4c15ab8e5eda9712fa803abe4bb45e5a6c8ee961d295de18b0b15722a"
BASE_URL = "https://api.openaq.org/v3"
DATOS_DIR = "../datos"

# Asegurar que existe el directorio de datos
if not os.path.exists(DATOS_DIR):
    os.makedirs(DATOS_DIR)

def hacer_peticion_segura(endpoint, params=None, pausa=1):
    """Hacer petición con pausa automática para evitar límites"""
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    url = f"{BASE_URL}/{endpoint}"
    if params:
        url_params = urllib.parse.urlencode(params)
        url = f"{url}?{url_params}"
    
    headers = {
        'X-API-Key': API_KEY,
        'Content-Type': 'application/json'
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
            if response.getcode() == 200:
                data = json.loads(response.read().decode('utf-8'))
                time.sleep(pausa)  # Pausa automática
                return data
            else:
                print(f"❌ Status {response.getcode()}")
                return None
                
    except Exception as e:
        print(f"⚠️ Error: {e}")
        return None

def identificar_ubicaciones_6_sensores():
    """Identificar todas las ubicaciones que tienen exactamente 6 sensores"""
    
    print("🔍 === IDENTIFICANDO UBICACIONES CON 6 SENSORES ===")
    
    # Obtener todas las ubicaciones de Chile en lotes
    todas_ubicaciones = []
    limit = 100
    
    for offset in range(0, 500, limit):  # Máximo 500 ubicaciones
        print(f"📡 Obteniendo ubicaciones: offset {offset}")
        
        params = {
            'countries_id': 3,  # Chile
            'limit': limit,
            'offset': offset
        }
        
        data = hacer_peticion_segura('locations', params, pausa=2)
        
        if not data or not data.get('results'):
            break
        
        ubicaciones = data['results']
        todas_ubicaciones.extend(ubicaciones)
        
        print(f"   ✅ {len(ubicaciones)} ubicaciones obtenidas (total: {len(todas_ubicaciones)})")
        
        if len(ubicaciones) < limit:
            break
    
    print(f"\n📊 Total ubicaciones analizadas: {len(todas_ubicaciones)}")
    
    # Filtrar ubicaciones con exactamente 6 sensores
    ubicaciones_6_sensores = []
    
    for ubicacion in todas_ubicaciones:
        sensores = ubicacion.get('sensors', [])
        if len(sensores) == 6:
            ubicaciones_6_sensores.append(ubicacion)
    
    print(f"🎯 Ubicaciones con 6 sensores: {len(ubicaciones_6_sensores)}")
    
    # Mostrar detalles de las ubicaciones encontradas
    print(f"\n📋 UBICACIONES CON 6 SENSORES COMPLETOS:")
    for i, ubicacion in enumerate(ubicaciones_6_sensores, 1):
        nombre = ubicacion.get('name', 'Sin nombre') or 'Sin nombre'
        ciudad = ubicacion.get('locality', 'Sin ciudad') or 'Sin ciudad'
        sensores = ubicacion.get('sensors', [])
        parametros = [s.get('parameter', {}).get('name', 'N/A') for s in sensores]
        
        print(f"   {i:2d}. {nombre:30} ({ciudad:15}) - {', '.join(parametros)}")
    
    return ubicaciones_6_sensores

def extraer_datos_sensores_completos(ubicaciones_6_sensores):
    """Extraer datos de todas las ubicaciones con 6 sensores"""
    
    print(f"\n⚡ === EXTRAYENDO DATOS DE {len(ubicaciones_6_sensores)} UBICACIONES PREMIUM ===")
    
    todos_los_datos = []
    datos_ubicaciones = []
    contador = 0
    
    for i, ubicacion in enumerate(ubicaciones_6_sensores, 1):
        ubicacion_id = ubicacion.get('id')
        ubicacion_nombre = ubicacion.get('name', 'Sin nombre') or 'Sin nombre'
        ciudad = ubicacion.get('locality', 'Sin ciudad') or 'Sin ciudad'
        sensores = ubicacion.get('sensors', [])
        
        print(f"\n🏭 [{i:2d}/{len(ubicaciones_6_sensores)}] {ubicacion_nombre} ({ciudad})")
        
        # Información detallada de la ubicación
        info_ubicacion = {
            'timestamp_extraccion': datetime.now().isoformat(),
            'ubicacion_id': ubicacion_id,
            'ubicacion_nombre': ubicacion_nombre,
            'ciudad': ciudad,
            'latitud': ubicacion.get('coordinates', {}).get('latitude'),
            'longitud': ubicacion.get('coordinates', {}).get('longitude'),
            'proveedor': ubicacion.get('provider', {}).get('name', 'Desconocido'),
            'owner': ubicacion.get('owner', {}).get('name', 'Desconocido'),
            'tipo_instrumento': ubicacion.get('instruments', [{}])[0].get('name', 'Desconocido') if ubicacion.get('instruments') else 'Desconocido',
            'es_movil': ubicacion.get('isMobile', False),
            'es_monitor': ubicacion.get('isMonitor', False),
            'fecha_primer_dato': ubicacion.get('datetimeFirst', {}).get('utc') if isinstance(ubicacion.get('datetimeFirst'), dict) else None,
            'fecha_ultimo_dato': ubicacion.get('datetimeLast', {}).get('utc') if isinstance(ubicacion.get('datetimeLast'), dict) else None,
            'timezone': ubicacion.get('timezone', 'N/A'),
            'total_sensores': len(sensores),
            'parametros_disponibles': ', '.join([s.get('parameter', {}).get('name', 'N/A') for s in sensores])
        }
        datos_ubicaciones.append(info_ubicacion)
        
        # Procesar cada uno de los 6 sensores
        for j, sensor in enumerate(sensores, 1):
            sensor_id = sensor.get('id')
            parametro = sensor.get('parameter', {})
            param_name = parametro.get('name', 'unknown') if isinstance(parametro, dict) else 'unknown'
            param_units = parametro.get('units', 'N/A') if isinstance(parametro, dict) else 'N/A'
            param_display = parametro.get('displayName', param_name) if isinstance(parametro, dict) else param_name
            
            print(f"     🔬 [{j}/6] {param_name} ({param_units}): ", end="")
            
            # Intentar obtener datos del sensor
            sensor_data = hacer_peticion_segura(f'sensors/{sensor_id}', pausa=0.8)
            
            # Crear registro del sensor
            registro_sensor = {
                'timestamp_extraccion': datetime.now().isoformat(),
                'ubicacion_id': ubicacion_id,
                'ubicacion_nombre': ubicacion_nombre,
                'ciudad': ciudad,
                'sensor_id': sensor_id,
                'parametro': param_name,
                'parametro_display': param_display,
                'unidades': param_units,
                'latitud': info_ubicacion['latitud'],
                'longitud': info_ubicacion['longitud'],
                'proveedor': info_ubicacion['proveedor'],
                'owner': info_ubicacion['owner'],
                'tipo_instrumento': info_ubicacion['tipo_instrumento'],
                'timezone': info_ubicacion['timezone'],
                'fecha_primer_dato': info_ubicacion['fecha_primer_dato'],
                'fecha_ultimo_dato': info_ubicacion['fecha_ultimo_dato'],
                'sensor_activo': True
            }
            
            # Agregar datos específicos del sensor si están disponibles
            if sensor_data:
                if isinstance(sensor_data, dict):
                    registro_sensor.update({
                        'valor_actual': sensor_data.get('value', 'N/A'),
                        'fecha_medicion': sensor_data.get('datetime', sensor_data.get('date', 'N/A')),
                        'datos_disponibles': True
                    })
                    print("✅ Con datos")
                else:
                    registro_sensor.update({
                        'valor_actual': 'N/A',
                        'fecha_medicion': 'N/A',
                        'datos_disponibles': True
                    })
                    print("✅ Metadata")
            else:
                registro_sensor.update({
                    'valor_actual': 'N/A',
                    'fecha_medicion': 'N/A',
                    'datos_disponibles': False
                })
                print("❌ Sin datos")
            
            todos_los_datos.append(registro_sensor)
            contador += 1
        
        print(f"     📊 Total procesado: {contador} sensores")
        
        # Pausa entre ubicaciones
        if i % 5 == 0:
            print(f"   ⏸️ Pausa de seguridad... ({contador} sensores procesados)")
            time.sleep(5)
        else:
            time.sleep(2)
    
    return todos_los_datos, datos_ubicaciones

def guardar_datos_6_sensores(datos_sensores, datos_ubicaciones):
    """Guardar datos en formato Excel optimizado"""
    
    if not datos_sensores:
        print("❌ No hay datos para guardar")
        return False
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Crear DataFrames
    df_sensores = pd.DataFrame(datos_sensores)
    df_ubicaciones = pd.DataFrame(datos_ubicaciones)
    
    # Archivo Excel principal
    excel_file = f"{DATOS_DIR}/chile_6_sensores_completo_{timestamp}.xlsx"
    
    print(f"\n💾 === GUARDANDO DATOS EN EXCEL ===")
    
    with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
        # Hoja 1: Todos los sensores
        df_sensores.to_excel(writer, sheet_name='Sensores_Completos', index=False)
        
        # Hoja 2: Ubicaciones premium
        df_ubicaciones.to_excel(writer, sheet_name='Ubicaciones_Premium', index=False)
        
        # Hoja 3: Matriz de parámetros por ciudad
        if not df_sensores.empty:
            matriz_ciudad_param = df_sensores.pivot_table(
                values='sensor_id',
                index='ciudad',
                columns='parametro',
                aggfunc='count',
                fill_value=0
            )
            matriz_ciudad_param.to_excel(writer, sheet_name='Matriz_Ciudad_Parametro')
        
        # Hoja 4: Resumen ejecutivo
        if not df_sensores.empty and not df_ubicaciones.empty:
            resumen = {
                'Metrica': [
                    'Total Ubicaciones',
                    'Total Sensores',
                    'Ciudades Únicas',
                    'Parámetros Únicos',
                    'Proveedores Únicos',
                    'Sensores con Datos',
                    'Cobertura Geográfica (Lat Min)',
                    'Cobertura Geográfica (Lat Max)',
                    'Cobertura Geográfica (Lon Min)',
                    'Cobertura Geográfica (Lon Max)'
                ],
                'Valor': [
                    len(df_ubicaciones),
                    len(df_sensores),
                    df_sensores['ciudad'].nunique(),
                    df_sensores['parametro'].nunique(),
                    df_sensores['proveedor'].nunique(),
                    df_sensores['datos_disponibles'].sum(),
                    df_sensores['latitud'].min(),
                    df_sensores['latitud'].max(),
                    df_sensores['longitud'].min(),
                    df_sensores['longitud'].max()
                ]
            }
            pd.DataFrame(resumen).to_excel(writer, sheet_name='Resumen_Ejecutivo', index=False)
    
    # Archivos CSV adicionales
    csv_sensores = f"{DATOS_DIR}/chile_sensores_6_{timestamp}.csv"
    csv_ubicaciones = f"{DATOS_DIR}/chile_ubicaciones_6_{timestamp}.csv"
    
    df_sensores.to_csv(csv_sensores, index=False, encoding='utf-8-sig')
    df_ubicaciones.to_csv(csv_ubicaciones, index=False, encoding='utf-8-sig')
    
    print(f"✅ ARCHIVOS GENERADOS:")
    print(f"   📊 Excel completo: {excel_file}")
    print(f"   📄 CSV Sensores: {csv_sensores}")
    print(f"   📄 CSV Ubicaciones: {csv_ubicaciones}")
    
    # Mostrar estadísticas finales
    mostrar_estadisticas_finales(df_sensores, df_ubicaciones)
    
    return True

def mostrar_estadisticas_finales(df_sensores, df_ubicaciones):
    """Mostrar estadísticas detalladas"""
    
    print(f"\n📈 === ESTADÍSTICAS FINALES - UBICACIONES PREMIUM ===")
    print(f"🏭 Ubicaciones con 6 sensores: {len(df_ubicaciones):,}")
    print(f"🔬 Total sensores procesados: {len(df_sensores):,}")
    print(f"📡 Sensores con datos: {df_sensores['datos_disponibles'].sum():,}")
    print(f"📊 Porcentaje éxito: {(df_sensores['datos_disponibles'].sum() / len(df_sensores) * 100):.1f}%")
    
    print(f"\n🏙️ DISTRIBUCIÓN POR CIUDAD:")
    ciudades_stats = df_sensores.groupby('ciudad').agg({
        'sensor_id': 'nunique',
        'datos_disponibles': 'sum',
        'ubicacion_nombre': 'nunique'
    }).sort_values('sensor_id', ascending=False)
    
    for i, (ciudad, stats) in enumerate(ciudades_stats.iterrows(), 1):
        ciudad_nombre = ciudad or "Sin clasificar"
        print(f"   {i:2d}. {ciudad_nombre[:25]:25} - {stats['ubicacion_nombre']} ubicaciones, {stats['sensor_id']} sensores, {stats['datos_disponibles']} con datos")
    
    print(f"\n🧪 PARÁMETROS MONITOREADOS:")
    parametros_stats = df_sensores.groupby('parametro').agg({
        'sensor_id': 'nunique',
        'datos_disponibles': 'sum',
        'ciudad': 'nunique'
    }).sort_values('sensor_id', ascending=False)
    
    for i, (param, stats) in enumerate(parametros_stats.iterrows(), 1):
        print(f"   {i}. {param:10} - {stats['sensor_id']} sensores, {stats['datos_disponibles']} con datos, {stats['ciudad']} ciudades")
    
    # Cobertura temporal
    if not df_ubicaciones.empty:
        fechas_primer_dato = pd.to_datetime(df_ubicaciones['fecha_primer_dato'], errors='coerce')
        fechas_ultimo_dato = pd.to_datetime(df_ubicaciones['fecha_ultimo_dato'], errors='coerce')
        
        print(f"\n📅 COBERTURA TEMPORAL:")
        print(f"   Primer dato histórico: {fechas_primer_dato.min()}")
        print(f"   Último dato disponible: {fechas_ultimo_dato.max()}")
        print(f"   Rango temporal: {(fechas_ultimo_dato.max() - fechas_primer_dato.min()).days} días")

def main():
    """Función principal"""
    
    inicio = datetime.now()
    print("🎯 EXTRACTOR DE UBICACIONES CON 6 SENSORES - CHILE")
    print("=" * 55)
    print("🔍 Objetivo: Extraer datos de ubicaciones con máxima cobertura (6 sensores)")
    print("📊 Esto garantiza el conjunto de datos más completo disponible")
    print("=" * 55)
    
    # Paso 1: Identificar ubicaciones con 6 sensores
    ubicaciones_premium = identificar_ubicaciones_6_sensores()
    
    if not ubicaciones_premium:
        print("❌ No se encontraron ubicaciones con 6 sensores")
        return
    
    # Paso 2: Extraer datos de estas ubicaciones
    datos_sensores, datos_ubicaciones = extraer_datos_sensores_completos(ubicaciones_premium)
    
    # Paso 3: Guardar datos
    exito = guardar_datos_6_sensores(datos_sensores, datos_ubicaciones)
    
    fin = datetime.now()
    duracion = fin - inicio
    
    print("\n" + "=" * 55)
    if exito:
        print("🎉 EXTRACCIÓN DE UBICACIONES PREMIUM COMPLETADA")
        print("📊 Datos de máxima calidad guardados en Excel y CSV")
        print("🏆 Solo ubicaciones con 6 sensores (cobertura completa)")
    else:
        print("😞 LA EXTRACCIÓN NO PUDO COMPLETARSE")
    
    print(f"⏱️ Duración: {duracion}")
    print(f"🕒 Finalizado: {fin.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 55)

if __name__ == "__main__":
    main()
