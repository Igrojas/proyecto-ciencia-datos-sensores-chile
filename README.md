# Análisis de Calidad del Aire - Santiago de Chile

## 📊 Descripción del Proyecto

Este proyecto realiza un análisis completo de ciencia de datos sobre la calidad del aire en Santiago de Chile y sus alrededores, utilizando datos obtenidos de la API de OpenAQ. El objetivo es identificar patrones, entrenar modelos de predicción y generar recomendaciones útiles para usuarios.

## 🎯 Objetivos

- **Exploración de datos**: Analizar la estructura y calidad de los datos de calidad del aire
- **Análisis temporal**: Identificar patrones estacionales y horarios
- **Modelado predictivo**: Entrenar modelos para predecir parámetros de calidad del aire
- **Generación de recomendaciones**: Crear un sistema de alertas y recomendaciones para usuarios
- **Aplicaciones prácticas**: Desarrollar herramientas útiles para la toma de decisiones

## 🏗️ Estructura del Proyecto

```
Proyecto en Ciencia de datos/
├── data/                          # Datos del proyecto
│   ├── raw/                       # Datos originales
│   │   └── santiago_openaq_20250815_091808.csv
│   ├── processed/                 # Datos procesados
│   └── interim/                   # Datos intermedios
├── notebooks/                     # Jupyter notebooks de análisis
│   ├── 01_exploracion_datos.py   # Exploración inicial de datos
│   └── 02_prediccion_recomendaciones.py  # Análisis de predicción
├── src/                          # Código fuente
│   └── data_utils.py             # Utilidades para procesamiento de datos
├── models/                       # Modelos entrenados
│   └── air_quality_predictor.py # Clase para predicción
├── reports/                      # Reportes y visualizaciones
├── openaq_santiago_final.py      # Script original de recolección
├── main_analysis.py              # Script principal de análisis
├── requirements.txt              # Dependencias del proyecto
└── README.md                     # Este archivo
```

## 🚀 Instalación y Configuración

### 1. Clonar el repositorio
```bash
git clone <url-del-repositorio>
cd "Proyecto en Ciencia de datos"
```

### 2. Crear entorno virtual (recomendado)
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar API Key
El proyecto ya incluye la API key de OpenAQ en los scripts. Si deseas usar tu propia key, modifica la variable `API_KEY` en los archivos correspondientes.

## 📈 Uso del Proyecto

### Análisis Exploratorio
```bash
python notebooks/01_exploracion_datos.py
```

### Análisis de Predicción y Recomendaciones
```bash
python notebooks/02_prediccion_recomendaciones.py
```

### Análisis Completo
```bash
python main_analysis.py
```

## 🔍 Características del Análisis

### 1. **Exploración de Datos**
- Carga y limpieza de datos
- Análisis estadístico descriptivo
- Detección de valores atípicos
- Análisis de correlaciones entre parámetros

### 2. **Análisis Temporal**
- Patrones estacionales (mensuales)
- Patrones horarios
- Evolución temporal de contaminantes
- Variabilidad interanual

### 3. **Modelado Predictivo**
- **Algoritmos utilizados**:
  - Random Forest
  - Gradient Boosting
  - Regresión Lineal
  - Ridge/Lasso
  - Support Vector Regression
- **Características del modelo**:
  - Variables temporales (año, mes, día, hora)
  - Características cíclicas (seno/coseno)
  - Ubicación geográfica
  - Ajuste de hiperparámetros

### 4. **Parámetros Analizados**
- **PM2.5**: Partículas finas (prioridad alta)
- **PM10**: Partículas en suspensión (prioridad alta)
- **O3**: Ozono (prioridad media)
- **NO2**: Dióxido de nitrógeno (prioridad media)
- **SO2**: Dióxido de azufre
- **CO**: Monóxido de carbono

### 5. **Sistema de Recomendaciones**
- Índices de calidad del aire basados en estándares EPA
- Recomendaciones personalizadas por nivel de contaminación
- Alertas para actividades al aire libre
- Sugerencias para grupos sensibles

## 📊 Resultados y Salidas

### Archivos Generados
- **Datos procesados**: CSV con características temporales
- **Modelos entrenados**: Archivos .pkl de los mejores modelos
- **Predicciones**: CSV con valores futuros predichos
- **Visualizaciones**: Gráficos PNG de patrones temporales
- **Reportes**: Archivos de texto con análisis detallado

### Métricas de Modelos
- **R² Score**: Coeficiente de determinación
- **RMSE**: Error cuadrático medio
- **MAE**: Error absoluto medio
- **Importancia de características**: Ranking de variables más relevantes

## 🎯 Aplicaciones Prácticas

### 1. **Para Usuarios Individuales**
- Monitoreo en tiempo real de calidad del aire
- Planificación de actividades al aire libre
- Alertas personalizadas según sensibilidad
- Recomendaciones de uso de mascarillas

### 2. **Para Instituciones**
- Planificación de actividades escolares
- Gestión de eventos deportivos
- Protocolos de salud ocupacional
- Monitoreo ambiental continuo

### 3. **Para Políticas Públicas**
- Análisis de tendencias de contaminación
- Evaluación de efectividad de medidas
- Planificación urbana y transporte
- Alertas de emergencia ambiental

## 🔧 Personalización y Extensión

### Agregar Nuevos Parámetros
1. Modificar la lista `target_parameters` en `main_analysis.py`
2. Agregar estándares de calidad en `data_utils.py`
3. Actualizar funciones de recomendación

### Nuevos Modelos
1. Implementar en `air_quality_predictor.py`
2. Agregar a la función `train_models()`
3. Incluir en el ajuste de hiperparámetros

### Nuevas Ubicaciones
1. Modificar el script de recolección
2. Actualizar filtros geográficos
3. Reentrenar modelos con nuevos datos

## 📚 Dependencias Principales

- **openaq**: Cliente oficial de la API de OpenAQ
- **pandas**: Manipulación y análisis de datos
- **numpy**: Computación numérica
- **scikit-learn**: Machine learning y modelado
- **matplotlib/seaborn**: Visualización de datos
- **joblib**: Persistencia de modelos

## 🤝 Contribuciones

Para contribuir al proyecto:

1. Fork del repositorio
2. Crear rama para nueva funcionalidad
3. Implementar cambios con tests
4. Crear Pull Request con descripción detallada

## 📄 Licencia

Este proyecto está bajo licencia MIT. Ver archivo LICENSE para más detalles.

## 📞 Contacto

Para preguntas o sugerencias sobre el proyecto, crear un issue en el repositorio.

## 🙏 Agradecimientos

- **OpenAQ**: Por proporcionar acceso a datos de calidad del aire
- **Comunidad de ciencia de datos**: Por las librerías y herramientas utilizadas
- **Santiago de Chile**: Por ser el caso de estudio de este proyecto

---

**Nota**: Este proyecto es educativo y de investigación. Las recomendaciones de salud deben ser validadas por profesionales médicos y autoridades sanitarias locales.
