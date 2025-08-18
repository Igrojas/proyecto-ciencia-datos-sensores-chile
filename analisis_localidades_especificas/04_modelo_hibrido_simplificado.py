#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MODELO HÍBRIDO SIMPLIFICADO - Random Forest + ARIMA
Versión simplificada para datos de calidad del aire

Autor: Análisis de Datos - Proyecto en Ciencia de Datos
Fecha: 2025
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Machine Learning
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

# Time Series
from statsmodels.tsa.arima.model import ARIMA

# Configuración de visualización
plt.style.use('default')
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (12, 8)

class ModeloHibridoSimplificado:
    """
    Clase simplificada del modelo híbrido Random Forest + ARIMA
    """
    
    def __init__(self, parametro_objetivo='pm25'):
        self.parametro_objetivo = parametro_objetivo
        self.rf_model = None
        self.arima_fitted = None
        self.is_fitted = False
        
    def cargar_datos(self, ruta_csv):
        """Carga y prepara los datos"""
        print(f"📊 Cargando datos desde: {ruta_csv}")
        
        try:
            # Cargar datos
            df = pd.read_csv(ruta_csv)
            
            # Filtrar por parámetro objetivo
            df_filtrado = df[df['parametro_nombre'] == self.parametro_objetivo].copy()
            
            # Convertir fecha y ordenar
            df_filtrado['timestamp'] = pd.to_datetime(df_filtrado['fecha_desde_utc'])
            df_filtrado = df_filtrado.sort_values('timestamp').reset_index(drop=True)
            
            # Seleccionar solo columnas necesarias
            df_clean = df_filtrado[['timestamp', 'valor', 'localidad_nombre']].copy()
            
            print(f"✅ Datos cargados exitosamente")
            print(f"   - Total de registros: {len(df_clean):,}")
            print(f"   - Parámetro objetivo: {self.parametro_objetivo}")
            print(f"   - Rango temporal: {df_clean['timestamp'].min()} a {df_clean['timestamp'].max()}")
            
            return df_clean
            
        except Exception as e:
            print(f"❌ Error al cargar datos: {e}")
            return None
    
    def crear_features_basicos(self, df):
        """Crea features básicos temporales"""
        print("🔧 Creando features básicos...")
        
        df_features = df.copy()
        
        # Features de tiempo básicos
        df_features['hour'] = df_features['timestamp'].dt.hour
        df_features['day'] = df_features['timestamp'].dt.day
        df_features['month'] = df_features['timestamp'].dt.month
        
        # Features cíclicos
        df_features['hour_sin'] = np.sin(2 * np.pi * df_features['hour'] / 24)
        df_features['hour_cos'] = np.cos(2 * np.pi * df_features['hour'] / 24)
        df_features['month_sin'] = np.sin(2 * np.pi * df_features['month'] / 12)
        df_features['month_cos'] = np.cos(2 * np.pi * df_features['month'] / 12)
        
        # Lags simples (solo 1 y 2)
        df_features['lag_1'] = df_features['valor'].shift(1)
        df_features['lag_2'] = df_features['valor'].shift(2)
        
        # Promedio móvil simple
        df_features['ma_3'] = df_features['valor'].rolling(window=3).mean()
        
        # Feature de localidad (código numérico)
        df_features['localidad_code'] = df_features['localidad_nombre'].astype('category').cat.codes
        
        # Eliminar NaN
        df_features = df_features.dropna()
        
        print(f"✅ Features creados: {len(df_features)} muestras, {df_features.shape[1]} columnas")
        
        return df_features
    
    def dividir_datos_temporales(self, df_features):
        """Divide los datos temporalmente"""
        print("✂️ Dividiendo datos temporalmente...")
        
        n_samples = len(df_features)
        n_train = int(n_samples * 0.6)
        n_val = int(n_samples * 0.2)
        
        # División temporal
        train_data = df_features[:n_train]
        val_data = df_features[n_train:n_train + n_val]
        test_data = df_features[n_train + n_val:]
        
        # Preparar X e y
        feature_cols = [col for col in df_features.columns 
                       if col not in ['timestamp', 'valor', 'localidad_nombre']]
        
        X_train = train_data[feature_cols]
        y_train = train_data['valor']
        
        X_val = val_data[feature_cols]
        y_val = val_data['valor']
        
        X_test = test_data[feature_cols]
        y_test = test_data['valor']
        
        print(f"✅ Datos divididos:")
        print(f"   - Entrenamiento: {len(X_train):,} muestras")
        print(f"   - Validación: {len(X_val):,} muestras")
        print(f"   - Test: {len(X_test):,} muestras")
        
        return X_train, X_val, X_test, y_train, y_val, y_test
    
    def entrenar_random_forest(self, X_train, y_train, X_val, y_val):
        """Entrena Random Forest"""
        print("🌲 Entrenando Random Forest...")
        
        self.rf_model = RandomForestRegressor(
            n_estimators=50,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        
        self.rf_model.fit(X_train, y_train)
        
        # Evaluar en validación
        y_pred_val = self.rf_model.predict(X_val)
        mse_val = mean_squared_error(y_val, y_pred_val)
        mae_val = mean_absolute_error(y_val, y_pred_val)
        r2_val = r2_score(y_val, y_pred_val)
        
        print(f"✅ Random Forest entrenado:")
        print(f"   - MSE Validación: {mse_val:.4f}")
        print(f"   - MAE Validación: {mae_val:.4f}")
        print(f"   - R² Validación: {r2_val:.4f}")
        
        return self.rf_model
    
    def entrenar_arima(self, y_train):
        """Entrena ARIMA"""
        print("📈 Entrenando ARIMA...")
        
        try:
            # ARIMA simple
            self.arima_fitted = ARIMA(y_train, order=(1, 0, 0)).fit()
            print(f"✅ ARIMA entrenado exitosamente")
            return self.arima_fitted
        except Exception as e:
            print(f"⚠️ Error en ARIMA: {e}")
            return None
    
    def predecir_hibrido(self, X_test, y_test):
        """Realiza predicciones híbridas"""
        print("🔮 Realizando predicciones híbridas...")
        
        if self.rf_model is None:
            print("❌ Random Forest no entrenado")
            return None
        
        # Predicción Random Forest
        y_pred_rf = self.rf_model.predict(X_test)
        
        # Predicción ARIMA
        if self.arima_fitted is not None:
            try:
                y_pred_arima = self.arima_fitted.forecast(steps=len(y_test))
            except:
                y_pred_arima = np.full(len(y_test), y_test.mean())
        else:
            y_pred_arima = np.full(len(y_test), y_test.mean())
        
        # Combinar predicciones (70% RF + 30% ARIMA)
        y_pred_hibrido = 0.7 * y_pred_rf + 0.3 * y_pred_arima
        
        # Calcular métricas
        resultados = {
            'y_real': y_test,
            'y_pred_rf': y_pred_rf,
            'y_pred_arima': y_pred_arima,
            'y_pred_hibrido': y_pred_hibrido,
            'metricas': {
                'rf': {
                    'mse': mean_squared_error(y_test, y_pred_rf),
                    'mae': mean_absolute_error(y_test, y_pred_rf),
                    'r2': r2_score(y_test, y_pred_rf)
                },
                'arima': {
                    'mse': mean_squared_error(y_test, y_pred_arima),
                    'mae': mean_absolute_error(y_test, y_pred_arima),
                    'r2': r2_score(y_test, y_pred_arima)
                },
                'hibrido': {
                    'mse': mean_squared_error(y_test, y_pred_hibrido),
                    'mae': mean_absolute_error(y_test, y_pred_hibrido),
                    'r2': r2_score(y_test, y_pred_hibrido)
                }
            }
        }
        
        # Mostrar métricas
        print("📊 Métricas de Predicción:")
        for modelo, metricas in resultados['metricas'].items():
            print(f"   {modelo.upper()}:")
            print(f"     - MSE: {metricas['mse']:.4f}")
            print(f"     - MAE: {metricas['mae']:.4f}")
            print(f"     - R²: {metricas['r2']:.4f}")
        
        return resultados
    
    def crear_visualizacion(self, resultados):
        """Crea visualización simple"""
        print("📊 Creando visualización...")
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Gráfico 1: Comparación de predicciones
        ax1.plot(resultados['y_real'].values, label='Real', alpha=0.7, linewidth=2)
        ax1.plot(resultados['y_pred_hibrido'], label='Híbrido (RF+ARIMA)', alpha=0.8, linewidth=2)
        ax1.plot(resultados['y_pred_rf'], label='Random Forest', alpha=0.6, linewidth=1.5)
        ax1.plot(resultados['y_pred_arima'], label='ARIMA', alpha=0.6, linewidth=1.5)
        ax1.set_title(f'Modelo Híbrido - {self.parametro_objetivo.upper()}')
        ax1.set_xlabel('Muestras')
        ax1.set_ylabel(f'{self.parametro_objetivo.upper()}')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Gráfico 2: Scatter plot
        ax2.scatter(resultados['y_real'], resultados['y_pred_hibrido'], alpha=0.6, color='blue')
        ax2.plot([resultados['y_real'].min(), resultados['y_real'].max()], 
                 [resultados['y_real'].min(), resultados['y_real'].max()], 
                 'r--', linewidth=2, label='Línea Perfecta')
        ax2.set_title('Real vs Predicho (Híbrido)')
        ax2.set_xlabel('Valor Real')
        ax2.set_ylabel('Valor Predicho')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Guardar
        nombre_archivo = f"modelo_hibrido_{self.parametro_objetivo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(nombre_archivo, dpi=300, bbox_inches='tight')
        print(f"✅ Visualización guardada: {nombre_archivo}")
        
        plt.show()
    
    def generar_reporte(self, resultados):
        """Genera reporte final"""
        print("\n" + "="*60)
        print("📋 REPORTE FINAL - MODELO HÍBRIDO SIMPLIFICADO")
        print("="*60)
        
        print(f"\n🎯 PARÁMETRO OBJETIVO: {self.parametro_objetivo.upper()}")
        print(f"📊 TOTAL DE MUESTRAS: {len(resultados['y_real']):,}")
        
        print(f"\n🏆 RESULTADOS POR MODELO:")
        print("-" * 40)
        
        for modelo, metricas in resultados['metricas'].items():
            print(f"\n{modelo.upper()}:")
            print(f"  • MSE: {metricas['mse']:.6f}")
            print(f"  • MAE: {metricas['mae']:.6f}")
            print(f"  • R²: {metricas['r2']:.4f}")
        
        # Mejor modelo
        mejor_modelo = min(resultados['metricas'].keys(), 
                          key=lambda x: resultados['metricas'][x]['mse'])
        
        print(f"\n🥇 MEJOR MODELO: {mejor_modelo.upper()}")
        print(f"   - R²: {resultados['metricas'][mejor_modelo]['r2']:.4f}")
        
        print("\n" + "="*60)
    
    def ejecutar_pipeline(self, ruta_csv):
        """Ejecuta el pipeline completo"""
        print("🚀 INICIANDO PIPELINE SIMPLIFICADO")
        print("=" * 50)
        
        # 1. Cargar datos
        df = self.cargar_datos(ruta_csv)
        if df is None:
            return None
        
        # 2. Crear features
        df_features = self.crear_features_basicos(df)
        
        # 3. Dividir datos
        X_train, X_val, X_test, y_train, y_val, y_test = self.dividir_datos_temporales(df_features)
        
        # 4. Entrenar Random Forest
        self.entrenar_random_forest(X_train, y_train, X_val, y_val)
        
        # 5. Entrenar ARIMA
        self.entrenar_arima(y_train)
        
        # 6. Predecir
        resultados = self.predecir_hibrido(X_test, y_test)
        
        # 7. Visualizar
        self.crear_visualizacion(resultados)
        
        # 8. Reporte
        self.generar_reporte(resultados)
        
        self.is_fitted = True
        print("\n✅ PIPELINE COMPLETADO!")
        return resultados


def main():
    """Función principal"""
    print("🎯 MODELO HÍBRIDO SIMPLIFICADO - Random Forest + ARIMA")
    print("=" * 60)
    
    # Crear modelo
    modelo = ModeloHibridoSimplificado(parametro_objetivo='pm10')
    
    # Ruta al CSV
    ruta_csv = "../data/localidades_especificas_20250818_001116.csv"
    
    try:
        # Ejecutar pipeline
        resultados = modelo.ejecutar_pipeline(ruta_csv)
        
        if resultados is not None:
            print(f"\n🎉 ¡Modelo híbrido ejecutado exitosamente!")
        else:
            print(f"\n❌ Error en la ejecución")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
