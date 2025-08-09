#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test simple de la API v3 de OpenAQ
"""
#%%
import requests
import json

# API Configuration para v3
API_KEY = "91eab8b4c15ab8e5eda9712fa803abe4bb45e5a6c8ee961d295de18b0b15722a"
BASE_URL = "https://api.openaq.org/v3"
HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

def test_api_endpoints():
    """Probar diferentes endpoints de la API v3"""
    
    print("🧪 === PRUEBA DE ENDPOINTS API v3 ===\n")
    
    # Lista de endpoints posibles para probar
    endpoints_test = [
        "/countries",
        "/locations", 
        "/parameters",
        "/measurements",
        "/sensors",
        "/providers"
    ]
    
    for endpoint in endpoints_test:
        print(f"🔍 Probando: {BASE_URL}{endpoint}")
        
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", headers=HEADERS, timeout=10)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Exitoso - Estructura disponible")
                if 'results' in data:
                    print(f"   📊 Resultados: {len(data['results'])} elementos")
                print(f"   🔑 Claves: {list(data.keys())}")
            else:
                print(f"   ❌ Error: {response.text[:100]}...")
                
        except Exception as e:
            print(f"   ⚠️ Error de conexión: {e}")
        
        print()

def test_chile_specific():
    """Probar endpoints específicos para Chile"""
    
    print("🇨🇱 === PRUEBA ESPECÍFICA PARA CHILE ===\n")
    
    # Probar búsqueda de países
    try:
        print("🔍 Buscando información de países...")
        response = requests.get(f"{BASE_URL}/countries", headers=HEADERS, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Países disponibles: {len(data.get('results', []))}")
            
            # Buscar Chile específicamente
            chile_found = False
            for country in data.get('results', []):
                if 'chile' in str(country).lower() or 'cl' in str(country).lower():
                    print(f"🇨🇱 Chile encontrado: {country}")
                    chile_found = True
                    
            if not chile_found:
                print("❌ Chile no encontrado en la lista")
                print("Primeros 5 países:")
                for country in data.get('results', [])[:5]:
                    print(f"   {country}")
        else:
            print(f"❌ Error al obtener países: {response.status_code}")
            print(f"Respuesta: {response.text[:200]}")
            
    except Exception as e:
        print(f"⚠️ Error: {e}")

if __name__ == "__main__":
    test_api_endpoints()
    test_chile_specific()

# %%
