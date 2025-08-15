#!/usr/bin/env python3
"""
Modelo de predicción para la calidad del aire
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.svm import SVR
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.pipeline import Pipeline
import joblib
import warnings
warnings.filterwarnings('ignore')

class AirQualityPredictor:
    """
    Clase para predecir parámetros de calidad del aire
    """
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.feature_importance = {}
        self.best_params = {}
        
    def prepare_features(self, df, target_parameter):
        """
        Preparar características para el modelo
        
        Args:
            df (pd.DataFrame): DataFrame con los datos
            target_parameter (str): Parámetro objetivo a predecir
            
        Returns:
            tuple: (X, y) características y objetivo
        """
        # Filtrar datos del parámetro objetivo
        param_data = df[df['parameter_name'] == target_parameter].copy()
        
        if len(param_data) == 0:
            print(f"⚠ No hay datos para {target_parameter}")
            return None, None
        
        # Crear características temporales
        param_data['year'] = param_data['date_from_utc'].dt.year
        param_data['month'] = param_data['date_from_utc'].dt.month
        param_data['day'] = param_data['date_from_utc'].dt.day
        param_data['hour'] = param_data['date_from_utc'].dt.hour
        param_data['day_of_week'] = param_data['date_from_utc'].dt.dayofweek
        
        # Crear características cíclicas
        param_data['month_sin'] = np.sin(2 * np.pi * param_data['month'] / 12)
        param_data['month_cos'] = np.cos(2 * np.pi * param_data['month'] / 12)
        param_data['hour_sin'] = np.sin(2 * np.pi * param_data['hour'] / 24)
        param_data['hour_cos'] = np.cos(2 * np.pi * param_data['hour'] / 24)
        param_data['day_sin'] = np.sin(2 * np.pi * param_data['day'] / 31)
        param_data['day_cos'] = np.cos(2 * np.pi * param_data['day'] / 31)
        
        # Características de ubicación (one-hot encoding)
        location_dummies = pd.get_dummies(param_data['location_name'], prefix='location')
        
        # Características finales
        feature_cols = [
            'year', 'month', 'day', 'hour', 'day_of_week',
            'month_sin', 'month_cos', 'hour_sin', 'hour_cos', 'day_sin', 'day_cos'
        ]
        
        X = pd.concat([param_data[feature_cols], location_dummies], axis=1)
        y = param_data['value']
        
        print(f"✓ Características preparadas para {target_parameter}: {X.shape}")
        return X, y
    
    def train_models(self, X, y, target_parameter):
        """
        Entrenar múltiples modelos
        
        Args:
            X (pd.DataFrame): Características
            y (pd.Series): Variable objetivo
            target_parameter (str): Parámetro objetivo
        """
        print(f"\n=== ENTRENANDO MODELOS PARA {target_parameter.upper()} ===")
        
        # Dividir datos
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Definir modelos
        models = {
            'RandomForest': RandomForestRegressor(n_estimators=100, random_state=42),
            'GradientBoosting': GradientBoostingRegressor(random_state=42),
            'LinearRegression': LinearRegression(),
            'Ridge': Ridge(alpha=1.0),
            'Lasso': Lasso(alpha=0.1),
            'SVR': SVR(kernel='rbf')
        }
        
        # Entrenar y evaluar modelos
        results = {}
        
        for name, model in models.items():
            print(f"\nEntrenando {name}...")
            
            try:
                # Entrenar modelo
                model.fit(X_train, y_train)
                
                # Predicciones
                y_pred = model.predict(X_test)
                
                # Métricas
                mse = mean_squared_error(y_test, y_pred)
                rmse = np.sqrt(mse)
                mae = mean_absolute_error(y_test, y_pred)
                r2 = r2_score(y_test, y_pred)
                
                results[name] = {
                    'model': model,
                    'mse': mse,
                    'rmse': rmse,
                    'mae': mae,
                    'r2': r2,
                    'y_pred': y_pred
                }
                
                print(f"  ✓ {name}: R²={r2:.3f}, RMSE={rmse:.3f}, MAE={mae:.3f}")
                
                # Guardar importancia de características para Random Forest
                if name == 'RandomForest':
                    self.feature_importance[target_parameter] = pd.DataFrame({
                        'feature': X.columns,
                        'importance': model.feature_importances_
                    }).sort_values('importance', ascending=False)
                
            except Exception as e:
                print(f"  ✗ Error con {name}: {e}")
        
        # Guardar resultados
        self.models[target_parameter] = results
        
        # Seleccionar mejor modelo
        best_model_name = max(results.keys(), key=lambda x: results[x]['r2'])
        best_model = results[best_model_name]['model']
        
        print(f"\n🏆 Mejor modelo: {best_model_name} (R²={results[best_model_name]['r2']:.3f})")
        
        return best_model, results
    
    def hyperparameter_tuning(self, X, y, target_parameter, model_type='RandomForest'):
        """
        Ajuste de hiperparámetros
        
        Args:
            X (pd.DataFrame): Características
            y (pd.Series): Variable objetivo
            target_parameter (str): Parámetro objetivo
            model_type (str): Tipo de modelo a optimizar
        """
        print(f"\n=== AJUSTE DE HIPERPARÁMETROS PARA {target_parameter.upper()} ===")
        
        if model_type == 'RandomForest':
            param_grid = {
                'n_estimators': [50, 100, 200],
                'max_depth': [10, 20, None],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4]
            }
            model = RandomForestRegressor(random_state=42)
            
        elif model_type == 'GradientBoosting':
            param_grid = {
                'n_estimators': [50, 100, 200],
                'learning_rate': [0.01, 0.1, 0.2],
                'max_depth': [3, 5, 7],
                'subsample': [0.8, 0.9, 1.0]
            }
            model = GradientBoostingRegressor(random_state=42)
            
        else:
            print(f"⚠ Tipo de modelo {model_type} no soportado para tuning")
            return None
        
        # Grid search con validación cruzada
        grid_search = GridSearchCV(
            model, param_grid, cv=5, scoring='r2', n_jobs=-1, verbose=1
        )
        
        grid_search.fit(X, y)
        
        print(f"✓ Mejores parámetros: {grid_search.best_params_}")
        print(f"✓ Mejor score: {grid_search.best_score_:.3f}")
        
        # Guardar mejores parámetros
        self.best_params[target_parameter] = grid_search.best_params_
        
        return grid_search.best_estimator_
    
    def predict_future(self, model, location_name, future_dates, target_parameter):
        """
        Predecir valores futuros
        
        Args:
            model: Modelo entrenado
            location_name (str): Nombre de la ubicación
            future_dates (pd.DatetimeIndex): Fechas futuras
            target_parameter (str): Parámetro objetivo
            
        Returns:
            pd.DataFrame: Predicciones futuras
        """
        print(f"\n=== PREDICIENDO VALORES FUTUROS PARA {target_parameter.upper()} ===")
        
        # Crear características para fechas futuras
        future_features = []
        
        for date in future_dates:
            features = {
                'year': date.year,
                'month': date.month,
                'day': date.day,
                'hour': 12,  # Hora del mediodía como referencia
                'day_of_week': date.dayofweek,
                'month_sin': np.sin(2 * np.pi * date.month / 12),
                'month_cos': np.cos(2 * np.pi * date.month / 12),
                'hour_sin': np.sin(2 * np.pi * 12 / 24),
                'hour_cos': np.cos(2 * np.pi * 12 / 24),
                'day_sin': np.sin(2 * np.pi * date.day / 31),
                'day_cos': np.cos(2 * np.pi * date.day / 31)
            }
            
            # Agregar ubicación
            for col in model.feature_names_in_:
                if col.startswith('location_'):
                    features[col] = 1 if col == f'location_{location_name}' else 0
            
            future_features.append(features)
        
        # Crear DataFrame de características
        X_future = pd.DataFrame(future_features)
        
        # Asegurar que las columnas coincidan con el modelo
        missing_cols = set(model.feature_names_in_) - set(X_future.columns)
        for col in missing_cols:
            X_future[col] = 0
        
        X_future = X_future[model.feature_names_in_]
        
        # Predicciones
        predictions = model.predict(X_future)
        
        # Crear DataFrame de resultados
        results_df = pd.DataFrame({
            'date': future_dates,
            'location': location_name,
            'parameter': target_parameter,
            'predicted_value': predictions
        })
        
        print(f"✓ Predicciones generadas para {len(future_dates)} fechas")
        return results_df
    
    def save_model(self, model, target_parameter, filepath):
        """
        Guardar modelo entrenado
        
        Args:
            model: Modelo a guardar
            target_parameter (str): Parámetro objetivo
            filepath (str): Ruta donde guardar el modelo
        """
        try:
            joblib.dump(model, filepath)
            print(f"✓ Modelo guardado en: {filepath}")
        except Exception as e:
            print(f"✗ Error al guardar modelo: {e}")
    
    def load_model(self, filepath):
        """
        Cargar modelo guardado
        
        Args:
            filepath (str): Ruta del modelo
            
        Returns:
            Modelo cargado
        """
        try:
            model = joblib.load(filepath)
            print(f"✓ Modelo cargado desde: {filepath}")
            return model
        except Exception as e:
            print(f"✗ Error al cargar modelo: {e}")
            return None
    
    def generate_recommendations(self, predicted_value, target_parameter):
        """
        Generar recomendaciones basadas en predicciones
        
        Args:
            predicted_value (float): Valor predicho
            target_parameter (str): Parámetro objetivo
            
        Returns:
            dict: Recomendaciones
        """
        # Estándares EPA simplificados
        if target_parameter.lower() == 'pm25':
            if predicted_value <= 12.0:
                recommendation = "Excelente calidad del aire. Actividades al aire libre sin restricciones."
                activity_level = "Sin restricciones"
            elif predicted_value <= 35.4:
                recommendation = "Calidad del aire moderada. Personas sensibles deben considerar reducir actividades al aire libre."
                activity_level = "Moderadas restricciones"
            elif predicted_value <= 55.4:
                recommendation = "No saludable para grupos sensibles. Evitar actividades al aire libre prolongadas."
                activity_level = "Restricciones significativas"
            else:
                recommendation = "Calidad del aire no saludable. Evitar TODAS las actividades al aire libre."
                activity_level = "Restricciones severas"
        
        elif target_parameter.lower() == 'o3':
            if predicted_value <= 0.054:
                recommendation = "Excelente calidad del aire. Actividades al aire libre sin restricciones."
                activity_level = "Sin restricciones"
            elif predicted_value <= 0.070:
                recommendation = "Calidad del aire moderada. Personas sensibles deben considerar reducir actividades al aire libre."
                activity_level = "Moderadas restricciones"
            elif predicted_value <= 0.085:
                recommendation = "No saludable para grupos sensibles. Evitar actividades al aire libre prolongadas."
                activity_level = "Restricciones significativas"
            else:
                recommendation = "Calidad del aire no saludable. Evitar TODAS las actividades al aire libre."
                activity_level = "Restricciones severas"
        
        else:
            recommendation = "Consultar estándares locales para este parámetro."
            activity_level = "No determinado"
        
        return {
            'recommendation': recommendation,
            'activity_level': activity_level,
            'predicted_value': predicted_value,
            'parameter': target_parameter
        }
