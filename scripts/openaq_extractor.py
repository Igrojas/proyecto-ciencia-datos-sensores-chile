#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extractor de datos de calidad del aire de OpenAQ
================================================

Este script permite extraer datos de calidad del aire de la API de OpenAQ
con parámetros personalizables para filtrar por países, ciudades, 
contaminantes y fechas.

Autor: Asistente IA
Fecha: 2025
"""

import pandas as pd
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
import time


class OpenAQExtractor:
    """
    Clase para extraer datos de calidad del aire de OpenAQ
    """
    
    def __init__(self, api_key: str):
        """
        Inicializa el extractor con la clave de API
        
        Args:
            api_key (str): Clave de API de OpenAQ
        """
        self.api_key = api_key
        self.base_url = "https://api.openaq.org/v3"
        self.headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        }
    
    def get_countries(self) -> List[Dict]:
        """
        Obtiene la lista de países disponibles
        
        Returns:
            List[Dict]: Lista de países con sus códigos
        """
        url = f"{self.base_url}/countries"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            return data.get('results', [])
        except Exception as e:
            print(f"Error al obtener países: {e}")
            return []
    
    def get_cities(self, country_code: Optional[str] = None) -> List[Dict]:
        """
        Obtiene la lista de ciudades disponibles
        
        Args:
            country_code (str, optional): Código del país para filtrar
            
        Returns:
            List[Dict]: Lista de ciudades
        """
        url = f"{self.base_url}/cities"
        params = {}
        
        if country_code:
            params['country'] = country_code
            
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get('results', [])
        except Exception as e:
            print(f"Error al obtener ciudades: {e}")
            return []
    
    def get_parameters(self) -> List[Dict]:
        """
        Obtiene la lista de parámetros/contaminantes disponibles
        
        Returns:
            List[Dict]: Lista de parámetros de calidad del aire
        """
        url = f"{self.base_url}/parameters"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            return data.get('results', [])
        except Exception as e:
            print(f"Error al obtener parámetros: {e}")
            return []
    
    def get_locations(self, 
                     country: Optional[str] = None,
                     city: Optional[str] = None,
                     parameter: Optional[str] = None) -> List[Dict]:
        """
        Obtiene las ubicaciones/estaciones de monitoreo
        
        Args:
            country (str, optional): Código del país
            city (str, optional): Nombre de la ciudad
            parameter (str, optional): Parámetro a medir
            
        Returns:
            List[Dict]: Lista de ubicaciones
        """
        url = f"{self.base_url}/locations"
        params = {}
        
        if country:
            params['country'] = country
        if city:
            params['city'] = city
        if parameter:
            params['parameter'] = parameter
            
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get('results', [])
        except Exception as e:
            print(f"Error al obtener ubicaciones: {e}")
            return []
    
    def get_measurements(self,
                        country: Optional[str] = None,
                        city: Optional[str] = None,
                        location: Optional[str] = None,
                        parameter: Optional[Union[str, List[str]]] = None,
                        date_from: Optional[str] = None,
                        date_to: Optional[str] = None,
                        limit: int = 1000,
                        max_pages: int = 10) -> pd.DataFrame:
        """
        Obtiene mediciones de calidad del aire
        
        Args:
            country (str, optional): Código del país (ej: 'ES', 'US', 'MX')
            city (str, optional): Nombre de la ciudad
            location (str, optional): ID o nombre de la ubicación específica
            parameter (str/List[str], optional): Parámetro(s) a obtener 
                                               (ej: 'pm25', 'pm10', 'o3', 'no2', 'so2', 'co')
            date_from (str, optional): Fecha inicio (YYYY-MM-DD)
            date_to (str, optional): Fecha fin (YYYY-MM-DD)
            limit (int): Número de resultados por página (máx 10000)
            max_pages (int): Número máximo de páginas a obtener
            
        Returns:
            pd.DataFrame: DataFrame con las mediciones
        """
        url = f"{self.base_url}/measurements"
        all_results = []
        page = 1
        
        # Preparar parámetros base
        params = {
            'limit': min(limit, 10000),  # OpenAQ limita a 10000 por página
            'page': page,
            'order_by': 'datetime',
            'sort_order': 'desc'
        }
        
        # Agregar filtros opcionales
        if country:
            params['country'] = country
        if city:
            params['city'] = city
        if location:
            params['location'] = location
        if parameter:
            if isinstance(parameter, list):
                params['parameter'] = parameter
            else:
                params['parameter'] = [parameter]
        if date_from:
            params['date_from'] = date_from
        if date_to:
            params['date_to'] = date_to
        
        print(f"Obteniendo mediciones con parámetros: {params}")
        
        try:
            while page <= max_pages:
                params['page'] = page
                print(f"Procesando página {page}...")
                
                response = requests.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                data = response.json()
                
                results = data.get('results', [])
                if not results:
                    print("No hay más resultados")
                    break
                
                all_results.extend(results)
                
                # Verificar si hay más páginas
                meta = data.get('meta', {})
                total_pages = meta.get('pages', 1)
                
                print(f"Página {page} de {total_pages} - {len(results)} registros obtenidos")
                
                if page >= total_pages:
                    break
                    
                page += 1
                time.sleep(0.1)  # Pequeña pausa para no sobrecargar la API
                
        except Exception as e:
            print(f"Error al obtener mediciones: {e}")
            return pd.DataFrame()
        
        if not all_results:
            print("No se encontraron datos")
            return pd.DataFrame()
        
        # Convertir a DataFrame
        df = pd.DataFrame(all_results)
        
        # Procesar fechas
        if 'date' in df.columns:
            df['datetime'] = pd.to_datetime(df['date'].apply(lambda x: x.get('utc') if isinstance(x, dict) else x))
            df['fecha'] = df['datetime'].dt.date
            df['hora'] = df['datetime'].dt.time
        
        # Limpiar y organizar columnas
        columns_to_keep = ['datetime', 'fecha', 'hora', 'parameter', 'value', 'unit', 
                          'country', 'city', 'location', 'coordinates']
        
        available_columns = [col for col in columns_to_keep if col in df.columns]
        df = df[available_columns]
        
        print(f"Total de registros obtenidos: {len(df)}")
        return df
    
    def save_to_csv(self, df: pd.DataFrame, filename: str) -> None:
        """
        Guarda el DataFrame en un archivo CSV
        
        Args:
            df (pd.DataFrame): DataFrame a guardar
            filename (str): Nombre del archivo
        """
        try:
            df.to_csv(filename, index=False, encoding='utf-8')
            print(f"Datos guardados en: {filename}")
        except Exception as e:
            print(f"Error al guardar archivo: {e}")
    
    def save_to_excel(self, df: pd.DataFrame, filename: str) -> None:
        """
        Guarda el DataFrame en un archivo Excel
        
        Args:
            df (pd.DataFrame): DataFrame a guardar
            filename (str): Nombre del archivo
        """
        try:
            df.to_excel(filename, index=False)
            print(f"Datos guardados en: {filename}")
        except Exception as e:
            print(f"Error al guardar archivo Excel: {e}")
    
    def get_data_summary(self, df: pd.DataFrame) -> Dict:
        """
        Obtiene un resumen de los datos
        
        Args:
            df (pd.DataFrame): DataFrame con los datos
            
        Returns:
            Dict: Resumen estadístico
        """
        if df.empty:
            return {}
        
        summary = {
            'total_registros': len(df),
            'fechas': {
                'fecha_inicio': df['datetime'].min() if 'datetime' in df.columns else None,
                'fecha_fin': df['datetime'].max() if 'datetime' in df.columns else None
            },
            'paises': df['country'].unique().tolist() if 'country' in df.columns else [],
            'ciudades': df['city'].unique().tolist() if 'city' in df.columns else [],
            'parametros': df['parameter'].unique().tolist() if 'parameter' in df.columns else [],
            'ubicaciones': df['location'].unique().tolist() if 'location' in df.columns else []
        }
        
        # Estadísticas por parámetro
        if 'parameter' in df.columns and 'value' in df.columns:
            summary['estadisticas_por_parametro'] = {}
            for param in df['parameter'].unique():
                param_data = df[df['parameter'] == param]['value']
                summary['estadisticas_por_parametro'][param] = {
                    'count': len(param_data),
                    'mean': float(param_data.mean()),
                    'min': float(param_data.min()),
                    'max': float(param_data.max()),
                    'std': float(param_data.std())
                }
        
        return summary


def main():
    """
    Función principal para demostrar el uso del extractor
    """
    print("=== Extractor de Datos de Calidad del Aire - OpenAQ ===\n")
    
    # IMPORTANTE: Reemplaza con tu clave de API real
    # Regístrate en: https://explore.openaq.org/register
    api_key = "TU_CLAVE_DE_API_AQUI"
    
    if api_key == "TU_CLAVE_DE_API_AQUI":
        print("⚠️  IMPORTANTE: Debes obtener una clave de API de OpenAQ")
        print("1. Regístrate en: https://explore.openaq.org/register")
        print("2. Ve a tu cuenta: https://explore.openaq.org/account")
        print("3. Copia tu clave de API y reemplázala en este script")
        return
    
    # Inicializar extractor
    extractor = OpenAQExtractor(api_key)
    
    # Ejemplo 1: Obtener información básica
    print("1. Obteniendo países disponibles...")
    countries = extractor.get_countries()
    print(f"   Países encontrados: {len(countries)}")
    
    print("\n2. Obteniendo parámetros disponibles...")
    parameters = extractor.get_parameters()
    print("   Parámetros disponibles:")
    for param in parameters[:10]:  # Mostrar solo los primeros 10
        print(f"   - {param.get('name', 'N/A')} ({param.get('id', 'N/A')})")
    
    # Ejemplo 2: Obtener datos de España (últimos 7 días)
    print("\n3. Obteniendo datos de calidad del aire de España...")
    fecha_fin = datetime.now().strftime('%Y-%m-%d')
    fecha_inicio = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    df_spain = extractor.get_measurements(
        country='ES',
        parameter=['pm25', 'pm10', 'no2'],
        date_from=fecha_inicio,
        date_to=fecha_fin,
        limit=1000,
        max_pages=3
    )
    
    if not df_spain.empty:
        print(f"   Datos obtenidos: {len(df_spain)} registros")
        
        # Guardar datos
        extractor.save_to_csv(df_spain, 'datos_calidad_aire_espana.csv')
        
        # Mostrar resumen
        summary = extractor.get_data_summary(df_spain)
        print(f"\n   Resumen de datos:")
        print(f"   - Fechas: {summary['fechas']['fecha_inicio']} a {summary['fechas']['fecha_fin']}")
        print(f"   - Ciudades: {', '.join(summary['ciudades'][:5])}...")
        print(f"   - Parámetros: {', '.join(summary['parametros'])}")
        
        # Mostrar muestra de datos
        print(f"\n   Muestra de datos:")
        print(df_spain.head().to_string())
    
    print("\n✅ Proceso completado!")
    print("\nEjemplos de uso adicionales:")
    print("- Para obtener datos de México: country='MX'")
    print("- Para una ciudad específica: city='Madrid'")
    print("- Para más contaminantes: parameter=['pm25', 'pm10', 'o3', 'no2', 'so2', 'co']")


if __name__ == "__main__":
    main()
