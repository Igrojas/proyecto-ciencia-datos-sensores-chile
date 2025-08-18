#!/usr/bin/env python3
"""
Implementación de Modelos de Predicción - Calidad del Aire
Comparación de diferentes enfoques para predicción y recomendaciones
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Modelos de Machine Learning
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit

# Modelos de Series Temporales
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf

# Configuración
plt.style.use('default')
sns.set_palette("husl")

def cargar_y_preparar_datos():
    """
    Cargar y preparar datos para modelado
    """
    print("=== PREPARANDO DATOS PARA MODELADO ===\n")
    
    try:
        df = pd.read_csv('../data/localidades_especificas_20250817_222931.csv')
        print(f"✓ Datos cargados: {len(df):,} mediciones")
    except FileNotFoundError:
        print("✗ No se encontró el archivo de datos")
        return None
    
    # Convertir fechas
    df['fecha_desde_utc'] = pd.to_datetime(df['fecha_desde_utc'])
    
    # Crear features temporales
    df['mes'] = df['fecha_desde_utc'].dt.month
    df['hora'] = df['fecha_desde_utc'].dt.hour
    df['dia_semana'] = df['fecha_desde_utc'].dt.dayofweek
    df['dia_ano'] = df['fecha_desde_utc'].dt.dayofyear
    
    # Ordenar por fecha
    df = df.sort_values('fecha_desde_utc').reset_index(drop=True)
    
    print(f"✓ Datos preparados con features temporales")
    return df

def crear_dataset_modelado(df, parametro='pm25', localidad='Indura'):
    """
    Crear dataset específico para un parámetro y localidad
    """
    print(f"\n=== CREANDO DATASET PARA {parametro} en {localidad} ===")
    
    # Filtrar datos
    df_filtrado = df[(df['parametro_nombre'] == parametro) & 
                     (df['localidad_buscada'] == localidad)].copy()
    
    if len(df_filtrado) < 100:
        print(f"⚠ Datos insuficientes para {parametro} en {localidad}")
        return None, None, None
    
    # Crear pivot table para tener una serie temporal continua
    pivot_df = df_filtrado.pivot_table(
        index='fecha_desde_utc',
        values='valor',
        aggfunc='mean'
    ).fillna(method='ffill').fillna(method='bfill')
    
    # Crear features adicionales
    pivot_df['mes'] = pivot_df.index.month
    pivot_df['hora'] = pivot_df.index.hour
    pivot_df['dia_semana'] = pivot_df.index.dayofweek
    pivot_df['dia_ano'] = pivot_df.index.dayofyear
    
    # Crear lags (valores anteriores)
    for lag in [1, 2, 3, 6, 12, 24]:
        pivot_df[f'lag_{lag}'] = pivot_df['valor'].shift(lag)
    
    # Crear medias móviles
    for window in [3, 6, 12, 24]:
        pivot_df[f'media_movil_{window}'] = pivot_df['valor'].rolling(window=window).mean()
    
    # Eliminar filas con valores nulos
    pivot_df = pivot_df.dropna()
    
    print(f"✓ Dataset creado: {len(pivot_df)} observaciones")
    print(f"  - Features: {len(pivot_df.columns)}")
    print(f"  - Rango: {pivot_df.index.min()} a {pivot_df.index.max()}")
    
    return pivot_df, parametro, localidad

def dividir_datos_temporales(df, test_size=0.2, val_size=0.2):
    """
    Dividir datos temporalmente (no aleatoriamente)
    """
    n = len(df)
    n_test = int(n * test_size)
    n_val = int(n * val_size)
    
    # División temporal
    train_df = df.iloc[:-n_test-n_val]
    val_df = df.iloc[-n_test-n_val:-n_test]
    test_df = df.iloc[-n_test:]
    
    print(f"✓ División temporal:")
    print(f"  - Train: {len(train_df)} observaciones ({len(train_df)/n*100:.1f}%)")
    print(f"  - Validation: {len(val_df)} observaciones ({len(val_df)/n*100:.1f}%)")
    print(f"  - Test: {len(test_df)} observaciones ({len(test_df)/n*100:.1f}%)")
    
    return train_df, val_df, test_df

def modelo_regresion_lineal(train_df, val_df, test_df):
    """
    Implementar modelo de regresión lineal
    """
    print(f"\n=== MODELO: REGRESIÓN LINEAL ===")
    
    # Preparar features
    feature_cols = [col for col in train_df.columns if col != 'valor']
    X_train = train_df[feature_cols]
    y_train = train_df['valor']
    X_val = val_df[feature_cols]
    y_val = val_df['valor']
    X_test = test_df[feature_cols]
    y_test = test_df['valor']
    
    # Normalizar features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)
    
    # Entrenar modelo
    modelo = LinearRegression()
    modelo.fit(X_train_scaled, y_train)
    
    # Predicciones
    y_pred_train = modelo.predict(X_train_scaled)
    y_pred_val = modelo.predict(X_val_scaled)
    y_pred_test = modelo.predict(X_test_scaled)
    
    # Métricas
    metricas = {
        'train': {
            'mse': mean_squared_error(y_train, y_pred_train),
            'mae': mean_absolute_error(y_train, y_pred_train),
            'r2': r2_score(y_train, y_pred_train)
        },
        'val': {
            'mse': mean_squared_error(y_val, y_pred_val),
            'mae': mean_absolute_error(y_val, y_pred_val),
            'r2': r2_score(y_val, y_pred_val)
        },
        'test': {
            'mse': mean_squared_error(y_test, y_pred_test),
            'mae': mean_absolute_error(y_test, y_pred_test),
            'r2': r2_score(y_test, y_pred_test)
        }
    }
    
    print(f"✓ Modelo entrenado")
    print(f"  - R² Train: {metricas['train']['r2']:.4f}")
    print(f"  - R² Validation: {metricas['val']['r2']:.4f}")
    print(f"  - R² Test: {metricas['test']['r2']:.4f}")
    
    return modelo, metricas, (y_pred_train, y_pred_val, y_pred_test)

def modelo_random_forest(train_df, val_df, test_df):
    """
    Implementar modelo Random Forest
    """
    print(f"\n=== MODELO: RANDOM FOREST ===")
    
    # Preparar features
    feature_cols = [col for col in train_df.columns if col != 'valor']
    X_train = train_df[feature_cols]
    y_train = train_df['valor']
    X_val = val_df[feature_cols]
    y_val = val_df['valor']
    X_test = test_df[feature_cols]
    y_test = test_df['valor']
    
    # Entrenar modelo
    modelo = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    modelo.fit(X_train, y_train)
    
    # Predicciones
    y_pred_train = modelo.predict(X_train)
    y_pred_val = modelo.predict(X_val)
    y_pred_test = modelo.predict(X_test)
    
    # Métricas
    metricas = {
        'train': {
            'mse': mean_squared_error(y_train, y_pred_train),
            'mae': mean_absolute_error(y_train, y_pred_train),
            'r2': r2_score(y_train, y_pred_train)
        },
        'val': {
            'mse': mean_squared_error(y_val, y_pred_val),
            'mae': mean_absolute_error(y_val, y_pred_val),
            'r2': r2_score(y_val, y_pred_val)
        },
        'test': {
            'mse': mean_squared_error(y_test, y_pred_test),
            'mae': mean_absolute_error(y_test, y_pred_test),
            'r2': r2_score(y_test, y_pred_test)
        }
    }
    
    print(f"✓ Modelo entrenado")
    print(f"  - R² Train: {metricas['train']['r2']:.4f}")
    print(f"  - R² Validation: {metricas['val']['r2']:.4f}")
    print(f"  - R² Test: {metricas['test']['r2']:.4f}")
    
    # Feature importance
    feature_importance = pd.DataFrame({
        'feature': feature_cols,
        'importance': modelo.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print(f"\nTop 5 features más importantes:")
    for i, row in feature_importance.head().iterrows():
        print(f"  - {row['feature']}: {row['importance']:.4f}")
    
    return modelo, metricas, (y_pred_train, y_pred_val, y_pred_test), feature_importance

def modelo_arima(train_df, val_df, test_df):
    """
    Implementar modelo ARIMA
    """
    print(f"\n=== MODELO: ARIMA ===")
    
    # Usar solo la serie temporal del valor
    serie_train = train_df['valor']
    serie_val = val_df['valor']
    serie_test = test_df['valor']
    
    try:
        # Determinar orden ARIMA (simplificado)
        # En producción se usaría auto_arima o grid search
        p, d, q = 1, 1, 1
        
        # Entrenar modelo
        modelo = ARIMA(serie_train, order=(p, d, q))
        modelo_fit = modelo.fit()
        
        # Predicciones
        y_pred_train = modelo_fit.fittedvalues
        y_pred_val = modelo_fit.forecast(steps=len(serie_val))
        y_pred_test = modelo_fit.forecast(steps=len(serie_val) + len(serie_test))[-len(serie_test):]
        
        # Métricas
        metricas = {
            'train': {
                'mse': mean_squared_error(serie_train, y_pred_train),
                'mae': mean_absolute_error(serie_train, y_pred_train),
                'r2': r2_score(serie_train, y_pred_train)
            },
            'val': {
                'mse': mean_squared_error(serie_val, y_pred_val),
                'mae': mean_absolute_error(serie_val, y_pred_val),
                'r2': r2_score(serie_val, y_pred_val)
            },
            'test': {
                'mse': mean_squared_error(serie_test, y_pred_test),
                'mae': mean_absolute_error(serie_test, y_pred_test),
                'r2': r2_score(serie_test, y_pred_test)
            }
        }
        
        print(f"✓ Modelo ARIMA({p},{d},{q}) entrenado")
        print(f"  - R² Train: {metricas['train']['r2']:.4f}")
        print(f"  - R² Validation: {metricas['val']['r2']:.4f}")
        print(f"  - R² Test: {metricas['test']['r2']:.4f}")
        
        return modelo_fit, metricas, (y_pred_train, y_pred_val, y_pred_test)
        
    except Exception as e:
        print(f"✗ Error en modelo ARIMA: {e}")
        return None, None, None

def comparar_modelos(resultados_modelos):
    """
    Comparar rendimiento de todos los modelos
    """
    print(f"\n=== COMPARACIÓN DE MODELOS ===")
    
    # Crear tabla comparativa
    comparacion = []
    
    for nombre, (modelo, metricas, predicciones) in resultados_modelos.items():
        if metricas is not None:
            comparacion.append({
                'Modelo': nombre,
                'R² Train': f"{metricas['train']['r2']:.4f}",
                'R² Val': f"{metricas['val']['r2']:.4f}",
                'R² Test': f"{metricas['test']['r2']:.4f}",
                'MSE Test': f"{metricas['test']['mse']:.4f}",
                'MAE Test': f"{metricas['test']['mae']:.4f}"
            })
    
    df_comparacion = pd.DataFrame(comparacion)
    print(df_comparacion.to_string(index=False))
    
    # Determinar mejor modelo
    if len(comparacion) > 0:
        mejor_modelo = max(comparacion, key=lambda x: float(x['R² Test']))
        print(f"\n🏆 MEJOR MODELO: {mejor_modelo['Modelo']}")
        print(f"   - R² Test: {mejor_modelo['R² Test']}")
        print(f"   - MSE Test: {mejor_modelo['MSE Test']}")
    
    return df_comparacion

def generar_recomendaciones_finales(df_comparacion, parametro, localidad):
    """
    Generar recomendaciones finales para el usuario
    """
    print(f"\n=== RECOMENDACIONES FINALES PARA {parametro} en {localidad} ===")
    
    if df_comparacion.empty:
        print("⚠ No hay modelos exitosos para comparar")
        return
    
    # Análisis de rendimiento
    mejor_r2 = df_comparacion['R² Test'].astype(float).max()
    peor_r2 = df_comparacion['R² Test'].astype(float).min()
    
    print(f"\n📊 ANÁLISIS DE RENDIMIENTO:")
    print(f"  - Mejor R²: {mejor_r2:.4f}")
    print(f"  - Peor R²: {peor_r2:.4f}")
    print(f"  - Rango de rendimiento: {mejor_r2 - peor_r2:.4f}")
    
    # Recomendaciones específicas
    if mejor_r2 > 0.8:
        print(f"\n🎯 CALIDAD EXCELENTE:")
        print(f"  - Los modelos pueden hacer predicciones muy precisas")
        print(f"  - Recomendado para aplicaciones críticas")
        print(f"  - Considerar implementación en tiempo real")
    elif mejor_r2 > 0.6:
        print(f"\n🎯 CALIDAD BUENA:")
        print(f"  - Los modelos pueden hacer predicciones útiles")
        print(f"  - Adecuado para alertas y monitoreo")
        print(f"  - Mejorar con más datos o features")
    elif mejor_r2 > 0.4:
        print(f"\n🎯 CALIDAD MODERADA:")
        print(f"  - Los modelos tienen rendimiento limitado")
        print(f"  - Útil para tendencias generales")
        print(f"  - Requiere mejoras significativas")
    else:
        print(f"\n🎯 CALIDAD BAJA:")
        print(f"  - Los modelos no son confiables")
        print(f"  - Revisar calidad de datos")
        print(f"  - Considerar enfoques alternativos")
    
    # Recomendaciones por tipo de modelo
    print(f"\n🔧 RECOMENDACIONES TÉCNICAS:")
    
    # Verificar si Random Forest es el mejor
    if 'Random Forest' in df_comparacion['Modelo'].values:
        rf_row = df_comparacion[df_comparacion['Modelo'] == 'Random Forest'].iloc[0]
        rf_r2 = float(rf_row['R² Test'])
        if rf_r2 > 0.6:
            print(f"  ✅ Random Forest: Excelente para interpretabilidad y robustez")
            print(f"     - Usar para explicar factores importantes")
            print(f"     - Aplicar para alertas automáticas")
    
    # Verificar si Regresión Lineal es el mejor
    if 'Regresión Lineal' in df_comparacion['Modelo'].values:
        lr_row = df_comparacion[df_comparacion['Modelo'] == 'Regresión Lineal'].iloc[0]
        lr_r2 = float(lr_row['R² Test'])
        if lr_r2 > 0.5:
            print(f"  ✅ Regresión Lineal: Bueno para relaciones simples")
            print(f"     - Fácil de implementar y mantener")
            print(f"     - Adecuado para sistemas básicos")
    
    # Verificar si ARIMA es el mejor
    if 'ARIMA' in df_comparacion['Modelo'].values:
        arima_row = df_comparacion[df_comparacion['Modelo'] == 'ARIMA'].iloc[0]
        arima_r2 = float(arima_row['R² Test'])
        if arima_r2 > 0.6:
            print(f"  ✅ ARIMA: Excelente para patrones temporales")
            print(f"     - Usar para predicciones a corto plazo")
            print(f"     - Aplicar para alertas de calidad del aire")
    
    # Recomendaciones de implementación
    print(f"\n🚀 PLAN DE IMPLEMENTACIÓN:")
    print(f"  1. Modelo en Producción: Usar el modelo con mejor R² Test")
    print(f"  2. Monitoreo: Implementar métricas de rendimiento continuo")
    print(f"  3. Retraining: Actualizar modelo cada 1-3 meses")
    print(f"  4. Alertas: Configurar umbrales basados en MAE")
    print(f"  5. Dashboard: Crear interfaz para usuarios finales")
    
    # Recomendaciones para usuarios finales
    print(f"\n👥 RECOMENDACIONES PARA USUARIOS FINALES:")
    if mejor_r2 > 0.7:
        print(f"  ✅ Confiar en las predicciones para planificación")
        print(f"  ✅ Usar para tomar decisiones informadas")
        print(f"  ✅ Considerar implementar alertas automáticas")
    elif mejor_r2 > 0.5:
        print(f"  ⚠ Usar predicciones como guía general")
        print(f"  ⚠ Verificar con otras fuentes de información")
        print(f"  ⚠ No confiar para decisiones críticas")
    else:
        print(f"  ❌ No usar predicciones para decisiones")
        print(f"  ❌ Considerar solo como información de tendencia")
        print(f"  ❌ Buscar mejoras en la calidad de datos")

def crear_visualizaciones_comparativas(resultados_modelos, df_comparacion):
    """
    Crear visualizaciones comparativas de los modelos
    """
    print(f"\n=== CREANDO VISUALIZACIONES COMPARATIVAS ===")
    
    # Configurar subplots
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('Comparación de Modelos de Predicción', fontsize=16)
    
    # 1. Comparación de R² por conjunto de datos
    ax1 = axes[0, 0]
    modelos = df_comparacion['Modelo'].values
    r2_train = df_comparacion['R² Train'].astype(float).values
    r2_val = df_comparacion['R² Val'].astype(float).values
    r2_test = df_comparacion['R² Test'].astype(float).values
    
    x = np.arange(len(modelos))
    width = 0.25
    
    ax1.bar(x - width, r2_train, width, label='Train', alpha=0.8)
    ax1.bar(x, r2_val, width, label='Validation', alpha=0.8)
    ax1.bar(x + width, r2_test, width, label='Test', alpha=0.8)
    
    ax1.set_xlabel('Modelos')
    ax1.set_ylabel('R² Score')
    ax1.set_title('Comparación de R² por Conjunto de Datos')
    ax1.set_xticks(x)
    ax1.set_xticklabels(modelos, rotation=45)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. Métricas de error por modelo
    ax2 = axes[0, 1]
    mse_test = df_comparacion['MSE Test'].astype(float).values
    mae_test = df_comparacion['MAE Test'].astype(float).values
    
    ax2.bar(x - width/2, mse_test, width, label='MSE', alpha=0.8)
    ax2.bar(x + width/2, mae_test, width, label='MAE', alpha=0.8)
    
    ax2.set_xlabel('Modelos')
    ax2.set_ylabel('Error')
    ax2.set_title('Métricas de Error por Modelo')
    ax2.set_xticks(x)
    ax2.set_xticklabels(modelos, rotation=45)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. Predicciones vs Valores reales (mejor modelo)
    ax3 = axes[1, 0]
    mejor_modelo_nombre = df_comparacion.loc[df_comparacion['R² Test'].astype(float).idxmax(), 'Modelo']
    
    if mejor_modelo_nombre in resultados_modelos:
        modelo, metricas, predicciones = resultados_modelos[mejor_modelo_nombre]
        y_pred_test = predicciones[2]  # Test predictions
        
        # Obtener valores reales del test
        if 'test_df' in globals():
            y_test = test_df['valor']
            ax3.scatter(y_test, y_pred_test, alpha=0.6)
            ax3.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2)
            ax3.set_xlabel('Valores Reales')
            ax3.set_ylabel('Predicciones')
            ax3.set_title(f'Predicciones vs Reales - {mejor_modelo_nombre}')
            ax3.grid(True, alpha=0.3)
    
    # 4. Ranking de modelos por R² Test
    ax4 = axes[1, 1]
    df_sorted = df_comparacion.sort_values('R² Test', ascending=True)
    y_pos = np.arange(len(df_sorted))
    
    ax4.barh(y_pos, df_sorted['R² Test'].astype(float).values)
    ax4.set_yticks(y_pos)
    ax4.set_yticklabels(df_sorted['Modelo'].values)
    ax4.set_xlabel('R² Score')
    ax4.set_title('Ranking de Modelos por R² Test')
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('comparacion_modelos_prediccion.png', dpi=300, bbox_inches='tight')
    print(f"✓ Visualizaciones guardadas en: comparacion_modelos_prediccion.png")
    
    plt.show()

def main():
    """
    Función principal del análisis de modelos
    """
    print("🚀 INICIANDO ANÁLISIS DE MODELOS DE PREDICCIÓN")
    
    # 1. Cargar y preparar datos
    df = cargar_y_preparar_datos()
    if df is None:
        return
    
    # 2. Crear dataset para modelado
    pivot_df, parametro, localidad = crear_dataset_modelado(df, 'pm25', 'Indura')
    if pivot_df is None:
        return
    
    # 3. Dividir datos temporalmente
    train_df, val_df, test_df = dividir_datos_temporales(pivot_df)
    
    # 4. Implementar modelos
    resultados_modelos = {}
    
    # Regresión Lineal
    modelo_lr, metricas_lr, pred_lr = modelo_regresion_lineal(train_df, val_df, test_df)
    if modelo_lr is not None:
        resultados_modelos['Regresión Lineal'] = (modelo_lr, metricas_lr, pred_lr)
    
    # Random Forest
    modelo_rf, metricas_rf, pred_rf, feature_importance = modelo_random_forest(train_df, val_df, test_df)
    if modelo_rf is not None:
        resultados_modelos['Random Forest'] = (modelo_rf, metricas_rf, pred_rf)
    
    # ARIMA
    modelo_arima, metricas_arima, pred_arima = modelo_arima(train_df, val_df, test_df)
    if modelo_arima is not None:
        resultados_modelos['ARIMA'] = (modelo_arima, metricas_arima, pred_arima)
    
    # 5. Comparar modelos
    df_comparacion = comparar_modelos(resultados_modelos)
    
    # 6. Generar recomendaciones
    generar_recomendaciones_finales(df_comparacion, parametro, localidad)
    
    # 7. Crear visualizaciones
    crear_visualizaciones_comparativas(resultados_modelos, df_comparacion)
    
    # 8. Guardar resultados
    print(f"\n=== GUARDANDO RESULTADOS ===")
    
    # Guardar comparación de modelos
    df_comparacion.to_csv('comparacion_modelos.csv', index=False)
    print(f"✓ Comparación de modelos guardada en: comparacion_modelos.csv")
    
    # Guardar feature importance si existe
    if 'Random Forest' in resultados_modelos:
        feature_importance.to_csv('feature_importance_random_forest.csv', index=False)
        print(f"✓ Feature importance guardado en: feature_importance_random_forest.csv")
    
    print(f"\n🎉 ANÁLISIS DE MODELOS COMPLETADO")

if __name__ == "__main__":
    main()
