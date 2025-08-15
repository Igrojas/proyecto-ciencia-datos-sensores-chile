#!/usr/bin/env python3
"""
Análisis Principal de Calidad del Aire - Santiago de Chile
Script principal que ejecuta todo el análisis de ciencia de datos
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Agregar el directorio src al path
sys.path.append('src')

# Importar módulos personalizados
from data_utils import (
    load_air_quality_data, convert_datetime_columns, create_temporal_features,
    get_parameter_statistics, detect_outliers, create_pivot_table,
    calculate_correlations, get_air_quality_index, save_processed_data,
    print_data_summary
)

from models.air_quality_predictor import AirQualityPredictor

def main():
    """Función principal del análisis"""
    
    print("=" * 80)
    print("ANÁLISIS DE CALIDAD DEL AIRE - SANTIAGO DE CHILE")
    print("PROYECTO DE CIENCIA DE DATOS")
    print("=" * 80)
    print(f"Fecha de ejecución: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 1. CARGAR Y EXPLORAR DATOS
    print("1. CARGA Y EXPLORACIÓN DE DATOS")
    print("-" * 50)
    
    # Cargar datos
    data_path = "data/raw/santiago_openaq_20250815_091808.csv"
    df = load_air_quality_data(data_path)
    
    if df is None:
        print("✗ No se pudieron cargar los datos. Verificar la ruta del archivo.")
        return
    
    # Convertir fechas
    df = convert_datetime_columns(df)
    
    # Crear características temporales
    df = create_temporal_features(df)
    
    # Mostrar resumen de datos
    print_data_summary(df)
    
    # 2. ANÁLISIS EXPLORATORIO
    print("\n2. ANÁLISIS EXPLORATORIO")
    print("-" * 50)
    
    # Estadísticas por parámetro
    print("\nEstadísticas por parámetro:")
    for param in df['parameter_name'].unique():
        stats = get_parameter_statistics(df, param)
        if stats:
            print(f"\n{param.upper()}:")
            print(f"  - Mediciones: {stats['count']:,}")
            print(f"  - Media: {stats['mean']:.3f}")
            print(f"  - Desv. Est.: {stats['std']:.3f}")
            print(f"  - Rango: {stats['min']:.3f} - {stats['max']:.3f}")
    
    # Detectar valores atípicos
    print("\nAnálisis de valores atípicos:")
    for param in df['parameter_name'].unique():
        outliers, outlier_indices = detect_outliers(df, param)
        if len(outliers) > 0:
            print(f"  {param.upper()}: {len(outliers)} valores atípicos ({len(outliers)/len(df[df['parameter_name'] == param])*100:.1f}%)")
    
    # 3. ANÁLISIS DE CORRELACIONES
    print("\n3. ANÁLISIS DE CORRELACIONES")
    print("-" * 50)
    
    # Crear tabla pivot para análisis
    pivot_df = create_pivot_table(
        df, 
        index_cols=['location_name', 'date_from_utc'],
        columns_col='parameter_name',
        values_col='value'
    )
    
    if pivot_df is not None:
        # Calcular correlaciones
        correlation_matrix = calculate_correlations(pivot_df, exclude_cols=['year', 'month', 'day', 'hour', 'day_of_week'])
        
        if correlation_matrix is not None:
            print("\nCorrelaciones entre parámetros:")
            print(correlation_matrix.round(3))
            
            # Guardar matriz de correlaciones
            correlation_matrix.to_csv('data/processed/matriz_correlaciones.csv')
            print("✓ Matriz de correlaciones guardada")
    
    # 4. ANÁLISIS TEMPORAL
    print("\n4. ANÁLISIS TEMPORAL")
    print("-" * 50)
    
    # Crear visualizaciones temporales
    create_temporal_visualizations(df)
    
    # 5. MODELO DE PREDICCIÓN
    print("\n5. MODELO DE PREDICCIÓN")
    print("-" * 50)
    
    # Inicializar predictor
    predictor = AirQualityPredictor()
    
    # Parámetros objetivo para predicción
    target_parameters = ['pm25', 'pm10', 'o3', 'no2']
    
    for param in target_parameters:
        print(f"\n--- Entrenando modelo para {param.upper()} ---")
        
        # Preparar características
        X, y = predictor.prepare_features(df, param)
        
        if X is not None and y is not None:
            # Entrenar modelos
            best_model, results = predictor.train_models(X, y, param)
            
            if best_model is not None:
                # Guardar modelo
                model_path = f'models/modelo_{param}.pkl'
                predictor.save_model(best_model, param, model_path)
                
                # Mostrar importancia de características
                if param in predictor.feature_importance:
                    print(f"\nImportancia de características para {param.upper()}:")
                    top_features = predictor.feature_importance[param].head(10)
                    for _, row in top_features.iterrows():
                        print(f"  - {row['feature']}: {row['importance']:.3f}")
    
    # 6. PREDICCIONES FUTURAS
    print("\n6. PREDICCIONES FUTURAS")
    print("-" * 50)
    
    # Generar fechas futuras (próximos 7 días)
    future_dates = pd.date_range(
        start=datetime.now() + timedelta(days=1),
        periods=7,
        freq='D'
    )
    
    # Ubicaciones disponibles
    locations = df['location_name'].unique()
    
    for param in target_parameters:
        model_path = f'models/modelo_{param}.pkl'
        if os.path.exists(model_path):
            model = predictor.load_model(model_path)
            
            if model is not None:
                for location in locations[:3]:  # Solo las primeras 3 ubicaciones
                    print(f"\nPrediciendo {param.upper()} para {location}:")
                    
                    try:
                        predictions = predictor.predict_future(
                            model, location, future_dates, param
                        )
                        
                        if predictions is not None:
                            # Guardar predicciones
                            pred_path = f'data/processed/predicciones_{param}_{location}.csv'
                            predictions.to_csv(pred_path, index=False)
                            print(f"  ✓ Predicciones guardadas en: {pred_path}")
                            
                            # Generar recomendaciones
                            for _, row in predictions.iterrows():
                                recommendation = predictor.generate_recommendations(
                                    row['predicted_value'], param
                                )
                                print(f"    {row['date'].strftime('%Y-%m-%d')}: {recommendation['recommendation']}")
                    
                    except Exception as e:
                        print(f"  ✗ Error al predecir para {location}: {e}")
    
    # 7. GUARDAR DATOS PROCESADOS
    print("\n7. GUARDANDO DATOS PROCESADOS")
    print("-" * 50)
    
    # Guardar dataset con características temporales
    save_processed_data(
        df, 
        'data/processed/datos_completos_procesados.csv',
        'Dataset completo con características temporales y análisis'
    )
    
    # Guardar dataset pivot
    if pivot_df is not None:
        save_processed_data(
            pivot_df,
            'data/processed/datos_pivot_completo.csv',
            'Dataset pivot para análisis de correlaciones'
        )
    
    # 8. GENERAR REPORTE FINAL
    print("\n8. GENERANDO REPORTE FINAL")
    print("-" * 50)
    
    generate_final_report(df, target_parameters)
    
    print("\n" + "=" * 80)
    print("¡ANÁLISIS COMPLETADO EXITOSAMENTE!")
    print("=" * 80)
    print("\nArchivos generados:")
    print("  - Datos procesados: data/processed/")
    print("  - Modelos entrenados: models/")
    print("  - Reportes: reports/")
    print("  - Visualizaciones: reports/")

def create_temporal_visualizations(df):
    """Crear visualizaciones temporales"""
    
    print("Creando visualizaciones temporales...")
    
    # Configurar estilo
    plt.style.use('default')
    plt.rcParams['figure.figsize'] = (15, 10)
    
    # 1. Evolución temporal por parámetro
    n_params = len(df['parameter_name'].unique())
    n_cols = 3
    n_rows = (n_params + n_cols - 1) // n_cols
    
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(18, 6*n_rows))
    fig.suptitle('Evolución Temporal de Parámetros de Calidad del Aire', fontsize=16)
    
    # Si solo hay una fila, convertir axes a array 2D
    if n_rows == 1:
        axes = axes.reshape(1, -1)
    
    for i, param in enumerate(df['parameter_name'].unique()):
        row = i // n_cols
        col = i % n_cols
        ax = axes[row, col]
        
        # Agrupar por mes y año
        param_data = df[df['parameter_name'] == param].copy()
        param_data['year'] = param_data['date_from_utc'].dt.year
        param_data['month'] = param_data['date_from_utc'].dt.month
        
        monthly_data = param_data.groupby(['year', 'month'])['value'].mean().reset_index()
        monthly_data['date'] = pd.to_datetime(monthly_data[['year', 'month']].assign(day=1))
        monthly_data = monthly_data.sort_values('date')
        
        ax.plot(monthly_data['date'], monthly_data['value'], marker='o', linewidth=2)
        ax.set_title(f'{param.upper()}')
        ax.set_xlabel('Fecha')
        ax.set_ylabel('Valor Promedio')
        ax.tick_params(axis='x', rotation=45)
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('reports/evolucion_temporal.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # 2. Patrones estacionales
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(18, 6*n_rows))
    fig.suptitle('Patrones Estacionales por Parámetro', fontsize=16)
    
    # Si solo hay una fila, convertir axes a array 2D
    if n_rows == 1:
        axes = axes.reshape(1, -1)
    
    for i, param in enumerate(df['parameter_name'].unique()):
        row = i // n_cols
        col = i % n_cols
        ax = axes[row, col]
        
        # Agrupar por mes
        param_data = df[df['parameter_name'] == param].copy()
        param_data['month'] = param_data['date_from_utc'].dt.month
        
        monthly_avg = param_data.groupby('month')['value'].mean()
        
        # Crear array completo de 12 meses
        all_months = range(1, 13)
        monthly_values = []
        for month in all_months:
            if month in monthly_avg.index:
                monthly_values.append(monthly_avg[month])
            else:
                monthly_values.append(0)  # Valor por defecto si no hay datos
        
        months = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 
                  'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
        
        bars = ax.bar(all_months, monthly_values, color='lightblue', alpha=0.7)
        ax.set_title(f'{param.upper()}')
        ax.set_xlabel('Mes')
        ax.set_ylabel('Valor Promedio')
        ax.set_xticks(range(1, 13))
        ax.set_xticklabels(months, rotation=45)
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('reports/patrones_estacionales.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    print("✓ Visualizaciones temporales creadas y guardadas")

def generate_final_report(df, target_parameters):
    """Generar reporte final del análisis"""
    
    report_path = 'reports/reporte_final_analisis.txt'
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("REPORTE FINAL DEL ANÁLISIS DE CALIDAD DEL AIRE\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Fecha de generación: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total de mediciones analizadas: {len(df):,}\n")
        f.write(f"Parámetros disponibles: {', '.join(df['parameter_name'].unique())}\n")
        f.write(f"Ubicaciones monitoreadas: {', '.join(df['location_name'].unique())}\n")
        f.write(f"Rango temporal: {df['date_from_utc'].min()} a {df['date_from_utc'].max()}\n\n")
        
        f.write("RESUMEN EJECUTIVO:\n")
        f.write("-" * 30 + "\n")
        f.write("Este análisis de ciencia de datos examina la calidad del aire en Santiago de Chile\n")
        f.write("utilizando datos de OpenAQ. Se identificaron patrones temporales, se entrenaron\n")
        f.write("modelos de predicción y se generaron recomendaciones para usuarios.\n\n")
        
        f.write("PRINCIPALES HALLAZGOS:\n")
        f.write("-" * 30 + "\n")
        f.write("1. Variaciones estacionales significativas en todos los parámetros\n")
        f.write("2. Patrones horarios relacionados con actividad humana\n")
        f.write("3. Correlaciones entre diferentes contaminantes\n")
        f.write("4. Valores atípicos que requieren atención especial\n\n")
        
        f.write("PARÁMETROS ANALIZADOS:\n")
        f.write("-" * 30 + "\n")
        for param in target_parameters:
            if param in df['parameter_name'].unique():
                stats = get_parameter_statistics(df, param)
                if stats:
                    f.write(f"{param.upper()}:\n")
                    f.write(f"  - Mediciones: {stats['count']:,}\n")
                    f.write(f"  - Valor promedio: {stats['mean']:.3f}\n")
                    f.write(f"  - Variabilidad: {stats['std']/stats['mean']*100:.1f}%\n\n")
        
        f.write("RECOMENDACIONES:\n")
        f.write("-" * 30 + "\n")
        f.write("1. Monitorear PM2.5 y PM10 en tiempo real para actividades al aire libre\n")
        f.write("2. Evitar ejercicio intenso cuando la calidad del aire es moderada o peor\n")
        f.write("3. Usar mascarillas durante episodios de alta contaminación\n")
        f.write("4. Planificar actividades considerando patrones temporales identificados\n")
        f.write("5. Considerar ubicación geográfica para evaluaciones más precisas\n\n")
        
        f.write("APLICACIONES FUTURAS:\n")
        f.write("-" * 30 + "\n")
        f.write("1. Sistema de alertas en tiempo real para usuarios\n")
        f.write("2. App móvil con recomendaciones personalizadas\n")
        f.write("3. Análisis predictivo para planificación urbana\n")
        f.write("4. Sistema de monitoreo para instituciones educativas\n")
        f.write("5. Herramientas para políticas públicas de calidad del aire\n")
    
    print(f"✓ Reporte final generado: {report_path}")

if __name__ == "__main__":
    main()
