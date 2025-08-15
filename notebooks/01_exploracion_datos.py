#!/usr/bin/env python3
"""
Análisis de Calidad del Aire - Santiago de Chile
1. Exploración de Datos

Este script explora los datos de calidad del aire obtenidos de OpenAQ 
para Santiago de Chile y sus alrededores.
"""

# Importar librerías necesarias
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Configurar estilo de gráficos
plt.style.use('default')
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 12

print("=== ANÁLISIS DE CALIDAD DEL AIRE - SANTIAGO DE CHILE ===")
print("1. EXPLORACIÓN DE DATOS\n")

# Cargar los datos
print("Cargando datos...")
df = pd.read_csv('../data/raw/santiago_openaq_20250815_091808.csv')
print(f"✓ Datos cargados: {df.shape[0]:,} filas y {df.shape[1]} columnas")

# Información general del dataset
print("\n=== INFORMACIÓN GENERAL DEL DATASET ===")
print(f"\nTipos de datos:")
print(df.dtypes)
print(f"\nValores únicos por columna:")
for col in df.columns:
    print(f"  {col}: {df[col].nunique()} valores únicos")

# Convertir columnas de fecha
print("\n=== CONVERSIÓN DE FECHAS ===")
df['date_from_utc'] = pd.to_datetime(df['date_from_utc'])
df['date_from_local'] = pd.to_datetime(df['date_from_local'])
df['date_to_utc'] = pd.to_datetime(df['date_to_utc'])
df['date_to_local'] = pd.to_datetime(df['date_to_local'])

print("✓ Columnas de fecha convertidas correctamente")
print(f"Rango de fechas:")
print(f"  Desde: {df['date_from_utc'].min()}")
print(f"  Hasta: {df['date_from_utc'].max()}")

# Análisis de parámetros de calidad del aire
print("\n=== ANÁLISIS DE PARÁMETROS ===")
param_stats = df.groupby('parameter_name').agg({
    'value': ['count', 'mean', 'std', 'min', 'max'],
    'unit': 'first'
}).round(3)

print("Estadísticas por parámetro:")
print(param_stats)

# Análisis por ubicación
print("\n=== ANÁLISIS POR UBICACIÓN ===")
location_stats = df.groupby('location_name').agg({
    'parameter_name': 'nunique',
    'value': 'count',
    'sensor_id': 'nunique'
}).rename(columns={
    'parameter_name': 'num_parameters',
    'value': 'total_measurements',
    'sensor_id': 'num_sensors'
})

print("Estadísticas por ubicación:")
print(location_stats.sort_values('total_measurements', ascending=False))

# Crear visualizaciones
print("\n=== CREANDO VISUALIZACIONES ===")

# 1. Distribución de parámetros
plt.figure(figsize=(15, 10))

plt.subplot(2, 2, 1)
df['parameter_name'].value_counts().plot(kind='bar', color='skyblue')
plt.title('Distribución de Parámetros')
plt.xlabel('Parámetro')
plt.ylabel('Cantidad de Mediciones')
plt.xticks(rotation=45)

plt.subplot(2, 2, 2)
df['location_name'].value_counts().plot(kind='bar', color='lightcoral')
plt.title('Distribución por Ubicación')
plt.xlabel('Ubicación')
plt.ylabel('Cantidad de Mediciones')
plt.xticks(rotation=45)

plt.subplot(2, 2, 3)
df.groupby('parameter_name')['value'].mean().plot(kind='bar', color='lightgreen')
plt.title('Valor Promedio por Parámetro')
plt.xlabel('Parámetro')
plt.ylabel('Valor Promedio')
plt.xticks(rotation=45)

plt.subplot(2, 2, 4)
df['date_from_utc'].dt.year.value_counts().sort_index().plot(kind='line', marker='o', color='orange')
plt.title('Evolución Temporal por Año')
plt.xlabel('Año')
plt.ylabel('Cantidad de Mediciones')

plt.tight_layout()
plt.savefig('../reports/distribucion_parametros.png', dpi=300, bbox_inches='tight')
plt.show()

# 2. Análisis de correlaciones
print("\n=== ANÁLISIS DE CORRELACIONES ===")

# Crear pivot table para análisis de correlaciones
pivot_df = df.pivot_table(
    index=['location_name', 'date_from_utc'], 
    columns='parameter_name', 
    values='value', 
    aggfunc='mean'
).reset_index()

# Mostrar correlaciones
correlation_matrix = pivot_df.drop(['location_name', 'date_from_utc'], axis=1).corr()
print("Matriz de correlaciones:")
print(correlation_matrix.round(3))

# Visualizar correlaciones
plt.figure(figsize=(10, 8))
sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0, 
            square=True, linewidths=0.5)
plt.title('Correlaciones entre Parámetros de Calidad del Aire')
plt.tight_layout()
plt.savefig('../reports/correlaciones_parametros.png', dpi=300, bbox_inches='tight')
plt.show()

# 3. Análisis de valores atípicos
print("\n=== ANÁLISIS DE VALORES ATÍPICOS ===")

plt.figure(figsize=(15, 10))
for i, param in enumerate(df['parameter_name'].unique(), 1):
    plt.subplot(2, 3, i)
    param_data = df[df['parameter_name'] == param]['value']
    plt.boxplot(param_data)
    plt.title(f'{param}')
    plt.ylabel('Valor')
    
    # Mostrar estadísticas
    Q1 = param_data.quantile(0.25)
    Q3 = param_data.quantile(0.75)
    IQR = Q3 - Q1
    outliers = param_data[(param_data < Q1 - 1.5*IQR) | (param_data > Q3 + 1.5*IQR)]
    print(f"{param}: {len(outliers)} valores atípicos ({len(outliers)/len(param_data)*100:.1f}%)")

plt.tight_layout()
plt.savefig('../reports/valores_atipicos.png', dpi=300, bbox_inches='tight')
plt.show()

# Resumen de hallazgos
print("\n=== RESUMEN DE HALLAZGOS ===")
print(f"\n1. Total de mediciones: {len(df):,}")
print(f"2. Parámetros disponibles: {', '.join(df['parameter_name'].unique())}")
print(f"3. Ubicaciones monitoreadas: {', '.join(df['location_name'].unique())}")
print(f"4. Rango temporal: {df['date_from_utc'].min().strftime('%Y-%m-%d')} a {df['date_from_utc'].max().strftime('%Y-%m-%d')}")
print(f"5. Sensores utilizados: {df['sensor_id'].nunique()}")

print("\n6. Parámetros más medidos:")
param_counts = df['parameter_name'].value_counts()
for param, count in param_counts.items():
    print(f"   - {param}: {count:,} mediciones ({count/len(df)*100:.1f}%)")

print("\n7. Ubicaciones con más datos:")
location_counts = df['location_name'].value_counts()
for location, count in location_counts.head().items():
    print(f"   - {location}: {count:,} mediciones ({count/len(df)*100:.1f}%)")

print("\n=== FIN DEL ANÁLISIS EXPLORATORIO ===")
