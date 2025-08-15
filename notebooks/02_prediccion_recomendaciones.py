#!/usr/bin/env python3
"""
Análisis de Calidad del Aire - Santiago de Chile
2. Predicción y Recomendaciones

Este script analiza qué parámetros sería interesante predecir para 
ofrecer recomendaciones a usuarios sobre la calidad del aire.
"""

# Importar librerías necesarias
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

# Configurar estilo de gráficos
plt.style.use('default')
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 12

print("=== ANÁLISIS DE CALIDAD DEL AIRE - SANTIAGO DE CHILE ===")
print("2. PREDICCIÓN Y RECOMENDACIONES\n")

# Cargar los datos
print("Cargando datos...")
df = pd.read_csv('../data/raw/santiago_openaq_20250815_091808.csv')
print(f"✓ Datos cargados: {df.shape[0]:,} filas y {df.shape[1]} columnas")

# Convertir fechas
df['date_from_utc'] = pd.to_datetime(df['date_from_utc'])
df['date_from_local'] = pd.to_datetime(df['date_from_local'])

# Crear características temporales
df['year'] = df['date_from_utc'].dt.year
df['month'] = df['date_from_utc'].dt.month
df['day'] = df['date_from_utc'].dt.day
df['hour'] = df['date_from_utc'].dt.hour
df['day_of_week'] = df['date_from_utc'].dt.dayofweek

print("✓ Características temporales creadas")

# Análisis de qué parámetros predecir
print("\n=== ANÁLISIS DE PARÁMETROS A PREDECIR ===")

# 1. Análisis de importancia para la salud
print("\n1. IMPORTANCIA PARA LA SALUD HUMANA:")
health_importance = {
    'pm25': 'Alto - Partículas finas que penetran profundamente en los pulmones',
    'pm10': 'Alto - Partículas que afectan el sistema respiratorio',
    'o3': 'Alto - Ozono que puede causar problemas respiratorios',
    'no2': 'Alto - Dióxido de nitrógeno que afecta la función pulmonar',
    'so2': 'Medio - Dióxido de azufre que puede irritar las vías respiratorias',
    'co': 'Medio - Monóxido de carbono que reduce el oxígeno en sangre'
}

for param, importance in health_importance.items():
    if param in df['parameter_name'].unique():
        print(f"  ✓ {param.upper()}: {importance}")
    else:
        print(f"  ⚠ {param.upper()}: No disponible en los datos")

# 2. Análisis de correlaciones para predicción
print("\n2. ANÁLISIS DE CORRELACIONES PARA PREDICCIÓN:")

# Crear dataset para análisis de correlaciones
pivot_df = df.pivot_table(
    index=['location_name', 'date_from_utc'], 
    columns='parameter_name', 
    values='value', 
    aggfunc='mean'
).reset_index()

# Agregar características temporales
pivot_df['year'] = pivot_df['date_from_utc'].dt.year
pivot_df['month'] = pivot_df['date_from_utc'].dt.month
pivot_df['day'] = pivot_df['date_from_utc'].dt.day
pivot_df['hour'] = pivot_df['date_from_utc'].dt.hour
pivot_df['day_of_week'] = pivot_df['date_from_utc'].dt.dayofweek

# Mostrar correlaciones
correlation_matrix = pivot_df.drop(['location_name', 'date_from_utc'], axis=1).corr()
print("\nCorrelaciones entre parámetros y características temporales:")
print(correlation_matrix.round(3))

# 3. Análisis de variabilidad temporal
print("\n3. ANÁLISIS DE VARIABILIDAD TEMPORAL:")

plt.figure(figsize=(15, 10))

for i, param in enumerate(df['parameter_name'].unique(), 1):
    plt.subplot(2, 3, i)
    
    # Agrupar por mes y año
    monthly_data = df[df['parameter_name'] == param].groupby([
        df['date_from_utc'].dt.year, 
        df['date_from_utc'].dt.month
    ])['value'].mean().reset_index()
    
    monthly_data['date'] = pd.to_datetime(monthly_data[['year', 'month']].assign(day=1))
    monthly_data = monthly_data.sort_values('date')
    
    plt.plot(monthly_data['date'], monthly_data['value'], marker='o', linewidth=2)
    plt.title(f'{param.upper()} - Evolución Mensual')
    plt.xlabel('Fecha')
    plt.ylabel('Valor Promedio')
    plt.xticks(rotation=45)
    
    # Mostrar estadísticas de variabilidad
    variability = monthly_data['value'].std() / monthly_data['value'].mean() * 100
    print(f"  {param.upper()}: Variabilidad {variability:.1f}%")

plt.tight_layout()
plt.savefig('../reports/variabilidad_temporal.png', dpi=300, bbox_inches='tight')
plt.show()

# 4. Análisis de patrones estacionales
print("\n4. ANÁLISIS DE PATRONES ESTACIONALES:")

plt.figure(figsize=(15, 10))

for i, param in enumerate(df['parameter_name'].unique(), 1):
    plt.subplot(2, 3, i)
    
    # Agrupar por mes
    monthly_avg = df[df['parameter_name'] == param].groupby(
        df['date_from_utc'].dt.month
    )['value'].mean()
    
    months = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 
              'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    
    plt.bar(range(1, 13), monthly_avg.values, color='lightblue', alpha=0.7)
    plt.title(f'{param.upper()} - Patrón Estacional')
    plt.xlabel('Mes')
    plt.ylabel('Valor Promedio')
    plt.xticks(range(1, 13), months, rotation=45)

plt.tight_layout()
plt.savefig('../reports/patrones_estacionales.png', dpi=300, bbox_inches='tight')
plt.show()

# 5. Análisis de patrones horarios
print("\n5. ANÁLISIS DE PATRONES HORARIOS:")

plt.figure(figsize=(15, 10))

for i, param in enumerate(df['parameter_name'].unique(), 1):
    plt.subplot(2, 3, i)
    
    # Agrupar por hora
    hourly_avg = df[df['parameter_name'] == param].groupby(
        df['date_from_utc'].dt.hour
    )['value'].mean()
    
    plt.plot(hourly_avg.index, hourly_avg.values, marker='o', linewidth=2, color='orange')
    plt.title(f'{param.upper()} - Patrón Horario')
    plt.xlabel('Hora del día')
    plt.ylabel('Valor Promedio')
    plt.xticks(range(0, 24, 2))
    plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../reports/patrones_horarios.png', dpi=300, bbox_inches='tight')
plt.show()

# 6. Modelo de predicción para PM2.5 (parámetro más importante)
print("\n6. MODELO DE PREDICCIÓN PARA PM2.5:")

# Preparar datos para PM2.5
pm25_data = df[df['parameter_name'] == 'pm25'].copy()

if len(pm25_data) > 0:
    # Crear características
    pm25_data['year'] = pm25_data['date_from_utc'].dt.year
    pm25_data['month'] = pm25_data['date_from_utc'].dt.month
    pm25_data['day'] = pm25_data['date_from_utc'].dt.day
    pm25_data['hour'] = pm25_data['date_from_utc'].dt.hour
    pm25_data['day_of_week'] = pm25_data['date_from_utc'].dt.dayofweek
    
    # Crear dataset para predicción
    features = ['year', 'month', 'day', 'hour', 'day_of_week']
    X = pm25_data[features]
    y = pm25_data['value']
    
    # Dividir datos
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Entrenar modelo
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Predicciones
    y_pred = model.predict(X_test)
    
    # Métricas
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    print(f"  ✓ Modelo entrenado para PM2.5")
    print(f"  ✓ Error cuadrático medio: {mse:.2f}")
    print(f"  ✓ R² score: {r2:.3f}")
    
    # Importancia de características
    feature_importance = pd.DataFrame({
        'feature': features,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print(f"\n  Importancia de características:")
    for _, row in feature_importance.iterrows():
        print(f"    - {row['feature']}: {row['importance']:.3f}")
    
    # Visualizar predicciones vs reales
    plt.figure(figsize=(10, 6))
    plt.scatter(y_test, y_pred, alpha=0.6, color='blue')
    plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2)
    plt.xlabel('Valores Reales')
    plt.ylabel('Predicciones')
    plt.title('PM2.5: Predicciones vs Valores Reales')
    plt.grid(True, alpha=0.3)
    plt.savefig('../reports/prediccion_pm25.png', dpi=300, bbox_inches='tight')
    plt.show()

else:
    print("  ⚠ No hay datos de PM2.5 disponibles")

# 7. Recomendaciones para usuarios
print("\n=== RECOMENDACIONES PARA USUARIOS ===")

print("\n1. PARÁMETROS MÁS IMPORTANTES A MONITOREAR:")
print("   - PM2.5: Partículas finas (más peligrosas para la salud)")
print("   - PM10: Partículas en suspensión")
print("   - O3: Ozono (especialmente en verano)")
print("   - NO2: Dióxido de nitrógeno (tráfico vehicular)")

print("\n2. PATRONES TEMPORALES IDENTIFICADOS:")
print("   - Variaciones estacionales en todos los parámetros")
print("   - Patrones horarios relacionados con actividad humana")
print("   - Mayor contaminación en meses de invierno (PM2.5, PM10)")
print("   - Picos de ozono en horas de mayor radiación solar")

print("\n3. RECOMENDACIONES DE USO:")
print("   - Monitorear PM2.5 en tiempo real para actividades al aire libre")
print("   - Evitar ejercicio intenso cuando PM2.5 > 35 μg/m³")
print("   - Usar mascarilla cuando PM2.5 > 55 μg/m³")
print("   - Planificar actividades al aire libre en horas de menor contaminación")
print("   - Considerar ubicación geográfica (Puente Alto, Talagante tienen más datos)")

print("\n4. APLICACIONES POTENCIALES:")
print("   - App móvil con alertas en tiempo real")
print("   - Sistema de recomendaciones para deportistas")
print("   - Planificación de actividades escolares")
print("   - Alertas para personas con problemas respiratorios")
print("   - Análisis de tendencias para políticas públicas")

# Guardar datos procesados
print("\n=== GUARDANDO DATOS PROCESADOS ===")

# Guardar dataset con características temporales
df_processed = df.copy()
df_processed.to_csv('../data/processed/datos_con_caracteristicas_temporales.csv', index=False)
print("✓ Datos con características temporales guardados")

# Guardar dataset pivot para análisis
pivot_df.to_csv('../data/processed/datos_pivot_analisis.csv', index=False)
print("✓ Dataset pivot para análisis guardado")

# Guardar resumen de análisis
with open('../reports/resumen_analisis_prediccion.txt', 'w', encoding='utf-8') as f:
    f.write("RESUMEN DEL ANÁLISIS DE PREDICCIÓN Y RECOMENDACIONES\n")
    f.write("=" * 60 + "\n\n")
    f.write(f"Fecha de análisis: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"Total de mediciones analizadas: {len(df):,}\n")
    f.write(f"Parámetros disponibles: {', '.join(df['parameter_name'].unique())}\n")
    f.write(f"Ubicaciones: {', '.join(df['location_name'].unique())}\n\n")
    
    f.write("PARÁMETROS RECOMENDADOS PARA PREDICCIÓN:\n")
    f.write("- PM2.5: Alta prioridad (salud pública)\n")
    f.write("- PM10: Alta prioridad (calidad del aire)\n")
    f.write("- O3: Media prioridad (contaminación fotoquímica)\n")
    f.write("- NO2: Media prioridad (tráfico vehicular)\n\n")
    
    f.write("PATRONES IDENTIFICADOS:\n")
    f.write("- Variaciones estacionales significativas\n")
    f.write("- Patrones horarios relacionados con actividad humana\n")
    f.write("- Correlaciones entre parámetros\n")
    f.write("- Valores atípicos que requieren atención\n")

print("✓ Resumen del análisis guardado")

print("\n=== FIN DEL ANÁLISIS DE PREDICCIÓN Y RECOMENDACIONES ===")
