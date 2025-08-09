# -*- coding: utf-8 -*-
"""
Script de debug para investigar la estructura de la API v3
"""
#%%
import urllib.request
import urllib.parse
import json
import ssl

# Configuración
API_KEY = "91eab8b4c15ab8e5eda9712fa803abe4bb45e5a6c8ee961d295de18b0b15722a"
BASE_URL = "https://api.openaq.org/v3"

def hacer_peticion_debug(endpoint, params=None):
    """Hacer petición y mostrar estructura de respuesta"""
    
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
        print(f"🔍 Consultando: {url}")
        
        with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
            if response.getcode() == 200:
                data = json.loads(response.read().decode('utf-8'))
                print(f"   ✅ Status: {response.getcode()}")
                return data
            else:
                print(f"   ❌ Status: {response.getcode()}")
                return None
                
    except Exception as e:
        print(f"   ⚠️ Error: {e}")
        return None

def debug_estructura_api():
    """Investigar la estructura de la API v3"""
    
    print("🔍 === DEBUG DE ESTRUCTURA API v3 ===\n")
    
    # 1. Examinar estructura de países
    print("1️⃣ ESTRUCTURA DE PAÍSES:")
    paises_data = hacer_peticion_debug('countries', {'limit': 3})
    
    if paises_data:
        print(f"   📋 Claves principales: {list(paises_data.keys())}")
        if 'results' in paises_data:
            print(f"   📊 Número de países: {len(paises_data['results'])}")
            if paises_data['results']:
                print(f"   🏷️ Estructura de país:")
                primer_pais = paises_data['results'][0]
                print(f"      {json.dumps(primer_pais, indent=6, ensure_ascii=False)}")
    
    # 2. Examinar estructura de ubicaciones de Chile
    print(f"\n2️⃣ ESTRUCTURA DE UBICACIONES DE CHILE:")
    ubicaciones_data = hacer_peticion_debug('locations', {
        'countries_id': 3,
        'limit': 5
    })
    
    if ubicaciones_data:
        print(f"   📋 Claves principales: {list(ubicaciones_data.keys())}")
        if 'results' in ubicaciones_data:
            print(f"   📊 Número de ubicaciones: {len(ubicaciones_data['results'])}")
            if ubicaciones_data['results']:
                print(f"   🏷️ Estructura de ubicación:")
                primera_ubicacion = ubicaciones_data['results'][0]
                print(f"      {json.dumps(primera_ubicacion, indent=6, ensure_ascii=False)}")
                
                # Buscar campos que podrían contener ciudad
                print(f"\n   🔍 Buscando campos de ciudad en ubicación:")
                for key, value in primera_ubicacion.items():
                    if isinstance(value, str) and len(value) > 0:
                        print(f"      {key}: {value}")
    
    # 3. Examinar endpoints de mediciones
    print(f"\n3️⃣ PROBANDO ENDPOINTS DE MEDICIONES:")
    
    endpoints_test = [
        'measurements',
        'measurements/latest',
        'sensors'
    ]
    
    for endpoint in endpoints_test:
        print(f"\n   Probando: {endpoint}")
        
        params_test = {'limit': 3}
        if endpoint == 'measurements':
            params_test['countries_id'] = 3
        
        data = hacer_peticion_debug(endpoint, params_test)
        
        if data:
            print(f"      ✅ Funcionó")
            print(f"      📋 Claves: {list(data.keys())}")
            if 'results' in data and data['results']:
                print(f"      📊 Registros: {len(data['results'])}")
                primer_resultado = data['results'][0]
                print(f"      🏷️ Estructura:")
                # Mostrar solo las claves principales para no saturar
                if isinstance(primer_resultado, dict):
                    for key in list(primer_resultado.keys())[:10]:
                        value = primer_resultado[key]
                        if isinstance(value, (str, int, float)):
                            print(f"         {key}: {value}")
                        else:
                            print(f"         {key}: {type(value)}")
        else:
            print(f"      ❌ No funcionó")

if __name__ == "__main__":
    debug_estructura_api()

# %%
