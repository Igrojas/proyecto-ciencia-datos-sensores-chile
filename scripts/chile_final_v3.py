# -*- coding: utf-8 -*-
"""
Extractor FINAL de datos de Chile - API v3 OpenAQ (FUNCIONAL)
"""
#%%
import urllib.request
import urllib.parse
import json
import ssl
from datetime import datetime, timedelta

# Configuración
API_KEY = "91eab8b4c15ab8e5eda9712fa803abe4bb45e5a6c8ee961d295de18b0b15722a"
BASE_URL = "https://api.openaq.org/v3"

def hacer_peticion(endpoint, params=None):
    """Hacer petición a la API v3 de OpenAQ"""
    
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
    
    req = urllib.request.Request(url, headers=headers)
    
    try:
        print(f"🔍 {endpoint}: ", end="")
        
        with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
            if response.getcode() == 200:
                data = json.loads(response.read().decode('utf-8'))
                print(f"✅ {len(data.get('results', []))} resultados")
                return data
            else:
                print(f"❌ Status {response.getcode()}")
                return None
                
    except Exception as e:
        print(f"⚠️ Error: {e}")
        return None

def obtener_ubicaciones_chile():
    """Obtener todas las ubicaciones de Chile"""
    
    print("\n1️⃣ === OBTENIENDO UBICACIONES DE CHILE ===")
    
    ubicaciones_data = hacer_peticion('locations', {
        'countries_id': 3,  # Chile
        'limit': 200
    })
    
    if ubicaciones_data and ubicaciones_data.get('results'):
        ubicaciones = ubicaciones_data['results']
        
        # Agrupar por ciudad (locality)
        ciudades = {}
        
        for ubic in ubicaciones:
            locality = ubic.get('locality', 'Sin ciudad')
            if locality and locality != 'Sin ciudad':
                if locality not in ciudades:
                    ciudades[locality] = []
                ciudades[locality].append(ubic)
        
        print(f"\n   🏙️ CIUDADES ENCONTRADAS:")
        for ciudad, ubicaciones_ciudad in sorted(ciudades.items(), key=lambda x: len(x[1]), reverse=True):
            print(f"   📍 {ciudad}: {len(ubicaciones_ciudad)} ubicaciones")
        
        return ciudades
    
    return {}

def obtener_datos_sensor(sensor_id, sensor_name, ubicacion_name):
    """Obtener datos más recientes de un sensor específico"""
    
    # Intentar diferentes endpoints para obtener datos del sensor
    endpoints = [
        f'sensors/{sensor_id}/measurements/latest',
        f'sensors/{sensor_id}/latest',
        f'sensors/{sensor_id}'
    ]
    
    for endpoint in endpoints:
        print(f"     📡 {endpoint}: ", end="")
        
        data = hacer_peticion(endpoint.replace(f'{BASE_URL}/', ''))
        
        if data:
            # Diferentes estructuras posibles de respuesta
            if isinstance(data, dict):
                if 'results' in data and data['results']:
                    print(f"✅ Datos encontrados")
                    return data['results']
                elif 'value' in data:
                    print(f"✅ Valor: {data.get('value')}")
                    return [data]
                else:
                    print(f"ℹ️ Estructura: {list(data.keys())}")
            elif isinstance(data, list):
                print(f"✅ {len(data)} registros")
                return data
        else:
            print("❌")
    
    return []

def extraer_datos_chile_completo():
    """Extractor principal para Chile"""
    
    print("🇨🇱 === EXTRACTOR COMPLETO DE DATOS DE CHILE ===")
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    # Obtener ubicaciones por ciudad
    ciudades = obtener_ubicaciones_chile()
    
    if not ciudades:
        print("\n❌ No se encontraron ubicaciones en Chile")
        return False
    
    # Seleccionar las 2 ciudades con más ubicaciones
    ciudades_principales = sorted(ciudades.items(), key=lambda x: len(x[1]), reverse=True)[:2]
    
    print(f"\n2️⃣ === EXTRAYENDO DATOS DE 2 CIUDADES PRINCIPALES ===")
    for i, (ciudad, ubicaciones) in enumerate(ciudades_principales, 1):
        print(f"   {i}. {ciudad} ({len(ubicaciones)} ubicaciones)")
    
    # Datos recolectados
    todos_los_datos = []
    
    for ciudad, ubicaciones in ciudades_principales:
        print(f"\n3️⃣ === PROCESANDO {ciudad.upper()} ===")
        
        datos_ciudad = []
        
        # Procesar cada ubicación de la ciudad
        for ubic in ubicaciones[:3]:  # Máximo 3 ubicaciones por ciudad
            ubicacion_name = ubic.get('name', 'Sin nombre')
            ubicacion_id = ubic.get('id')
            sensores = ubic.get('sensors', [])
            
            print(f"\n   📍 {ubicacion_name} (ID: {ubicacion_id})")
            print(f"   🔬 Sensores disponibles: {len(sensores)}")
            
            # Mostrar información de sensores
            for sensor in sensores[:6]:  # Máximo 6 sensores por ubicación
                sensor_id = sensor.get('id')
                sensor_name = sensor.get('name', 'Sin nombre')
                parametro = sensor.get('parameter', {})
                param_name = parametro.get('name') if isinstance(parametro, dict) else 'N/A'
                param_units = parametro.get('units') if isinstance(parametro, dict) else 'N/A'
                
                print(f"     🧪 {param_name} ({param_units}) - Sensor {sensor_id}")
                
                # Intentar obtener datos del sensor
                datos_sensor = obtener_datos_sensor(sensor_id, sensor_name, ubicacion_name)
                
                # Procesar datos del sensor
                for dato in datos_sensor:
                    if isinstance(dato, dict):
                        registro = {
                            'fecha_extraccion': datetime.now().isoformat(),
                            'ciudad': ciudad,
                            'ubicacion': ubicacion_name,
                            'ubicacion_id': ubicacion_id,
                            'sensor_id': sensor_id,
                            'parametro': param_name,
                            'unidades': param_units,
                            'valor': dato.get('value', 'N/A'),
                            'fecha_medicion': dato.get('datetime', dato.get('date', 'N/A')),
                            'latitud': ubic.get('coordinates', {}).get('latitude'),
                            'longitud': ubic.get('coordinates', {}).get('longitude'),
                            'proveedor': ubic.get('provider', {}).get('name') if isinstance(ubic.get('provider'), dict) else 'N/A'
                        }
                        datos_ciudad.append(registro)
        
        # Guardar datos de la ciudad
        if datos_ciudad:
            filename = f"{ciudad.lower().replace(' ', '_')}_datos_sensores.csv"
            guardar_csv_simple(datos_ciudad, filename)
            todos_los_datos.extend(datos_ciudad)
            print(f"\n   ✅ {ciudad}: {len(datos_ciudad)} registros de sensores")
        else:
            print(f"\n   ❌ {ciudad}: No se obtuvieron datos de sensores")
    
    # Guardar datos combinados y mostrar resumen
    if todos_los_datos:
        print(f"\n4️⃣ === GUARDANDO DATOS COMBINADOS ===")
        guardar_csv_simple(todos_los_datos, 'chile_completo_sensores.csv')
        mostrar_resumen_final(todos_los_datos)
        return True
    else:
        print(f"\n❌ No se obtuvieron datos de ninguna ciudad")
        return False

def guardar_csv_simple(datos, filename):
    """Guardar datos en formato CSV simple"""
    
    if not datos:
        return
    
    try:
        # Headers
        headers = list(datos[0].keys())
        csv_lines = [','.join(headers)]
        
        # Datos
        for dato in datos:
            row = []
            for header in headers:
                value = str(dato.get(header, '')).replace(',', ';').replace('\n', ' ')
                row.append(f'"{value}"')  # Encerrar en comillas para evitar problemas
            csv_lines.append(','.join(row))
        
        # Guardar
        with open(filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(csv_lines))
        
        print(f"   💾 Guardado: {filename}")
        
    except Exception as e:
        print(f"   ⚠️ Error guardando {filename}: {e}")

def mostrar_resumen_final(datos):
    """Mostrar resumen final de los datos extraídos"""
    
    print(f"\n📊 === RESUMEN FINAL ===")
    print(f"   📁 Total registros: {len(datos)}")
    
    # Agrupar por ciudad
    ciudades_count = {}
    parametros = set()
    ubicaciones = set()
    
    for dato in datos:
        ciudad = dato.get('ciudad', 'N/A')
        parametro = dato.get('parametro', 'N/A')
        ubicacion = dato.get('ubicacion', 'N/A')
        
        ciudades_count[ciudad] = ciudades_count.get(ciudad, 0) + 1
        parametros.add(parametro)
        ubicaciones.add(ubicacion)
    
    print(f"\n   🏙️ Datos por ciudad:")
    for ciudad, count in ciudades_count.items():
        print(f"     • {ciudad}: {count} registros")
    
    print(f"\n   🧪 Parámetros monitoreados:")
    for parametro in sorted(parametros):
        print(f"     • {parametro}")
    
    print(f"\n   📍 Ubicaciones monitoreadas: {len(ubicaciones)}")
    
    print(f"\n   📂 Archivos generados:")
    print(f"     • Datos por ciudad individual")
    print(f"     • chile_completo_sensores.csv (datos combinados)")

if __name__ == "__main__":
    print("🚀 INICIANDO EXTRACCIÓN FINAL DE DATOS DE CHILE")
    print("=" * 50)
    
    exito = extraer_datos_chile_completo()
    
    print("\n" + "=" * 50)
    if exito:
        print("🎉 ¡EXTRACCIÓN COMPLETADA EXITOSAMENTE!")
        print("📂 Revisa los archivos CSV generados en el directorio actual")
    else:
        print("😞 La extracción no pudo completarse")
        print("💡 Intenta ejecutar el script nuevamente o verifica la conectividad")
    
    print("🔗 API utilizada: OpenAQ v3")
    print("🗓️ Datos extraídos el:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

# %%
