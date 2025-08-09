# -*- coding: utf-8 -*-
"""
EXTRACTOR MASIVO DE DATOS DE CHILE - OpenAQ API v3
==================================================
Extrae la máxima cantidad de datos posibles de todas las ciudades, 
comunas y zonas de Chile con el mayor rango temporal disponible.
"""

import urllib.request
import urllib.parse
import json
import ssl
import pandas as pd
from datetime import datetime, timedelta
import time
import os
from collections import defaultdict

# Configuración
API_KEY = "91eab8b4c15ab8e5eda9712fa803abe4bb45e5a6c8ee961d295de18b0b15722a"
BASE_URL = "https://api.openaq.org/v3"
DATOS_DIR = "../datos"

# Asegurar que existe el directorio de datos
if not os.path.exists(DATOS_DIR):
    os.makedirs(DATOS_DIR)

def hacer_peticion_robusta(endpoint, params=None, reintentos=3):
    """Hacer petición con reintentos y manejo robusto de errores"""
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    url = f"{BASE_URL}/{endpoint}"
    if params:
        url_params = urllib.parse.urlencode(params)
        url = f"{url}?{url_params}"
    
    headers = {
        'X-API-Key': API_KEY,
        'Content-Type': 'application/json',
        'User-Agent': 'ChileDataExtractor/1.0'
    }
    
    for intento in range(reintentos):
        try:
            req = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(req, context=ctx, timeout=60) as response:
                if response.getcode() == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    return data
                else:
                    print(f"   ⚠️ Status {response.getcode()} en intento {intento + 1}")
                    
        except Exception as e:
            print(f"   ⚠️ Error en intento {intento + 1}: {e}")
            if intento < reintentos - 1:
                time.sleep(2 ** intento)  # Backoff exponencial
    
    return None

def obtener_todas_ubicaciones_chile():
    """Obtener TODAS las ubicaciones disponibles en Chile"""
    
    print("🇨🇱 === OBTENIENDO TODAS LAS UBICACIONES DE CHILE ===")
    
    todas_ubicaciones = []
    offset = 0
    limit = 100
    
    while True:
        print(f"📡 Obteniendo ubicaciones: offset {offset}")
        
        params = {
            'countries_id': 3,  # Chile
            'limit': limit,
            'offset': offset
        }
        
        data = hacer_peticion_robusta('locations', params)
        
        if not data or not data.get('results'):
            break
        
        ubicaciones = data['results']
        todas_ubicaciones.extend(ubicaciones)
        
        print(f"   ✅ {len(ubicaciones)} ubicaciones obtenidas (total: {len(todas_ubicaciones)})")
        
        # Verificar si hay más páginas
        meta = data.get('meta', {})
        total_found = meta.get('found', 0)
        
        # Convertir a entero por seguridad
        try:
            total_found = int(total_found)
        except (ValueError, TypeError):
            total_found = 0
        
        if len(todas_ubicaciones) >= total_found or len(ubicaciones) < limit:
            break
        
        offset += limit
        time.sleep(0.5)  # Pausa para no sobrecargar la API
    
    print(f"\n📊 TOTAL UBICACIONES ENCONTRADAS: {len(todas_ubicaciones)}")
    
    return todas_ubicaciones

def analizar_ubicaciones(ubicaciones):
    """Analizar y categorizar todas las ubicaciones"""
    
    print("\n📋 === ANÁLISIS DE UBICACIONES ===")
    
    # Agrupar por diferentes criterios
    por_ciudad = defaultdict(list)
    por_region = defaultdict(list)
    por_proveedor = defaultdict(list)
    todos_parametros = set()
    total_sensores = 0
    
    for ubic in ubicaciones:
        # Por ciudad/localidad
        locality = ubic.get('locality', 'Sin clasificar')
        por_ciudad[locality].append(ubic)
        
        # Por proveedor
        proveedor = ubic.get('provider', {})
        proveedor_nombre = proveedor.get('name', 'Desconocido') if isinstance(proveedor, dict) else 'Desconocido'
        por_proveedor[proveedor_nombre].append(ubic)
        
        # Contar sensores y parámetros
        sensores = ubic.get('sensors', [])
        total_sensores += len(sensores)
        
        for sensor in sensores:
            parametro = sensor.get('parameter', {})
            if isinstance(parametro, dict):
                param_name = parametro.get('name')
                if param_name:
                    todos_parametros.add(param_name)
    
    # Mostrar estadísticas
    print(f"🏙️ CIUDADES/LOCALIDADES: {len(por_ciudad)}")
    ciudades_ordenadas = sorted(por_ciudad.items(), key=lambda x: len(x[1]), reverse=True)
    for i, (ciudad, ubicaciones_ciudad) in enumerate(ciudades_ordenadas[:15]):
        sensores_ciudad = sum(len(u.get('sensors', [])) for u in ubicaciones_ciudad)
        ciudad_nombre = ciudad or "Sin nombre"
        print(f"   {i+1:2d}. {ciudad_nombre[:25]:25} - {len(ubicaciones_ciudad):2d} ubicaciones, {sensores_ciudad:3d} sensores")
    
    if len(ciudades_ordenadas) > 15:
        print(f"   ... y {len(ciudades_ordenadas) - 15} ciudades más")
    
    print(f"\n🔬 PARÁMETROS DISPONIBLES: {len(todos_parametros)}")
    for i, param in enumerate(sorted(todos_parametros), 1):
        print(f"   {i:2d}. {param}")
    
    print(f"\n🏢 PROVEEDORES: {len(por_proveedor)}")
    for proveedor, ubicaciones_prov in sorted(por_proveedor.items()):
        proveedor_nombre = proveedor or "Desconocido"
        print(f"   • {proveedor_nombre}: {len(ubicaciones_prov)} ubicaciones")
    
    print(f"\n📊 RESUMEN TOTAL:")
    print(f"   • Ubicaciones: {len(ubicaciones)}")
    print(f"   • Sensores: {total_sensores}")
    print(f"   • Ciudades: {len(por_ciudad)}")
    print(f"   • Parámetros: {len(todos_parametros)}")
    
    return {
        'por_ciudad': dict(por_ciudad),
        'por_proveedor': dict(por_proveedor),
        'todos_parametros': todos_parametros,
        'ciudades_ordenadas': ciudades_ordenadas
    }

def obtener_datos_masivos_sensor(sensor_id, sensor_info, ubicacion_info, progreso):
    """Obtener datos de un sensor específico"""
    
    parametro = sensor_info.get('parameter', {})
    param_name = parametro.get('name', 'unknown') if isinstance(parametro, dict) else 'unknown'
    param_units = parametro.get('units', 'N/A') if isinstance(parametro, dict) else 'N/A'
    
    print(f"     📡 {progreso} Sensor {sensor_id} ({param_name}): ", end="")
    
    # Intentar obtener datos del sensor
    data = hacer_peticion_robusta(f'sensors/{sensor_id}')
    
    if not data:
        print("❌ Sin datos")
        return []
    
    registros = []
    
    # Procesar datos del sensor
    if isinstance(data, dict):
        # Información básica del sensor
        registro_base = {
            'fecha_extraccion': datetime.now().isoformat(),
            'sensor_id': sensor_id,
            'ubicacion_id': ubicacion_info.get('id'),
            'ubicacion_nombre': ubicacion_info.get('name', 'Sin nombre'),
            'ciudad': ubicacion_info.get('locality', 'Sin ciudad'),
            'parametro': param_name,
            'unidades': param_units,
            'latitud': ubicacion_info.get('coordinates', {}).get('latitude'),
            'longitud': ubicacion_info.get('coordinates', {}).get('longitude'),
            'proveedor': ubicacion_info.get('provider', {}).get('name', 'Desconocido'),
            'tipo_instrumento': ubicacion_info.get('instruments', [{}])[0].get('name', 'Desconocido') if ubicacion_info.get('instruments') else 'Desconocido',
            'es_movil': ubicacion_info.get('isMobile', False),
            'es_monitor': ubicacion_info.get('isMonitor', False),
            'fecha_primer_dato': ubicacion_info.get('datetimeFirst', {}).get('utc') if isinstance(ubicacion_info.get('datetimeFirst'), dict) else None,
            'fecha_ultimo_dato': ubicacion_info.get('datetimeLast', {}).get('utc') if isinstance(ubicacion_info.get('datetimeLast'), dict) else None,
            'timezone': ubicacion_info.get('timezone', 'N/A'),
        }
        
        # Si hay datos específicos del sensor
        if 'value' in data:
            registro_base.update({
                'valor': data.get('value'),
                'fecha_medicion': data.get('datetime', data.get('date')),
                'tipo_dato': 'sensor_info'
            })
        else:
            registro_base.update({
                'valor': 'N/A',
                'fecha_medicion': 'N/A',
                'tipo_dato': 'sensor_metadata'
            })
        
        registros.append(registro_base)
        print("✅ OK")
    else:
        print("⚠️ Formato inesperado")
    
    return registros

def extraer_datos_masivos():
    """Extracción masiva de datos de Chile"""
    
    print("🚀 === INICIANDO EXTRACCIÓN MASIVA DE DATOS DE CHILE ===")
    print(f"🕒 Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 1. Obtener todas las ubicaciones
    ubicaciones = obtener_todas_ubicaciones_chile()
    
    if not ubicaciones:
        print("❌ No se pudieron obtener ubicaciones")
        return False
    
    # 2. Analizar ubicaciones
    analisis = analizar_ubicaciones(ubicaciones)
    
    # 3. Extraer datos de todos los sensores
    print(f"\n⚡ === EXTRACCIÓN MASIVA DE SENSORES ===")
    
    todos_los_datos = []
    total_sensores = sum(len(ubic.get('sensors', [])) for ubic in ubicaciones)
    contador_sensores = 0
    
    print(f"📊 Total sensores a procesar: {total_sensores}")
    
    for i, ubicacion in enumerate(ubicaciones, 1):
        ubicacion_nombre = ubicacion.get('name', 'Sin nombre')
        ciudad = ubicacion.get('locality', 'Sin ciudad')
        sensores = ubicacion.get('sensors', [])
        
        if not sensores:
            continue
        
        print(f"\n🏭 [{i:3d}/{len(ubicaciones)}] {ubicacion_nombre} ({ciudad}) - {len(sensores)} sensores")
        
        # Procesar cada sensor de la ubicación
        for j, sensor in enumerate(sensores, 1):
            contador_sensores += 1
            sensor_id = sensor.get('id')
            
            if not sensor_id:
                continue
            
            progreso = f"[{contador_sensores:4d}/{total_sensores}]"
            
            datos_sensor = obtener_datos_masivos_sensor(
                sensor_id, sensor, ubicacion, progreso
            )
            
            todos_los_datos.extend(datos_sensor)
            
            # Pausa pequeña para no sobrecargar la API
            time.sleep(0.1)
        
        # Pausa más larga entre ubicaciones
        if i % 10 == 0:
            print(f"\n⏸️ Pausa de seguridad... ({len(todos_los_datos)} registros acumulados)")
            time.sleep(2)
    
    # 4. Procesar y guardar datos
    if todos_los_datos:
        print(f"\n💾 === GUARDANDO DATOS ===")
        
        # Crear DataFrame
        df = pd.DataFrame(todos_los_datos)
        
        # Guardar en múltiples formatos
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Excel completo
        excel_file = f"{DATOS_DIR}/chile_datos_completos_{timestamp}.xlsx"
        
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            # Hoja principal con todos los datos
            df.to_excel(writer, sheet_name='Todos_los_Datos', index=False)
            
            # Hoja resumen por ciudad
            if 'ciudad' in df.columns:
                resumen_ciudades = df.groupby('ciudad').agg({
                    'sensor_id': 'nunique',
                    'parametro': lambda x: ', '.join(x.unique()),
                    'ubicacion_nombre': 'nunique',
                    'proveedor': lambda x: ', '.join(x.unique())
                }).rename(columns={
                    'sensor_id': 'Sensores_Unicos',
                    'parametro': 'Parametros',
                    'ubicacion_nombre': 'Ubicaciones',
                    'proveedor': 'Proveedores'
                })
                resumen_ciudades.to_excel(writer, sheet_name='Resumen_Ciudades')
            
            # Hoja resumen por parámetro
            if 'parametro' in df.columns:
                resumen_parametros = df.groupby('parametro').agg({
                    'sensor_id': 'nunique',
                    'ciudad': 'nunique',
                    'ubicacion_nombre': 'nunique'
                }).rename(columns={
                    'sensor_id': 'Sensores',
                    'ciudad': 'Ciudades',
                    'ubicacion_nombre': 'Ubicaciones'
                })
                resumen_parametros.to_excel(writer, sheet_name='Resumen_Parametros')
        
        # CSV principal
        csv_file = f"{DATOS_DIR}/chile_datos_completos_{timestamp}.csv"
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        
        print(f"✅ Datos guardados:")
        print(f"   📊 Excel: {excel_file}")
        print(f"   📄 CSV: {csv_file}")
        
        # Estadísticas finales
        mostrar_estadisticas_finales(df, analisis)
        
        return True
    else:
        print("❌ No se obtuvieron datos")
        return False

def mostrar_estadisticas_finales(df, analisis):
    """Mostrar estadísticas finales de la extracción"""
    
    print(f"\n📈 === ESTADÍSTICAS FINALES ===")
    print(f"📊 Total registros extraídos: {len(df):,}")
    
    if not df.empty:
        print(f"🏙️ Ciudades únicas: {df['ciudad'].nunique()}")
        print(f"🔬 Sensores únicos: {df['sensor_id'].nunique()}")
        print(f"📍 Ubicaciones únicas: {df['ubicacion_nombre'].nunique()}")
        print(f"🧪 Parámetros únicos: {df['parametro'].nunique()}")
        print(f"🏢 Proveedores únicos: {df['proveedor'].nunique()}")
        
        # Top ciudades
        print(f"\n🏆 TOP 10 CIUDADES POR SENSORES:")
        top_ciudades = df.groupby('ciudad')['sensor_id'].nunique().sort_values(ascending=False).head(10)
        for i, (ciudad, sensores) in enumerate(top_ciudades.items(), 1):
            print(f"   {i:2d}. {ciudad:25} - {sensores:3d} sensores")
        
        # Parámetros más comunes
        print(f"\n🧪 PARÁMETROS MÁS MONITOREADOS:")
        top_parametros = df.groupby('parametro')['sensor_id'].nunique().sort_values(ascending=False)
        for i, (param, sensores) in enumerate(top_parametros.items(), 1):
            print(f"   {i:2d}. {param:15} - {sensores:3d} sensores")

def main():
    """Función principal"""
    
    inicio = datetime.now()
    exito = extraer_datos_masivos()
    fin = datetime.now()
    
    duracion = fin - inicio
    
    print("\n" + "=" * 60)
    if exito:
        print("🎉 EXTRACCIÓN MASIVA COMPLETADA EXITOSAMENTE")
    else:
        print("😞 LA EXTRACCIÓN NO PUDO COMPLETARSE")
    
    print(f"⏱️ Duración total: {duracion}")
    print(f"🕒 Finalizado: {fin.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

if __name__ == "__main__":
    main()
