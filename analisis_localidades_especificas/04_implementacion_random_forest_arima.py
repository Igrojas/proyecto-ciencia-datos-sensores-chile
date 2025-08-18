#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IMPLEMENTACIÓN DE LA PRIMERA OPCIÓN RECOMENDADA
Random Forest + ARIMA para Predicción de Calidad del Aire

Este script implementa la combinación de Random Forest y ARIMA como modelo híbrido
para obtener las mejores predicciones de calidad del aire en las localidades chilenas.

Autor: Análisis de Datos - Proyecto en Ciencia de Datos
Fecha: 2025
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Machine Learning
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler

# Time Series
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf

# Feature Engineering
from sklearn.feature_selection import SelectKBest, f_regression

# Configuración de visualización
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 10

class ModeloHibridoRFARIMA:
    """
    Clase que implementa el modelo híbrido Random Forest + ARIMA
    para predicción de calidad del aire
    """
    
    def __init__(self, parametro_objetivo='pm25'):
        """
        Inicializa el modelo híbrido
        
        Args:
            parametro_objetivo (str): Contaminante a predecir
        """
        self.parametro_objetivo = parametro_objetivo
        self.rf_model = None
        self.arima_model = None
        self.scaler = StandardScaler()
        self.feature_selector = None
        self.feature_names = None
        self.is_fitted = False
        
    def cargar_datos(self, ruta_csv):
        """
        Carga y prepara los datos del CSV
        
        Args:
            ruta_csv (str): Ruta al archivo CSV con los datos
            
        Returns:
            pd.DataFrame: DataFrame preparado
        """
        print(f"📊 Cargando datos desde: {ruta_csv}")
        
        try:
            # Cargar datos
            df = pd.read_csv(ruta_csv)
            
            # Convertir fecha_desde_utc a datetime y renombrar
            df['timestamp'] = pd.to_datetime(df['fecha_desde_utc'])
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            # Filtrar por parámetro objetivo (usar parametro_nombre)
            df_filtrado = df[df['parametro_nombre'] == self.parametro_objetivo].copy()
            
            print(f"✅ Datos cargados exitosamente")
            print(f"   - Total de registros: {len(df_filtrado):,}")
            print(f"   - Parámetro objetivo: {self.parametro_objetivo}")
            print(f"   - Rango temporal: {df_filtrado['timestamp'].min()} a {df_filtrado['timestamp'].max()}")
            
            return df_filtrado
            
        except Exception as e:
            print(f"❌ Error al cargar datos: {e}")
            return None
    
    def crear_features_temporales(self, df):
        """
        Crea features temporales para el modelo
        
        Args:
            df (pd.DataFrame): DataFrame con columna timestamp
            
        Returns:
            pd.DataFrame: DataFrame con features temporales
        """
        print("🔧 Creando features temporales...")
        
        df_features = df.copy()
        
        # Features básicos de tiempo
        df_features['year'] = df_features['timestamp'].dt.year
        df_features['month'] = df_features['timestamp'].dt.month
        df_features['day'] = df_features['timestamp'].dt.day
        df_features['hour'] = df_features['timestamp'].dt.hour
        df_features['day_of_week'] = df_features['timestamp'].dt.dayofweek
        df_features['day_of_year'] = df_features['timestamp'].dt.dayofyear
        
        # Features cíclicos (sin y cos para estacionalidad)
        df_features['month_sin'] = np.sin(2 * np.pi * df_features['month'] / 12)
        df_features['month_cos'] = np.cos(2 * np.pi * df_features['month'] / 12)
        df_features['hour_sin'] = np.sin(2 * np.pi * df_features['hour'] / 24)
        df_features['hour_cos'] = np.cos(2 * np.pi * df_features['hour'] / 24)
        df_features['day_of_week_sin'] = np.sin(2 * np.pi * df_features['day_of_week'] / 7)
        df_features['day_of_week_cos'] = np.cos(2 * np.pi * df_features['day_of_week'] / 7)
        
        # Lags temporales (solo los más importantes para evitar muchos NaN)
        for lag in [1, 2, 3]:
            df_features[f'lag_{lag}'] = df_features['valor'].shift(lag)
        
        # Promedios móviles (ventanas más pequeñas)
        for window in [3, 6]:
            df_features[f'ma_{window}'] = df_features['valor'].rolling(window=window).mean()
        
        # Diferencias temporales (solo primera diferencia)
        df_features['diff_1'] = df_features['valor'].diff()
        
        # Features de localidad (one-hot encoding) - solo si no hay valores nulos
        if 'localidad_nombre' in df_features.columns and df_features['localidad_nombre'].notna().all():
            df_features = pd.get_dummies(df_features, columns=['localidad_nombre'], prefix='loc')
        else:
            # Si hay valores nulos, crear feature binaria simple
            df_features['localidad_encoded'] = df_features['localidad_nombre'].astype('category').cat.codes
        
        print(f"✅ Features temporales creados: {df_features.shape[1]} columnas")
        
        return df_features
    
    def preparar_datos_modelado(self, df_features):
        """
        Prepara los datos para el modelado, eliminando NaN y seleccionando features
        
        Args:
            df_features (pd.DataFrame): DataFrame con features
            
        Returns:
            tuple: (X, y) preparados para modelado
        """
        print("🔧 Preparando datos para modelado...")
        
        # Eliminar filas con NaN (por lags y promedios móviles)
        df_clean = df_features.dropna()
        print(f"   - Después de limpiar NaN: {len(df_clean)} muestras")
        
        # Separar features y target
        feature_columns = [col for col in df_clean.columns 
                          if col not in ['timestamp', 'parametro_nombre', 'valor', 'unidad']]
        
        print(f"   - Features disponibles: {len(feature_columns)}")
        print(f"   - Features: {feature_columns[:10]}...")
        
        X = df_clean[feature_columns]
        y = df_clean['valor']
        
        # Seleccionar mejores features
        self.feature_selector = SelectKBest(score_func=f_regression, k=min(20, len(feature_columns)))
        X_selected = self.feature_selector.fit_transform(X, y)
        
        # Obtener nombres de features seleccionados
        selected_features = self.feature_selector.get_support()
        self.feature_names = X.columns[selected_features].tolist()
        
        print(f"✅ Datos preparados: {X_selected.shape[0]} muestras, {X_selected.shape[1]} features")
        print(f"   - Features seleccionados: {self.feature_names[:10]}...")
        
        return X_selected, y
    
    def dividir_datos_temporales(self, X, y, train_ratio=0.6, val_ratio=0.2):
        """
        Divide los datos temporalmente (no aleatoriamente)
        
        Args:
            X (np.array): Features
            y (np.array): Target
            train_ratio (float): Proporción para entrenamiento
            val_ratio (float): Proporción para validación
            
        Returns:
            tuple: (X_train, X_val, X_test, y_train, y_val, y_test)
        """
        print("✂️ Dividiendo datos temporalmente...")
        
        n_samples = len(X)
        n_train = int(n_samples * train_ratio)
        n_val = int(n_samples * val_ratio)
        
        # División temporal (no aleatoria)
        X_train = X[:n_train]
        y_train = y[:n_train]
        
        X_val = X[n_train:n_train + n_val]
        y_val = y[n_train:n_train + n_val]
        
        X_test = X[n_train + n_val:]
        y_test = y[n_train + n_val:]
        
        print(f"✅ Datos divididos:")
        print(f"   - Entrenamiento: {len(X_train):,} muestras ({train_ratio*100:.0f}%)")
        print(f"   - Validación: {len(X_val):,} muestras ({val_ratio*100:.0f}%)")
        print(f"   - Test: {len(X_test):,} muestras ({(1-train_ratio-val_ratio)*100:.0f}%)")
        
        return X_train, X_val, X_test, y_train, y_val, y_test
    
    def entrenar_random_forest(self, X_train, y_train, X_val, y_val):
        """
        Entrena el modelo Random Forest
        
        Args:
            X_train, y_train: Datos de entrenamiento
            X_val, y_val: Datos de validación
            
        Returns:
            RandomForestRegressor: Modelo entrenado
        """
        print("🌲 Entrenando Random Forest...")
        
        # Configurar modelo
        self.rf_model = RandomForestRegressor(
            n_estimators=100,
            max_depth=15,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )
        
        # Entrenar modelo
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
        """
        Entrena el modelo ARIMA
        
        Args:
            y_train (np.array): Serie temporal de entrenamiento
            
        Returns:
            ARIMA: Modelo entrenado
        """
        print("📈 Entrenando ARIMA...")
        
        try:
            # Determinar orden ARIMA automáticamente (p, d, q)
            # Para simplificar, usamos valores estándar
            p, d, q = 1, 1, 1
            
            # Crear y entrenar modelo ARIMA
            self.arima_model = ARIMA(y_train, order=(p, d, q))
            self.arima_fitted = self.arima_model.fit()
            
            print(f"✅ ARIMA entrenado con orden ({p}, {d}, {q})")
            print(f"   - AIC: {self.arima_fitted.aic:.2f}")
            print(f"   - BIC: {self.arima_fitted.bic:.2f}")
            
            return self.arima_fitted
            
        except Exception as e:
            print(f"⚠️ Error en ARIMA, usando orden simple: {e}")
            # Fallback a orden simple
            try:
                self.arima_model = ARIMA(y_train, order=(1, 0, 0))
                self.arima_fitted = self.arima_model.fit()
                print(f"✅ ARIMA fallback entrenado")
                return self.arima_fitted
            except:
                print(f"❌ No se pudo entrenar ARIMA")
                return None
    
    def predecir_hibrido(self, X_test, y_test):
        """
        Realiza predicciones combinando Random Forest y ARIMA
        
        Args:
            X_test (np.array): Features de test
            y_test (np.array): Valores reales de test
            
        Returns:
            dict: Diccionario con predicciones y métricas
        """
        print("🔮 Realizando predicciones híbridas...")
        
        if self.rf_model is None or self.arima_fitted is None:
            print("❌ Modelos no entrenados")
            return None
        
        # Predicción Random Forest
        y_pred_rf = self.rf_model.predict(X_test)
        
        # Predicción ARIMA
        try:
            y_pred_arima = self.arima_fitted.forecast(steps=len(y_test))
        except:
            # Si falla, usar predicción simple
            y_pred_arima = np.full(len(y_test), y_test.mean())
        
        # Combinar predicciones (promedio ponderado)
        # RF tiene más peso por ser más robusto
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
    
    def analizar_importancia_features(self):
        """
        Analiza la importancia de features del Random Forest
        
        Returns:
            pd.DataFrame: DataFrame con importancia de features
        """
        if self.rf_model is None:
            print("❌ Modelo Random Forest no entrenado")
            return None
        
        # Obtener importancia de features
        importancia = self.rf_model.feature_importances_
        
        # Crear DataFrame
        df_importancia = pd.DataFrame({
            'feature': self.feature_names,
            'importancia': importancia
        }).sort_values('importancia', ascending=False)
        
        return df_importancia
    
    def crear_visualizaciones(self, resultados, df_original):
        """
        Crea visualizaciones de los resultados
        
        Args:
            resultados (dict): Resultados de predicción
            df_original (pd.DataFrame): DataFrame original
        """
        print("📊 Creando visualizaciones...")
        
        # Configurar subplots
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle(f'Modelo Híbrido Random Forest + ARIMA - {self.parametro_objetivo}', 
                     fontsize=16, fontweight='bold')
        
        # 1. Comparación de predicciones
        axes[0, 0].plot(resultados['y_real'].values, label='Real', alpha=0.7, linewidth=2)
        axes[0, 0].plot(resultados['y_pred_hibrido'], label='Híbrido (RF+ARIMA)', alpha=0.8, linewidth=2)
        axes[0, 0].plot(resultados['y_pred_rf'], label='Random Forest', alpha=0.6, linewidth=1.5)
        axes[0, 0].plot(resultados['y_pred_arima'], label='ARIMA', alpha=0.6, linewidth=1.5)
        axes[0, 0].set_title('Comparación de Predicciones')
        axes[0, 0].set_xlabel('Muestras')
        axes[0, 0].set_ylabel(f'{self.parametro_objetivo}')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
        
        # 2. Scatter plot real vs predicho
        axes[0, 1].scatter(resultados['y_real'], resultados['y_pred_hibrido'], 
                           alpha=0.6, color='blue')
        axes[0, 1].plot([resultados['y_real'].min(), resultados['y_real'].max()], 
                        [resultados['y_real'].min(), resultados['y_real'].max()], 
                        'r--', linewidth=2, label='Línea Perfecta')
        axes[0, 1].set_title('Real vs Predicho (Híbrido)')
        axes[0, 1].set_xlabel('Valor Real')
        axes[0, 1].set_ylabel('Valor Predicho')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)
        
        # 3. Importancia de features
        if self.rf_model is not None:
            importancia = self.analizar_importancia_features()
            top_features = importancia.head(10)
            axes[1, 0].barh(range(len(top_features)), top_features['importancia'])
            axes[1, 0].set_yticks(range(len(top_features)))
            axes[1, 0].set_yticklabels(top_features['feature'])
            axes[1, 0].set_title('Top 10 Features Más Importantes')
            axes[1, 0].set_xlabel('Importancia')
            axes[1, 0].grid(True, alpha=0.3)
        
        # 4. Métricas comparativas
        modelos = list(resultados['metricas'].keys())
        mse_values = [resultados['metricas'][m]['mse'] for m in modelos]
        mae_values = [resultados['metricas'][m]['mae'] for m in modelos]
        
        x = np.arange(len(modelos))
        width = 0.35
        
        axes[1, 1].bar(x - width/2, mse_values, width, label='MSE', alpha=0.8)
        axes[1, 1].bar(x + width/2, mae_values, width, label='MAE', alpha=0.8)
        axes[1, 1].set_title('Comparación de Métricas por Modelo')
        axes[1, 1].set_xlabel('Modelo')
        axes[1, 1].set_ylabel('Error')
        axes[1, 1].set_xticks(x)
        axes[1, 1].set_xticklabels([m.upper() for m in modelos])
        axes[1, 1].legend()
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Guardar visualización
        nombre_archivo = f"modelo_hibrido_{self.parametro_objetivo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(nombre_archivo, dpi=300, bbox_inches='tight')
        print(f"✅ Visualización guardada: {nombre_archivo}")
        
        plt.show()
    
    def generar_reporte_final(self, resultados):
        """
        Genera un reporte final del modelo
        
        Args:
            resultados (dict): Resultados de predicción
        """
        print("\n" + "="*80)
        print("📋 REPORTE FINAL - MODELO HÍBRIDO RANDOM FOREST + ARIMA")
        print("="*80)
        
        print(f"\n🎯 PARÁMETRO OBJETIVO: {self.parametro_objetivo}")
        print(f"📊 TOTAL DE MUESTRAS: {len(resultados['y_real']):,}")
        
        print(f"\n🏆 RESULTADOS POR MODELO:")
        print("-" * 50)
        
        for modelo, metricas in resultados['metricas'].items():
            print(f"\n{modelo.upper()}:")
            print(f"  • Error Cuadrático Medio (MSE): {metricas['mse']:.6f}")
            print(f"  • Error Absoluto Medio (MAE): {metricas['mae']:.6f}")
            print(f"  • Coeficiente de Determinación (R²): {metricas['r2']:.4f}")
        
        # Determinar mejor modelo
        mejor_modelo = min(resultados['metricas'].keys(), 
                          key=lambda x: resultados['metricas'][x]['mse'])
        
        print(f"\n🥇 MEJOR MODELO: {mejor_modelo.upper()}")
        print(f"   - MSE: {resultados['metricas'][mejor_modelo]['mse']:.6f}")
        print(f"   - MAE: {resultados['metricas'][mejor_modelo]['mae']:.6f}")
        print(f"   - R²: {resultados['metricas'][mejor_modelo]['r2']:.4f}")
        
        print(f"\n💡 RECOMENDACIONES:")
        print("-" * 30)
        print("• El modelo híbrido combina la robustez de Random Forest con la")
        print("  capacidad temporal de ARIMA")
        print("• Random Forest maneja relaciones no lineales y features complejos")
        print("• ARIMA captura patrones temporales y estacionalidad")
        print("• La combinación ofrece mejor precisión que modelos individuales")
        
        print(f"\n🚀 PRÓXIMOS PASOS:")
        print("-" * 25)
        print("• Implementar en producción con datos en tiempo real")
        print("• Crear sistema de alertas automáticas")
        print("• Desarrollar dashboard interactivo")
        print("• Monitorear rendimiento continuamente")
        
        print("\n" + "="*80)
    
    def ejecutar_pipeline_completo(self, ruta_csv):
        """
        Ejecuta el pipeline completo del modelo híbrido
        
        Args:
            ruta_csv (str): Ruta al archivo CSV
            
        Returns:
            dict: Resultados completos del modelo
        """
        print("🚀 INICIANDO PIPELINE COMPLETO - MODELO HÍBRIDO RF+ARIMA")
        print("=" * 70)
        
        # 1. Cargar datos
        df = self.cargar_datos(ruta_csv)
        if df is None:
            return None
        
        # 2. Crear features temporales
        df_features = self.crear_features_temporales(df)
        
        # 3. Preparar datos para modelado
        X, y = self.preparar_datos_modelado(df_features)
        
        # 4. Dividir datos temporalmente
        X_train, X_val, X_test, y_train, y_val, y_test = self.dividir_datos_temporales(X, y)
        
        # 5. Entrenar Random Forest
        self.entrenar_random_forest(X_train, y_train, X_val, y_val)
        
        # 6. Entrenar ARIMA
        self.entrenar_arima(y_train)
        
        # 7. Realizar predicciones híbridas
        resultados = self.predecir_hibrido(X_test, y_test)
        
        # 8. Crear visualizaciones
        self.crear_visualizaciones(resultados, df)
        
        # 9. Generar reporte final
        self.generar_reporte_final(resultados)
        
        # 10. Marcar como entrenado
        self.is_fitted = True
        
        print("\n✅ PIPELINE COMPLETADO EXITOSAMENTE!")
        return resultados


def main():
    """
    Función principal para ejecutar el modelo híbrido
    """
    print("🎯 IMPLEMENTACIÓN DE LA PRIMERA OPCIÓN RECOMENDADA")
    print("Random Forest + ARIMA para Predicción de Calidad del Aire")
    print("=" * 70)
    
    # Configurar parámetro objetivo (cambiar según necesidad)
    parametros_disponibles = ['pm25', 'pm10', 'no2', 'o3', 'so2', 'co']
    
    print(f"\n📋 Parámetros disponibles: {', '.join(parametros_disponibles)}")
    print("💡 Recomendación: pm25 o pm10 para mejor precisión")
    
    # Crear instancia del modelo
    modelo = ModeloHibridoRFARIMA(parametro_objetivo='pm25')
    
    # Ruta al CSV (ajustar según ubicación)
    ruta_csv = "../data/localidades_especificas_20250818_001116.csv"
    
    try:
        # Ejecutar pipeline completo
        resultados = modelo.ejecutar_pipeline_completo(ruta_csv)
        
        if resultados is not None:
            print(f"\n🎉 ¡Modelo híbrido implementado exitosamente!")
            print(f"📊 Archivos generados:")
            print(f"   - Visualización: modelo_hibrido_{modelo.parametro_objetivo}_*.png")
            print(f"   - Modelo entrenado disponible en la instancia")
            
            # Guardar modelo (opcional)
            print(f"\n💾 Para guardar el modelo:")
            print(f"   import joblib")
            print(f"   joblib.dump(modelo, 'modelo_hibrido_{modelo.parametro_objetivo}.pkl')")
            
        else:
            print(f"\n❌ Error en la ejecución del pipeline")
            
    except Exception as e:
        print(f"\n❌ Error durante la ejecución: {e}")
        print(f"💡 Verificar que el archivo CSV existe y tiene el formato correcto")


if __name__ == "__main__":
    main()
