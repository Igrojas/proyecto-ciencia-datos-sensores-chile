# -*- coding: utf-8 -*-
"""
EXTRACTOR OPTIMIZADO DE DATOS DE CHILE - Con manejo de límites y guardado incremental
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

def hacer_peticion_con_limites(endpoint, params=None):
    """Hacer petición con manejo inteligente de límites de tasa"""
    
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
    
    max_intentos = 3
    
    for intento in range(max_intentos):
        try:
            req = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
                if response.getcode() == 200:
                    return json.loads(response.read().decode('utf-8'))
                elif response.getcode() == 429:  # Too Many Requests
                    wait_time = (2 ** intento) * 5  # Backoff exponencial más agresivo
                    print(f"⏳ Límite alcanzado, esperando {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"❌ Status {response.getcode()}")
                    return None
                    
        except Exception as e:
            if "429" in str(e):
                wait_time = (2 ** intento) * 5
                print(f"⏳ Límite detectado, esperando {wait_time}s...")
                time.sleep(wait_time)
                continue
            else:
                print(f"⚠️ Error: {e}")
                return None
    
    return None

def extraer_datos_chile_inteligente():
    """Extracción inteligente con guardado incremental"""
    
    print("🇨🇱 === EXTRACTOR INTELIGENTE DE CHILE ===")
    print(f"🕒 Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. Obtener ubicaciones principales (las primeras 50)
    print("\n📍 Obteniendo ubicaciones principales...")
    
    ubicaciones_data = hacer_peticion_con_limites('locations', {
        'countries_id': 3,
        'limit': 50
    })
    
    if not ubicaciones_data or not ubicaciones_data.get('results'):
        print("❌ No se pudieron obtener ubicaciones")
        return False
    
    ubicaciones = ubicaciones_data['results']
    print(f"✅ {len(ubicaciones)} ubicaciones obtenidas")
    
    # 2. Procesar ubicaciones por lotes
    todos_los_datos = []
    datos_ubicaciones = []
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    print(f"\n⚡ Procesando {len(ubicaciones)} ubicaciones...")
    
    for i, ubicacion in enumerate(ubicaciones, 1):
        ubicacion_nombre = ubicacion.get('name', 'Sin nombre')
        ciudad = ubicacion.get('locality', 'Sin ciudad')
        sensores = ubicacion.get('sensors', [])
        
        print(f"\n🏭 [{i:2d}/{len(ubicaciones)}] {ubicacion_nombre} ({ciudad}) - {len(sensores)} sensores")
        
        # Información de la ubicación
        info_ubicacion = {
            'timestamp_extraccion': datetime.now().isoformat(),
            'ubicacion_id': ubicacion.get('id'),
            'ubicacion_nombre': ubicacion_nombre,
            'ciudad': ciudad,
            'latitud': ubicacion.get('coordinates', {}).get('latitude'),
            'longitud': ubicacion.get('coordinates', {}).get('longitude'),
            'proveedor': ubicacion.get('provider', {}).get('name', 'Desconocido'),
            'tipo_instrumento': ubicacion.get('instruments', [{}])[0].get('name', 'Desconocido') if ubicacion.get('instruments') else 'Desconocido',
            'es_movil': ubicacion.get('isMobile', False),
            'es_monitor': ubicacion.get('isMonitor', False),
            'fecha_primer_dato': ubicacion.get('datetimeFirst', {}).get('utc') if isinstance(ubicacion.get('datetimeFirst'), dict) else None,
            'fecha_ultimo_dato': ubicacion.get('datetimeLast', {}).get('utc') if isinstance(ubicacion.get('datetimeLast'), dict) else None,
            'timezone': ubicacion.get('timezone', 'N/A'),
            'total_sensores': len(sensores)
        }
        datos_ubicaciones.append(info_ubicacion)
        
        # Procesar sensores de manera más eficiente
        sensores_procesados = 0
        for j, sensor in enumerate(sensores[:6], 1):  # Máximo 6 sensores por ubicación
            sensor_id = sensor.get('id')
            parametro = sensor.get('parameter', {})
            param_name = parametro.get('name', 'unknown') if isinstance(parametro, dict) else 'unknown'
            param_units = parametro.get('units', 'N/A') if isinstance(parametro, dict) else 'N/A'
            
            print(f"     🔬 [{j}/{min(len(sensores), 6)}] {param_name}: ", end="")
            
            # Crear registro básico del sensor
            registro_sensor = {
                'timestamp_extraccion': datetime.now().isoformat(),
                'ubicacion_id': ubicacion.get('id'),
                'ubicacion_nombre': ubicacion_nombre,
                'ciudad': ciudad,
                'sensor_id': sensor_id,
                'parametro': param_name,
                'unidades': param_units,
                'latitud': info_ubicacion['latitud'],
                'longitud': info_ubicacion['longitud'],
                'proveedor': info_ubicacion['proveedor'],
                'tipo_instrumento': info_ubicacion['tipo_instrumento'],
                'timezone': info_ubicacion['timezone'],
                'sensor_activo': True  # Asumimos que está activo si aparece en la lista
            }
            
            todos_los_datos.append(registro_sensor)
            sensores_procesados += 1
            print("✅")
            
            # Pausa pequeña entre sensores
            time.sleep(0.5)
        
        print(f"     📊 {sensores_procesados} sensores procesados")
        
        # Guardado incremental cada 10 ubicaciones
        if i % 10 == 0:
            print(f"\n💾 Guardado incremental... ({len(todos_los_datos)} registros)")
            guardar_datos_parciales(todos_los_datos, datos_ubicaciones, timestamp, i)
        
        # Pausa entre ubicaciones para respetar límites
        time.sleep(2)
    
    # Guardado final
    print(f"\n💾 === GUARDADO FINAL ===")
    return guardar_datos_completos(todos_los_datos, datos_ubicaciones, timestamp)

def guardar_datos_parciales(datos_sensores, datos_ubicaciones, timestamp, batch_num):
    """Guardar datos parciales como backup"""
    
    if datos_sensores:
        df_sensores = pd.DataFrame(datos_sensores)
        csv_parcial = f"{DATOS_DIR}/chile_sensores_parcial_{timestamp}_batch{batch_num}.csv"
        df_sensores.to_csv(csv_parcial, index=False, encoding='utf-8-sig')
        print(f"   💾 Backup: {csv_parcial}")

def guardar_datos_completos(datos_sensores, datos_ubicaciones, timestamp):
    """Guardar datos completos en múltiples formatos"""
    
    if not datos_sensores:
        print("❌ No hay datos para guardar")
        return False
    
    # Crear DataFrames
    df_sensores = pd.DataFrame(datos_sensores)
    df_ubicaciones = pd.DataFrame(datos_ubicaciones)
    
    # Archivo Excel principal con múltiples hojas
    excel_file = f"{DATOS_DIR}/chile_datos_completos_{timestamp}.xlsx"
    
    with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
        # Hoja 1: Datos de sensores
        df_sensores.to_excel(writer, sheet_name='Sensores', index=False)
        
        # Hoja 2: Datos de ubicaciones
        df_ubicaciones.to_excel(writer, sheet_name='Ubicaciones', index=False)
        
        # Hoja 3: Resumen por ciudad
        if not df_sensores.empty:
            resumen_ciudades = df_sensores.groupby('ciudad').agg({
                'sensor_id': 'nunique',
                'parametro': lambda x: ', '.join(sorted(x.unique())),
                'ubicacion_nombre': 'nunique'
            }).rename(columns={
                'sensor_id': 'Total_Sensores',
                'parametro': 'Parametros_Monitoreados',
                'ubicacion_nombre': 'Ubicaciones'
            })
            resumen_ciudades.to_excel(writer, sheet_name='Resumen_Ciudades')
        
        # Hoja 4: Resumen por parámetro
        if not df_sensores.empty:
            resumen_parametros = df_sensores.groupby('parametro').agg({
                'sensor_id': 'nunique',
                'ciudad': 'nunique',
                'ubicacion_nombre': 'nunique'
            }).rename(columns={
                'sensor_id': 'Total_Sensores',
                'ciudad': 'Ciudades',
                'ubicacion_nombre': 'Ubicaciones'
            })
            resumen_parametros.to_excel(writer, sheet_name='Resumen_Parametros')
    
    # Archivos CSV separados
    csv_sensores = f"{DATOS_DIR}/chile_sensores_{timestamp}.csv"
    csv_ubicaciones = f"{DATOS_DIR}/chile_ubicaciones_{timestamp}.csv"
    
    df_sensores.to_csv(csv_sensores, index=False, encoding='utf-8-sig')
    df_ubicaciones.to_csv(csv_ubicaciones, index=False, encoding='utf-8-sig')
    
    print(f"✅ Datos guardados:")
    print(f"   📊 Excel completo: {excel_file}")
    print(f"   📄 CSV Sensores: {csv_sensores}")
    print(f"   📄 CSV Ubicaciones: {csv_ubicaciones}")
    
    # Mostrar estadísticas
    mostrar_estadisticas(df_sensores, df_ubicaciones)
    
    return True

def mostrar_estadisticas(df_sensores, df_ubicaciones):
    """Mostrar estadísticas finales"""
    
    print(f"\n📈 === ESTADÍSTICAS FINALES ===")
    print(f"📊 Total sensores registrados: {len(df_sensores):,}")
    print(f"🏭 Total ubicaciones: {len(df_ubicaciones):,}")
    
    if not df_sensores.empty:
        print(f"🏙️ Ciudades únicas: {df_sensores['ciudad'].nunique()}")
        print(f"🧪 Parámetros únicos: {df_sensores['parametro'].nunique()}")
        print(f"🏢 Proveedores únicos: {df_sensores['proveedor'].nunique()}")
        
        # Top ciudades
        print(f"\n🏆 TOP 10 CIUDADES:")
        top_ciudades = df_sensores.groupby('ciudad')['sensor_id'].nunique().sort_values(ascending=False).head(10)
        for i, (ciudad, sensores) in enumerate(top_ciudades.items(), 1):
            ciudad_nombre = ciudad or "Sin clasificar"
            print(f"   {i:2d}. {ciudad_nombre[:30]:30} - {sensores:3d} sensores")
        
        # Parámetros
        print(f"\n🧪 PARÁMETROS MONITOREADOS:")
        parametros = df_sensores.groupby('parametro')['sensor_id'].nunique().sort_values(ascending=False)
        for i, (param, sensores) in enumerate(parametros.items(), 1):
            print(f"   {i:2d}. {param:15} - {sensores:3d} sensores")

def main():
    """Función principal"""
    
    inicio = datetime.now()
    print("🚀 INICIANDO EXTRACCIÓN OPTIMIZADA DE CHILE")
    print("=" * 50)
    
    exito = extraer_datos_chile_inteligente()
    
    fin = datetime.now()
    duracion = fin - inicio
    
    print("\n" + "=" * 50)
    if exito:
        print("🎉 EXTRACCIÓN COMPLETADA EXITOSAMENTE")
        print("📂 Los datos están guardados en formato Excel y CSV")
        print("📊 El archivo Excel incluye múltiples hojas con análisis")
    else:
        print("😞 LA EXTRACCIÓN NO PUDO COMPLETARSE")
    
    print(f"⏱️ Duración: {duracion}")
    print(f"🕒 Finalizado: {fin.strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()

