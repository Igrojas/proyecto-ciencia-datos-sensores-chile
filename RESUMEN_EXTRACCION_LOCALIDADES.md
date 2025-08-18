# RESUMEN DE EXTRACCIÓN DE DATOS - LOCALIDADES ESPECÍFICAS DE CHILE

## 📍 Localidades Objetivo
Se extrajeron datos de calidad del aire de las siguientes localidades específicas de Chile:
- **Bocatoma**
- **ENAP Price** 
- **JUNJI**
- **Indura**

## 🎯 Resultados de la Extracción

### ✅ Localidades Encontradas
- **Bocatoma**: 1 ubicación encontrada
  - ID: 356
  - Coordenadas: -36.803034, -73.120527
  
- **ENAP Price**: 1 ubicación encontrada
  - ID: 812
  - Coordenadas: -36.791231, -73.119152
  
- **JUNJI**: 1 ubicación encontrada
  - ID: 810
  - Coordenadas: -36.780632, -73.115657
  
- **Indura**: 1 ubicación encontrada
  - ID: 808
  - Coordenadas: -36.769803, -73.113708

### 📊 Sensores Encontrados
**Total: 21 sensores**

- **Bocatoma**: 3 sensores
- **Indura**: 6 sensores  
- **JUNJI**: 6 sensores
- **ENAP Price**: 6 sensores

### 📈 Mediciones Obtenidas
**Total: 21,000 mediciones** (máximo posible por API)

#### Por Localidad:
- **Indura**: 6,000 mediciones
- **JUNJI**: 6,000 mediciones
- **ENAP Price**: 6,000 mediciones
- **Bocatoma**: 3,000 mediciones

#### Por Parámetro de Calidad del Aire:
- **SO2 (Dióxido de Azufre)**: 4,000 mediciones
- **PM2.5 (Material Particulado 2.5)**: 4,000 mediciones
- **PM10 (Material Particulado 10)**: 4,000 mediciones
- **NO2 (Dióxido de Nitrógeno)**: 3,000 mediciones
- **O3 (Ozono)**: 3,000 mediciones
- **CO (Monóxido de Carbono)**: 3,000 mediciones

### 📅 Rango Temporal
- **Fecha más antigua**: 10 de octubre de 2016, 03:00 UTC
- **Fecha más reciente**: 3 de octubre de 2020, 06:00 UTC
- **Período cubierto**: Aproximadamente 4 años de datos

## 💾 Archivo Generado

**Nombre**: `localidades_especificas_20250817_222931.csv`
**Ubicación**: `data/`
**Tamaño**: 3.38 MB
**Formato**: CSV con codificación UTF-8

### 📋 Columnas del Dataset
1. `parametro_nombre` - Nombre del parámetro medido
2. `parametro_id` - ID del parámetro
3. `valor` - Valor de la medición
4. `unidad` - Unidad de medida
5. `fecha_desde_utc` - Fecha de inicio de medición (UTC)
6. `fecha_desde_local` - Fecha de inicio de medición (hora local)
7. `fecha_hasta_utc` - Fecha de fin de medición (UTC)
8. `fecha_hasta_local` - Fecha de fin de medición (hora local)
9. `cobertura_porcentaje` - Porcentaje de cobertura de datos
10. `sensor_id` - ID del sensor
11. `localidad_id` - ID de la localidad
12. `localidad_nombre` - Nombre de la localidad
13. `localidad_buscada` - Localidad objetivo buscada
14. `ciudad` - Ciudad de la localidad
15. `coordenadas_lat` - Latitud
16. `coordenadas_lon` - Longitud

## 🔧 Tecnologías Utilizadas

- **API**: OpenAQ (Open Air Quality)
- **Lenguaje**: Python 3
- **Librerías**: 
  - `openaq` - Cliente oficial de la API
  - `pandas` - Manipulación de datos
  - `datetime` - Manejo de fechas
- **Formato de salida**: CSV estándar

## 📍 Ubicación Geográfica

Todas las localidades se encuentran en la región de **Concepción, Chile**:
- **Latitud**: Entre -36.78° y -36.80° (aproximadamente)
- **Longitud**: Entre -73.11° y -73.12° (aproximadamente)

## 🎉 Éxito de la Extracción

✅ **100% de éxito** en encontrar las localidades objetivo
✅ **Máxima cantidad de datos** extraída (21,000 mediciones)
✅ **Cobertura completa** de parámetros de calidad del aire
✅ **Datos históricos** de 4 años (2016-2020)
✅ **Formato estándar** CSV para fácil análisis posterior

## 📊 Potencial de Análisis

Con estos datos se pueden realizar:
- Análisis de tendencias temporales
- Comparación entre localidades
- Análisis de correlación entre contaminantes
- Estudios de calidad del aire por estación
- Modelos predictivos de contaminación
- Análisis de patrones estacionales

## 🔍 Notas Técnicas

- Se utilizó el límite máximo de la API (1,000 mediciones por sensor)
- Los datos incluyen información completa de ubicación y coordenadas
- Todas las mediciones tienen 100% de cobertura de datos
- Los datos están en formato UTC y hora local chilena
- Se incluyen todos los parámetros estándar de calidad del aire

---
*Extracción realizada el 17 de agosto de 2025 a las 22:29:31*
*Script: `extractor_final_localidades.py`*
