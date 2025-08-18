#!/usr/bin/env python3
"""
Análisis Exploratorio de Datos - Localidades Específicas de Chile
Análisis de datos de calidad del aire para determinar mejores modelos de predicción
"""

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

def cargar_y_explorar_datos():
    """
    Cargar datos y realizar exploración inicial
    """
    print("=== ANÁLISIS EXPLORATORIO DE DATOS - CALIDAD DEL AIRE ===\n")
    
    # Cargar datos
    try:
        df = pd.read_csv('../data/localidades_especificas_20250817_222931.csv')
        print(f"✓ Datos cargados exitosamente")
        print(f"  - Filas: {len(df):,}")
        print(f"  - Columnas: {len(df.columns)}")
    except FileNotFoundError:
        print("✗ No se encontró el archivo de datos")
        return None
    
    # Información básica del dataset
    print(f"\n=== INFORMACIÓN BÁSICA DEL DATASET ===")
    print(f"Columnas disponibles:")
    for i, col in enumerate(df.columns, 1):
        print(f"  {i:2d}. {col}")
    
    # Tipos de datos
    print(f"\n=== TIPOS DE DATOS ===")
    print(df.dtypes)
    
    # Estadísticas descriptivas
    print(f"\n=== ESTADÍSTICAS DESCRIPTIVAS ===")
    print(df.describe())
    
    # Verificar valores nulos
    print(f"\n=== VALORES NULOS ===")
    null_counts = df.isnull().sum()
    for col, count in null_counts.items():
        if count > 0:
            print(f"  {col}: {count} valores nulos ({count/len(df)*100:.1f}%)")
        else:
            print(f"  {col}: Sin valores nulos")
    
    return df

def analizar_estructura_temporal(df):
    """
    Analizar la estructura temporal de los datos
    """
    print(f"\n=== ANÁLISIS DE ESTRUCTURA TEMPORAL ===")
    
    # Convertir fechas
    df['fecha_desde_utc'] = pd.to_datetime(df['fecha_desde_utc'])
    df['fecha_desde_local'] = pd.to_datetime(df['fecha_desde_local'])
    
    # Rango temporal
    fecha_min = df['fecha_desde_utc'].min()
    fecha_max = df['fecha_desde_utc'].max()
    print(f"Rango temporal: {fecha_min} a {fecha_max}")
    print(f"Duración total: {(fecha_max - fecha_min).days} días")
    
    # Frecuencia de mediciones
    df_sorted = df.sort_values('fecha_desde_utc')
    time_diff = df_sorted['fecha_desde_utc'].diff().dropna()
    
    print(f"\nFrecuencia de mediciones:")
    print(f"  - Diferencia mínima: {time_diff.min()}")
    print(f"  - Diferencia máxima: {time_diff.max()}")
    print(f"  - Diferencia promedio: {time_diff.mean()}")
    print(f"  - Diferencia mediana: {time_diff.median()}")
    
    # Verificar si hay patrones estacionales
    df['mes'] = df['fecha_desde_utc'].dt.month
    df['hora'] = df['fecha_desde_utc'].dt.hour
    df['dia_semana'] = df['fecha_desde_utc'].dt.dayofweek
    
    return df

def analizar_parametros_contaminantes(df):
    """
    Analizar los parámetros de contaminantes
    """
    print(f"\n=== ANÁLISIS DE PARÁMETROS DE CONTAMINANTES ===")
    
    # Parámetros únicos
    parametros = df['parametro_nombre'].unique()
    print(f"Parámetros disponibles: {', '.join(parametros)}")
    
    # Estadísticas por parámetro
    for parametro in parametros:
        df_param = df[df['parametro_nombre'] == parametro]
        print(f"\n{parametro}:")
        print(f"  - Mediciones: {len(df_param):,}")
        print(f"  - Valor mínimo: {df_param['valor'].min():.2f}")
        print(f"  - Valor máximo: {df_param['valor'].max():.2f}")
        print(f"  - Valor promedio: {df_param['valor'].mean():.2f}")
        print(f"  - Desviación estándar: {df_param['valor'].std():.2f}")
        print(f"  - Unidad: {df_param['unidad'].iloc[0]}")
    
    return parametros

def analizar_distribucion_geografica(df):
    """
    Analizar la distribución geográfica de las localidades
    """
    print(f"\n=== ANÁLISIS DE DISTRIBUCIÓN GEOGRÁFICA ===")
    
    # Localidades únicas
    localidades = df['localidad_buscada'].unique()
    print(f"Localidades analizadas: {', '.join(localidades)}")
    
    # Estadísticas por localidad
    for localidad in localidades:
        df_loc = df[df['localidad_buscada'] == localidad]
        print(f"\n{localidad}:")
        print(f"  - Mediciones: {len(df_loc):,}")
        print(f"  - Coordenadas: ({df_loc['coordenadas_lat'].iloc[0]:.6f}, {df_loc['coordenadas_lon'].iloc[0]:.6f})")
        print(f"  - Parámetros: {', '.join(df_loc['parametro_nombre'].unique())}")
    
    return localidades

def crear_visualizaciones(df):
    """
    Crear visualizaciones para entender mejor los datos
    """
    print(f"\n=== CREANDO VISUALIZACIONES ===")
    
    # Configurar subplots
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('Análisis Exploratorio - Datos de Calidad del Aire', fontsize=16)
    
    # 1. Distribución de valores por parámetro
    ax1 = axes[0, 0]
    parametros = df['parametro_nombre'].unique()
    for parametro in parametros:
        df_param = df[df['parametro_nombre'] == parametro]
        ax1.hist(df_param['valor'], alpha=0.7, label=parametro, bins=30)
    ax1.set_xlabel('Valor')
    ax1.set_ylabel('Frecuencia')
    ax1.set_title('Distribución de Valores por Parámetro')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. Evolución temporal por parámetro
    ax2 = axes[0, 1]
    for parametro in parametros:
        df_param = df[df['parametro_nombre'] == parametro].sort_values('fecha_desde_utc')
        ax2.plot(df_param['fecha_desde_utc'], df_param['valor'], alpha=0.7, label=parametro, linewidth=1)
    ax2.set_xlabel('Fecha')
    ax2.set_ylabel('Valor')
    ax2.set_title('Evolución Temporal por Parámetro')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
    
    # 3. Boxplot por localidad
    ax3 = axes[1, 0]
    df.boxplot(column='valor', by='localidad_buscada', ax=ax3)
    ax3.set_xlabel('Localidad')
    ax3.set_ylabel('Valor')
    ax3.set_title('Distribución de Valores por Localidad')
    ax3.grid(True, alpha=0.3)
    
    # 4. Correlación entre parámetros (pivot table)
    ax4 = axes[1, 1]
    # Crear pivot table para correlación
    pivot_df = df.pivot_table(
        index='fecha_desde_utc', 
        columns='parametro_nombre', 
        values='valor', 
        aggfunc='mean'
    ).fillna(method='ffill')
    
    if len(pivot_df.columns) > 1:
        correlation_matrix = pivot_df.corr()
        sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0, ax=ax4)
        ax4.set_title('Matriz de Correlación entre Parámetros')
    else:
        ax4.text(0.5, 0.5, 'No hay suficientes parámetros\npara correlación', 
                ha='center', va='center', transform=ax4.transAxes)
        ax4.set_title('Matriz de Correlación')
    
    plt.tight_layout()
    plt.savefig('analisis_exploratorio_visualizaciones.png', dpi=300, bbox_inches='tight')
    print(f"✓ Visualizaciones guardadas en: analisis_exploratorio_visualizaciones.png")
    
    plt.show()

def analizar_estacionariedad(df):
    """
    Analizar la estacionariedad de las series temporales
    """
    print(f"\n=== ANÁLISIS DE ESTACIONARIEDAD ===")
    
    # Crear series temporales por parámetro y localidad
    parametros = df['parametro_nombre'].unique()
    localidades = df['localidad_buscada'].unique()
    
    resultados_estacionariedad = {}
    
    for parametro in parametros:
        for localidad in localidades:
            # Filtrar datos
            df_filtrado = df[(df['parametro_nombre'] == parametro) & 
                           (df['localidad_buscada'] == localidad)].copy()
            
            if len(df_filtrado) > 100:  # Solo si hay suficientes datos
                # Ordenar por fecha
                df_filtrado = df_filtrado.sort_values('fecha_desde_utc')
                
                # Calcular estadísticas móviles
                df_filtrado['media_movil'] = df_filtrado['valor'].rolling(window=24).mean()
                df_filtrado['varianza_movil'] = df_filtrado['valor'].rolling(window=24).var()
                
                # Test de estacionariedad simple (comparar primer y último tercio)
                n = len(df_filtrado)
                primer_tercio = df_filtrado['valor'].iloc[:n//3].mean()
                ultimo_tercio = df_filtrado['valor'].iloc[2*n//3:].mean()
                
                cambio_medio = abs(ultimo_tercio - primer_tercio) / primer_tercio * 100
                
                resultados_estacionariedad[f"{parametro}_{localidad}"] = {
                    'n_mediciones': len(df_filtrado),
                    'primer_tercio_media': primer_tercio,
                    'ultimo_tercio_media': ultimo_tercio,
                    'cambio_porcentual': cambio_medio,
                    'es_estacionario': cambio_medio < 20  # Umbral del 20%
                }
    
    # Mostrar resultados
    print(f"Análisis de estacionariedad por parámetro y localidad:")
    for key, result in resultados_estacionariedad.items():
        print(f"\n{key}:")
        print(f"  - Mediciones: {result['n_mediciones']:,}")
        print(f"  - Cambio medio: {result['cambio_porcentual']:.1f}%")
        print(f"  - Estacionario: {'Sí' if result['es_estacionario'] else 'No'}")
    
    return resultados_estacionariedad

def generar_recomendaciones_modelos(df, resultados_estacionariedad):
    """
    Generar recomendaciones sobre qué modelos aplicar
    """
    print(f"\n=== RECOMENDACIONES DE MODELOS DE PREDICCIÓN ===")
    
    # Análisis de características de los datos
    n_mediciones = len(df)
    n_parametros = df['parametro_nombre'].nunique()
    n_localidades = df['localidad_buscada'].nunique()
    
    print(f"Características de los datos:")
    print(f"  - Total de mediciones: {n_mediciones:,}")
    print(f"  - Parámetros: {n_parametros}")
    print(f"  - Localidades: {n_localidades}")
    
    # Recomendaciones por tipo de modelo
    
    print(f"\n📊 MODELOS DE SERIES TEMPORALES:")
    print(f"  ✅ ARIMA/SARIMA:")
    print(f"    - Aplicable para: Predicción de tendencias y patrones estacionales")
    print(f"    - Requisitos: Datos estacionarios, suficientes observaciones")
    print(f"    - Evaluación: {sum(1 for r in resultados_estacionariedad.values() if r['es_estacionario'])}/{len(resultados_estacionariedad)} series estacionarias")
    
    print(f"\n  ✅ Prophet (Facebook):")
    print(f"    - Aplicable para: Series con patrones estacionales y tendencias")
    print(f"    - Ventajas: Maneja automáticamente estacionalidad, robusto a outliers")
    print(f"    - Recomendado para: Predicciones a mediano plazo (días/semanas)")
    
    print(f"\n  ✅ LSTM/Redes Neuronales:")
    print(f"    - Aplicable para: Patrones complejos no lineales")
    print(f"    - Requisitos: Muchos datos, patrones complejos")
    print(f"    - Evaluación: {'Adecuado' if n_mediciones > 10000 else 'Limitado'} (datos suficientes)")
    
    print(f"\n📈 MODELOS DE REGRESIÓN:")
    print(f"  ✅ Regresión Lineal Múltiple:")
    print(f"    - Aplicable para: Relaciones lineales entre parámetros")
    print(f"    - Ventajas: Interpretable, rápido, bueno para correlaciones")
    print(f"    - Evaluación: {'Adecuado' if n_parametros > 2 else 'Limitado'} (parámetros suficientes)")
    
    print(f"\n  ✅ Random Forest:")
    print(f"    - Aplicable para: Relaciones no lineales complejas")
    print(f"    - Ventajas: Maneja outliers, no requiere normalización")
    print(f"    - Evaluación: {'Excelente' if n_mediciones > 5000 else 'Adecuado'}")
    
    print(f"\n  ✅ XGBoost/LightGBM:")
    print(f"    - Aplicable para: Predicciones de alta precisión")
    print(f"    - Ventajas: Alta precisión, maneja datos faltantes")
    print(f"    - Evaluación: {'Excelente' if n_mediciones > 10000 else 'Adecuado'}")
    
    print(f"\n🎯 RECOMENDACIONES FINALES:")
    
    if n_mediciones > 15000:
        print(f"  🥇 PRIMERA OPCIÓN: XGBoost/LightGBM + LSTM")
        print(f"     - Para máxima precisión en predicciones")
        print(f"     - Combinar con análisis de series temporales")
    elif n_mediciones > 10000:
        print(f"  🥈 SEGUNDA OPCIÓN: Random Forest + Prophet")
        print(f"     - Balance entre precisión y interpretabilidad")
        print(f"     - Bueno para patrones estacionales")
    else:
        print(f"  🥉 TERCERA OPCIÓN: Regresión Lineal + ARIMA")
        print(f"     - Para interpretabilidad y patrones simples")
        print(f"     - Adecuado para datasets más pequeños")
    
    print(f"\n📋 PLAN DE IMPLEMENTACIÓN:")
    print(f"  1. Preprocesamiento: Limpieza, normalización, feature engineering")
    print(f"  2. División temporal: Train/validation/test por fechas")
    print(f"  3. Baseline: Modelo simple como referencia")
    print(f"  4. Modelos avanzados: Implementar recomendaciones principales")
    print(f"  5. Ensemble: Combinar mejores modelos")
    print(f"  6. Validación: Backtesting temporal y métricas de calidad")

def main():
    """
    Función principal del análisis exploratorio
    """
    print("🚀 INICIANDO ANÁLISIS EXPLORATORIO DE DATOS")
    
    # 1. Cargar y explorar datos
    df = cargar_y_explorar_datos()
    if df is None:
        return
    
    # 2. Analizar estructura temporal
    df = analizar_estructura_temporal(df)
    
    # 3. Analizar parámetros de contaminantes
    parametros = analizar_parametros_contaminantes(df)
    
    # 4. Analizar distribución geográfica
    localidades = analizar_distribucion_geografica(df)
    
    # 5. Crear visualizaciones
    crear_visualizaciones(df)
    
    # 6. Analizar estacionariedad
    resultados_estacionariedad = analizar_estacionariedad(df)
    
    # 7. Generar recomendaciones
    generar_recomendaciones_modelos(df, resultados_estacionariedad)
    
    # 8. Guardar resultados del análisis
    print(f"\n=== GUARDANDO RESULTADOS ===")
    
    # Resumen ejecutivo
    resumen = {
        'fecha_analisis': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_mediciones': len(df),
        'parametros_analizados': list(parametros),
        'localidades_analizadas': list(localidades),
        'rango_temporal': f"{df['fecha_desde_utc'].min()} a {df['fecha_desde_utc'].max()}",
        'series_estacionarias': sum(1 for r in resultados_estacionariedad.values() if r['es_estacionario']),
        'total_series': len(resultados_estacionariedad)
    }
    
    # Guardar resumen
    with open('resumen_analisis_exploratorio.txt', 'w', encoding='utf-8') as f:
        f.write("RESUMEN DEL ANÁLISIS EXPLORATORIO\n")
        f.write("=" * 50 + "\n\n")
        for key, value in resumen.items():
            f.write(f"{key.replace('_', ' ').title()}: {value}\n")
    
    print(f"✓ Resumen guardado en: resumen_analisis_exploratorio.txt")
    print(f"\n🎉 ANÁLISIS EXPLORATORIO COMPLETADO")

if __name__ == "__main__":
    main()
