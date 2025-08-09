# 🌍 Extractor de Datos de Calidad del Aire - OpenAQ

Este proyecto te permite extraer datos de calidad del aire de múltiples ciudades del mundo utilizando la API de OpenAQ. 

## 📋 Características

- ✅ Extracción de datos de calidad del aire de +80 países
- ✅ Filtros por país, ciudad, contaminante y fecha
- ✅ Soporte para múltiples contaminantes (PM2.5, PM10, O3, NO2, SO2, CO)
- ✅ Exportación a CSV y Excel
- ✅ Análisis estadístico de los datos
- ✅ Interfaz fácil de usar con parámetros personalizables

## 🚀 Instalación

1. **Clona o descarga los archivos**
2. **Instala las dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Obtén tu clave de API:**
   - Regístrate en: [https://explore.openaq.org/register](https://explore.openaq.org/register)
   - Ve a tu cuenta: [https://explore.openaq.org/account](https://explore.openaq.org/account)
   - Copia tu clave de API

## 📖 Uso Básico

### Ejemplo simple

```python
from openaq_extractor import OpenAQExtractor
from datetime import datetime, timedelta

# Inicializar con tu API key
api_key = "tu_clave_de_api_aqui"
extractor = OpenAQExtractor(api_key)

# Obtener datos de PM2.5 de Madrid en la última semana
fecha_fin = datetime.now().strftime('%Y-%m-%d')
fecha_inicio = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

datos = extractor.get_measurements(
    country='ES',           # España
    city='Madrid',          # Ciudad específica
    parameter='pm25',       # Contaminante PM2.5
    date_from=fecha_inicio, # Fecha inicio
    date_to=fecha_fin,      # Fecha fin
    limit=1000              # Máximo registros
)

# Guardar datos
extractor.save_to_csv(datos, 'madrid_pm25.csv')
```

### Parámetros disponibles

#### Países (códigos ISO):
- `'ES'` - España
- `'US'` - Estados Unidos  
- `'MX'` - México
- `'FR'` - Francia
- `'DE'` - Alemania
- Y muchos más...

#### Contaminantes:
- `'pm25'` - Partículas PM2.5 (µg/m³)
- `'pm10'` - Partículas PM10 (µg/m³)
- `'o3'` - Ozono (µg/m³)
- `'no2'` - Dióxido de nitrógeno (µg/m³)
- `'so2'` - Dióxido de azufre (µg/m³)
- `'co'` - Monóxido de carbono (µg/m³)

## 🔧 Funciones Principales

### 1. get_measurements()
Función principal para obtener mediciones:

```python
datos = extractor.get_measurements(
    country='ES',                           # Código del país
    city='Barcelona',                       # Ciudad (opcional)
    location='ES0001R',                     # Estación específica (opcional)
    parameter=['pm25', 'pm10', 'o3'],      # Lista de contaminantes
    date_from='2024-01-01',                 # Fecha inicio
    date_to='2024-01-31',                   # Fecha fin
    limit=5000,                             # Registros por página
    max_pages=10                            # Máximo páginas
)
```

### 2. get_countries()
Obtiene lista de países disponibles:

```python
paises = extractor.get_countries()
for pais in paises:
    print(f"{pais['name']} ({pais['code']})")
```

### 3. get_cities()
Obtiene ciudades de un país:

```python
ciudades = extractor.get_cities(country_code='ES')
for ciudad in ciudades:
    print(f"{ciudad['city']} - {ciudad['count']} mediciones")
```

### 4. get_parameters()
Lista todos los contaminantes disponibles:

```python
parametros = extractor.get_parameters()
for param in parametros:
    print(f"{param['displayName']} ({param['id']})")
```

## 📊 Ejemplos Avanzados

### Múltiples ciudades
```python
ciudades = ['Madrid', 'Barcelona', 'Valencia']
datos_consolidados = []

for ciudad in ciudades:
    datos = extractor.get_measurements(
        country='ES',
        city=ciudad,
        parameter=['pm25', 'no2'],
        date_from='2024-01-01',
        date_to='2024-01-07'
    )
    datos_consolidados.append(datos)

# Combinar todos los datos
import pandas as pd
df_final = pd.concat(datos_consolidados, ignore_index=True)
```

### Análisis estadístico
```python
# Obtener resumen de datos
resumen = extractor.get_data_summary(datos)
print(f"Total registros: {resumen['total_registros']}")
print(f"Fechas: {resumen['fechas']}")
print(f"Estadísticas por parámetro: {resumen['estadisticas_por_parametro']}")

# Análisis con pandas
promedios_diarios = datos.groupby('fecha')['value'].mean()
maximos_por_ciudad = datos.groupby('city')['value'].max()
```

### Exportar a Excel
```python
# Guardar en Excel con múltiples hojas
with pd.ExcelWriter('calidad_aire.xlsx') as writer:
    datos_pm25 = datos[datos['parameter'] == 'pm25']
    datos_no2 = datos[datos['parameter'] == 'no2']
    
    datos_pm25.to_excel(writer, sheet_name='PM2.5', index=False)
    datos_no2.to_excel(writer, sheet_name='NO2', index=False)
```

## 📁 Archivos del Proyecto

- `openaq_extractor.py` - Clase principal del extractor
- `ejemplo_uso_openaq.py` - Ejemplos prácticos de uso
- `requirements.txt` - Dependencias necesarias
- `README.md` - Esta documentación

## ⚠️ Consideraciones Importantes

1. **API Key requerida**: Necesitas registrarte en OpenAQ para obtener una clave gratuita
2. **Límites de tasa**: La API tiene límites de velocidad, el código incluye pausas automáticas
3. **Datos en tiempo real**: Los datos pueden tener retrasos de algunas horas
4. **Disponibilidad por región**: No todas las ciudades tienen todos los contaminantes

## 🌟 Ejemplos de Casos de Uso

### Investigación académica
```python
# Comparar calidad del aire entre capitales europeas
capitales = ['Madrid', 'Paris', 'Berlin', 'Rome']
# ... código para obtener y comparar datos
```

### Monitoreo de salud pública
```python
# Obtener datos de PM2.5 para evaluación de riesgos
datos_pm25 = extractor.get_measurements(
    country='MX',
    parameter='pm25',
    date_from='2024-01-01',
    date_to='2024-12-31'
)
```

### Análisis de tendencias
```python
# Evaluar cambios en la calidad del aire durante varios años
for año in range(2020, 2025):
    datos_año = extractor.get_measurements(
        country='US',
        city='Los Angeles',
        date_from=f'{año}-01-01',
        date_to=f'{año}-12-31'
    )
    # ... análisis de tendencias
```

## 🆘 Solución de Problemas

### Error de autenticación
```
Error 401: Unauthorized
```
- Verifica que tu API key sea correcta
- Asegúrate de haberla configurado en el código

### Sin datos devueltos
```
No se encontraron datos
```
- Verifica que los parámetros sean correctos
- Prueba con un rango de fechas más amplio
- Confirma que la ciudad/país tenga estaciones activas

### Límite de tasa excedido
```
Error 429: Too Many Requests
```
- Reduce la frecuencia de consultas
- Aumenta el parámetro `time.sleep()` entre peticiones

## 📚 Recursos Adicionales

- [Documentación oficial de OpenAQ](https://docs.openaq.org/)
- [Explorador web de datos](https://explore.openaq.org/)
- [API de OpenAQ](https://docs.openaq.org/reference)

## 📄 Licencia

Este proyecto es de uso libre para fines educativos y de investigación.

---

¡Disfruta explorando los datos de calidad del aire del mundo! 🌍✨
