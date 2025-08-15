#!/usr/bin/env python3
"""
Utilidades para el procesamiento de datos de calidad del aire
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

def load_air_quality_data(filepath):
    """
    Cargar datos de calidad del aire desde CSV
    
    Args:
        filepath (str): Ruta al archivo CSV
        
    Returns:
        pd.DataFrame: DataFrame con los datos cargados
    """
    try:
        df = pd.read_csv(filepath)
        print(f"✓ Datos cargados: {len(df):,} filas y {len(df.columns)} columnas")
        return df
    except Exception as e:
        print(f"✗ Error al cargar datos: {e}")
        return None

def convert_datetime_columns(df):
    """
    Convertir columnas de fecha a datetime
    
    Args:
        df (pd.DataFrame): DataFrame con columnas de fecha
        
    Returns:
        pd.DataFrame: DataFrame con fechas convertidas
    """
    date_columns = ['date_from_utc', 'date_from_local', 'date_to_utc', 'date_to_local']
    
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col])
    
    print("✓ Columnas de fecha convertidas")
    return df

def create_temporal_features(df):
    """
    Crear características temporales a partir de las fechas
    
    Args:
        df (pd.DataFrame): DataFrame con columna 'date_from_utc'
        
    Returns:
        pd.DataFrame: DataFrame con características temporales agregadas
    """
    if 'date_from_utc' not in df.columns:
        print("⚠ Columna 'date_from_utc' no encontrada")
        return df
    
    df['year'] = df['date_from_utc'].dt.year
    df['month'] = df['date_from_utc'].dt.month
    df['day'] = df['date_from_utc'].dt.day
    df['hour'] = df['date_from_utc'].dt.hour
    df['day_of_week'] = df['date_from_utc'].dt.dayofweek
    df['season'] = df['date_from_utc'].dt.month.map({
        12: 'Verano', 1: 'Verano', 2: 'Verano',
        3: 'Otoño', 4: 'Otoño', 5: 'Otoño',
        6: 'Invierno', 7: 'Invierno', 8: 'Invierno',
        9: 'Primavera', 10: 'Primavera', 11: 'Primavera'
    })
    
    print("✓ Características temporales creadas")
    return df

def get_parameter_statistics(df, parameter_name):
    """
    Obtener estadísticas para un parámetro específico
    
    Args:
        df (pd.DataFrame): DataFrame con los datos
        parameter_name (str): Nombre del parámetro
        
    Returns:
        dict: Diccionario con estadísticas del parámetro
    """
    param_data = df[df['parameter_name'] == parameter_name]['value']
    
    if len(param_data) == 0:
        return None
    
    stats = {
        'count': len(param_data),
        'mean': param_data.mean(),
        'std': param_data.std(),
        'min': param_data.min(),
        'max': param_data.max(),
        'q25': param_data.quantile(0.25),
        'q50': param_data.quantile(0.50),
        'q75': param_data.quantile(0.75),
        'iqr': param_data.quantile(0.75) - param_data.quantile(0.25)
    }
    
    return stats

def detect_outliers(df, parameter_name, method='iqr'):
    """
    Detectar valores atípicos para un parámetro
    
    Args:
        df (pd.DataFrame): DataFrame con los datos
        parameter_name (str): Nombre del parámetro
        method (str): Método de detección ('iqr' o 'zscore')
        
    Returns:
        tuple: (outliers, outlier_indices)
    """
    param_data = df[df['parameter_name'] == parameter_name]['value']
    
    if len(param_data) == 0:
        return [], []
    
    if method == 'iqr':
        Q1 = param_data.quantile(0.25)
        Q3 = param_data.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        outliers = param_data[(param_data < lower_bound) | (param_data > upper_bound)]
        outlier_indices = outliers.index
        
    elif method == 'zscore':
        z_scores = np.abs((param_data - param_data.mean()) / param_data.std())
        outliers = param_data[z_scores > 3]
        outlier_indices = outliers.index
    
    return outliers, outlier_indices

def create_pivot_table(df, index_cols, columns_col, values_col, aggfunc='mean'):
    """
    Crear tabla pivot para análisis de correlaciones
    
    Args:
        df (pd.DataFrame): DataFrame con los datos
        index_cols (list): Columnas para el índice
        columns_col (str): Columna para las columnas
        values_col (str): Columna para los valores
        aggfunc (str): Función de agregación
        
    Returns:
        pd.DataFrame: Tabla pivot
    """
    try:
        pivot_df = df.pivot_table(
            index=index_cols,
            columns=columns_col,
            values=values_col,
            aggfunc=aggfunc
        ).reset_index()
        
        print(f"✓ Tabla pivot creada: {pivot_df.shape}")
        return pivot_df
        
    except Exception as e:
        print(f"✗ Error al crear tabla pivot: {e}")
        return None

def calculate_correlations(pivot_df, exclude_cols=None):
    """
    Calcular matriz de correlaciones
    
    Args:
        pivot_df (pd.DataFrame): DataFrame pivot
        exclude_cols (list): Columnas a excluir del análisis
        
    Returns:
        pd.DataFrame: Matriz de correlaciones
    """
    if exclude_cols is None:
        exclude_cols = []
    
    # Excluir columnas no numéricas
    numeric_cols = pivot_df.select_dtypes(include=[np.number]).columns
    analysis_cols = [col for col in numeric_cols if col not in exclude_cols]
    
    correlation_matrix = pivot_df[analysis_cols].corr()
    
    print(f"✓ Matriz de correlaciones calculada: {correlation_matrix.shape}")
    return correlation_matrix

def get_air_quality_index(value, parameter_name):
    """
    Calcular índice de calidad del aire basado en estándares EPA
    
    Args:
        value (float): Valor del parámetro
        parameter_name (str): Nombre del parámetro
        
    Returns:
        dict: Diccionario con categoría y recomendaciones
    """
    # Estándares EPA para PM2.5 (μg/m³)
    if parameter_name.lower() == 'pm25':
        if value <= 12.0:
            category = "Buena"
            health_implications = "La calidad del aire se considera satisfactoria"
            cautionary_statement = "Ninguna"
        elif value <= 35.4:
            category = "Moderada"
            health_implications = "Algunas personas pueden ser sensibles"
            cautionary_statement = "Personas sensibles deben considerar reducir actividades al aire libre"
        elif value <= 55.4:
            category = "No saludable para grupos sensibles"
            health_implications = "Mayor probabilidad de efectos adversos"
            cautionary_statement = "Personas con problemas cardíacos o pulmonares deben evitar actividades al aire libre"
        elif value <= 150.4:
            category = "No saludable"
            health_implications = "Algunos miembros del público pueden experimentar efectos adversos"
            cautionary_statement = "Evitar actividades al aire libre"
        elif value <= 250.4:
            category = "Muy no saludable"
            health_implications = "Advertencia de emergencia sanitaria"
            cautionary_statement = "Evitar TODAS las actividades al aire libre"
        else:
            category = "Peligrosa"
            health_implications = "Advertencia de emergencia sanitaria"
            cautionary_statement = "Evitar TODAS las actividades al aire libre"
    
    # Estándares para O3 (ppm)
    elif parameter_name.lower() == 'o3':
        if value <= 0.054:
            category = "Buena"
            health_implications = "La calidad del aire se considera satisfactoria"
            cautionary_statement = "Ninguna"
        elif value <= 0.070:
            category = "Moderada"
            health_implications = "Algunas personas pueden ser sensibles"
            cautionary_statement = "Personas sensibles deben considerar reducir actividades al aire libre"
        elif value <= 0.085:
            category = "No saludable para grupos sensibles"
            health_implications = "Mayor probabilidad de efectos adversos"
            cautionary_statement = "Personas con problemas respiratorios deben evitar actividades al aire libre"
        elif value <= 0.105:
            category = "No saludable"
            health_implications = "Algunos miembros del público pueden experimentar efectos adversos"
            cautionary_statement = "Evitar actividades al aire libre"
        elif value <= 0.200:
            category = "Muy no saludable"
            health_implications = "Advertencia de emergencia sanitaria"
            cautionary_statement = "Evitar TODAS las actividades al aire libre"
        else:
            category = "Peligrosa"
            health_implications = "Advertencia de emergencia sanitaria"
            cautionary_statement = "Evitar TODAS las actividades al aire libre"
    
    else:
        category = "No clasificado"
        health_implications = "Estándares no disponibles para este parámetro"
        cautionary_statement = "Consultar autoridades locales"
    
    return {
        'category': category,
        'health_implications': health_implications,
        'cautionary_statement': cautionary_statement
    }

def save_processed_data(df, filepath, description=""):
    """
    Guardar datos procesados
    
    Args:
        df (pd.DataFrame): DataFrame a guardar
        filepath (str): Ruta donde guardar el archivo
        description (str): Descripción de los datos
    """
    try:
        df.to_csv(filepath, index=False, encoding='utf-8')
        print(f"✓ Datos guardados en: {filepath}")
        if description:
            print(f"  Descripción: {description}")
    except Exception as e:
        print(f"✗ Error al guardar datos: {e}")

def print_data_summary(df):
    """
    Imprimir resumen de los datos
    
    Args:
        df (pd.DataFrame): DataFrame a resumir
    """
    print("\n=== RESUMEN DE DATOS ===")
    print(f"Total de mediciones: {len(df):,}")
    print(f"Parámetros disponibles: {', '.join(df['parameter_name'].unique())}")
    print(f"Ubicaciones: {', '.join(df['location_name'].unique())}")
    
    if 'date_from_utc' in df.columns:
        print(f"Rango temporal: {df['date_from_utc'].min()} a {df['date_from_utc'].max()}")
    
    print(f"Sensores utilizados: {df['sensor_id'].nunique()}")
    
    print("\nMediciones por parámetro:")
    param_counts = df['parameter_name'].value_counts()
    for param, count in param_counts.items():
        print(f"  - {param}: {count:,} mediciones ({count/len(df)*100:.1f}%)")
