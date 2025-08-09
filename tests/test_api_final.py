# -*- coding: utf-8 -*-
"""
Test final completo de la API OpenAQ v3
"""

import urllib.request
import urllib.parse
import json
import ssl
from datetime import datetime, timedelta

# Configuración
API_KEY = "91eab8b4c15ab8e5eda9712fa803abe4bb45e5a6c8ee961d295de18b0b15722a"
BASE_URL = "https://api.openaq.org/v3"

def hacer_peticion_test(endpoint, params=None):
    """Hacer petición de prueba a la API"""
    
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
        with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
            if response.getcode() == 200:
                data = json.loads(response.read().decode('utf-8'))
                return True, data, response.getcode()
            else:
                return False, response.read().decode('utf-8'), response.getcode()
                
    except Exception as e:
        return False, str(e), None

def test_api_completo():
    """Test completo de la API OpenAQ v3"""
    
    print("🧪 === TEST FINAL DE API OPENAQ v3 ===")
    print(f"🕒 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔗 URL Base: {BASE_URL}")
    print("=" * 50)
    
    resultados = {
        'tests_passed': 0,
        'tests_failed': 0,
        'tests_total': 0,
        'detalles': []
    }
    
    # Test 1: Conectividad básica
    print("\n1️⃣ TEST: Conectividad básica")
    print("-" * 30)
    
    success, data, status = hacer_peticion_test('countries', {'limit': 1})
    resultados['tests_total'] += 1
    
    if success:
        print("✅ Conectividad: OK")
        print(f"   Status: {status}")
        print(f"   Respuesta: {len(data.get('results', []))} países obtenidos")
        resultados['tests_passed'] += 1
        resultados['detalles'].append("✅ Conectividad básica")
    else:
        print("❌ Conectividad: FAILED")
        print(f"   Error: {data}")
        resultados['tests_failed'] += 1
        resultados['detalles'].append("❌ Conectividad básica")
    
    # Test 2: Autenticación
    print("\n2️⃣ TEST: Autenticación con API Key")
    print("-" * 30)
    
    success, data, status = hacer_peticion_test('countries', {'limit': 5})
    resultados['tests_total'] += 1
    
    if success and status == 200:
        print("✅ Autenticación: OK")
        print(f"   API Key válida")
        print(f"   Países disponibles: {len(data.get('results', []))}")
        resultados['tests_passed'] += 1
        resultados['detalles'].append("✅ Autenticación válida")
    else:
        print("❌ Autenticación: FAILED")
        print(f"   Status: {status}")
        resultados['tests_failed'] += 1
        resultados['detalles'].append("❌ Autenticación fallida")
    
    # Test 3: Búsqueda de Chile
    print("\n3️⃣ TEST: Disponibilidad de datos de Chile")
    print("-" * 30)
    
    success, data, status = hacer_peticion_test('countries')
    resultados['tests_total'] += 1
    
    chile_encontrado = False
    chile_info = None
    
    if success:
        for pais in data.get('results', []):
            if pais.get('code') == 'CL':
                chile_encontrado = True
                chile_info = pais
                break
        
        if chile_encontrado:
            print("✅ Chile encontrado: OK")
            print(f"   ID: {chile_info.get('id')}")
            print(f"   Nombre: {chile_info.get('name')}")
            print(f"   Parámetros: {len(chile_info.get('parameters', []))}")
            print(f"   Último dato: {chile_info.get('datetimeLast', 'N/A')}")
            resultados['tests_passed'] += 1
            resultados['detalles'].append("✅ Chile disponible")
        else:
            print("❌ Chile NO encontrado")
            resultados['tests_failed'] += 1
            resultados['detalles'].append("❌ Chile no disponible")
    else:
        print("❌ Error obteniendo países")
        resultados['tests_failed'] += 1
        resultados['detalles'].append("❌ Error en búsqueda de Chile")
    
    # Test 4: Ubicaciones en Chile
    print("\n4️⃣ TEST: Ubicaciones disponibles en Chile")
    print("-" * 30)
    
    success, data, status = hacer_peticion_test('locations', {
        'countries_id': 3,  # ID de Chile
        'limit': 10
    })
    resultados['tests_total'] += 1
    
    if success:
        ubicaciones = data.get('results', [])
        if ubicaciones:
            print("✅ Ubicaciones de Chile: OK")
            print(f"   Ubicaciones encontradas: {len(ubicaciones)}")
            
            # Mostrar algunas ubicaciones
            ciudades = set()
            for ubic in ubicaciones[:5]:
                locality = ubic.get('locality', 'Sin ciudad')
                if locality:
                    ciudades.add(locality)
                print(f"   📍 {ubic.get('name', 'Sin nombre')} - {locality}")
            
            print(f"   Ciudades únicas: {len(ciudades)}")
            resultados['tests_passed'] += 1
            resultados['detalles'].append(f"✅ {len(ubicaciones)} ubicaciones en Chile")
        else:
            print("❌ No se encontraron ubicaciones en Chile")
            resultados['tests_failed'] += 1
            resultados['detalles'].append("❌ Sin ubicaciones en Chile")
    else:
        print("❌ Error obteniendo ubicaciones")
        resultados['tests_failed'] += 1
        resultados['detalles'].append("❌ Error en ubicaciones")
    
    # Test 5: Sensores específicos
    print("\n5️⃣ TEST: Acceso a sensores específicos")
    print("-" * 30)
    
    # Usar un sensor conocido del test anterior
    test_sensor_ids = [105, 676, 1091]  # IDs conocidos de sensores chilenos
    sensores_funcionando = 0
    
    for sensor_id in test_sensor_ids:
        success, data, status = hacer_peticion_test(f'sensors/{sensor_id}')
        if success:
            sensores_funcionando += 1
            sensor_info = data if isinstance(data, dict) else data.get('results', {})
            parametro = sensor_info.get('parameter', {})
            param_name = parametro.get('name') if isinstance(parametro, dict) else 'N/A'
            print(f"   ✅ Sensor {sensor_id}: {param_name}")
        else:
            print(f"   ❌ Sensor {sensor_id}: No disponible")
    
    resultados['tests_total'] += 1
    if sensores_funcionando > 0:
        print(f"✅ Sensores: {sensores_funcionando}/{len(test_sensor_ids)} funcionando")
        resultados['tests_passed'] += 1
        resultados['detalles'].append(f"✅ {sensores_funcionando} sensores funcionando")
    else:
        print("❌ Ningún sensor disponible")
        resultados['tests_failed'] += 1
        resultados['detalles'].append("❌ Sensores no disponibles")
    
    # Test 6: Rendimiento
    print("\n6️⃣ TEST: Rendimiento de la API")
    print("-" * 30)
    
    import time
    start_time = time.time()
    
    success, data, status = hacer_peticion_test('locations', {
        'countries_id': 3,
        'limit': 50
    })
    
    end_time = time.time()
    response_time = end_time - start_time
    
    resultados['tests_total'] += 1
    
    if success and response_time < 10:  # Menos de 10 segundos
        print(f"✅ Rendimiento: OK ({response_time:.2f}s)")
        print(f"   Tiempo de respuesta aceptable")
        resultados['tests_passed'] += 1
        resultados['detalles'].append(f"✅ Rendimiento: {response_time:.2f}s")
    else:
        print(f"❌ Rendimiento: LENTO ({response_time:.2f}s)")
        resultados['tests_failed'] += 1
        resultados['detalles'].append(f"❌ Rendimiento lento: {response_time:.2f}s")
    
    # Resumen final
    print("\n" + "=" * 50)
    print("📊 === RESUMEN DE TESTS ===")
    print(f"✅ Tests exitosos: {resultados['tests_passed']}")
    print(f"❌ Tests fallidos: {resultados['tests_failed']}")
    print(f"📋 Total tests: {resultados['tests_total']}")
    
    porcentaje_exito = (resultados['tests_passed'] / resultados['tests_total']) * 100
    print(f"📈 Porcentaje de éxito: {porcentaje_exito:.1f}%")
    
    print("\n🔍 Detalles:")
    for detalle in resultados['detalles']:
        print(f"   {detalle}")
    
    # Veredicto final
    print("\n" + "=" * 50)
    if porcentaje_exito >= 80:
        print("🎉 VEREDICTO: API COMPLETAMENTE FUNCIONAL")
        print("✅ El sistema está listo para extracción de datos")
    elif porcentaje_exito >= 60:
        print("⚠️ VEREDICTO: API PARCIALMENTE FUNCIONAL")
        print("🔧 Algunos componentes necesitan atención")
    else:
        print("❌ VEREDICTO: API CON PROBLEMAS")
        print("🛠️ Se requiere revisión del sistema")
    
    return resultados

if __name__ == "__main__":
    test_api_completo()

