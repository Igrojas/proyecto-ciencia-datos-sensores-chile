#!/usr/bin/env python3
"""
Generador de Recomendaciones para Usuarios Finales - Calidad del Aire
Sistema de alertas y recomendaciones basado en datos de contaminación
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Configuración
plt.style.use('default')
sns.set_palette("husl")

def cargar_datos_analizados():
    """
    Cargar datos ya analizados para generar recomendaciones
    """
    print("=== CARGANDO DATOS PARA RECOMENDACIONES ===\n")
    
    try:
        df = pd.read_csv('../data/localidades_especificas_20250817_222931.csv')
        print(f"✓ Datos cargados: {len(df):,} mediciones")
        
        # Convertir fechas
        df['fecha_desde_utc'] = pd.to_datetime(df['fecha_desde_utc'])
        
        # Crear features temporales
        df['mes'] = df['fecha_desde_utc'].dt.month
        df['hora'] = df['fecha_desde_utc'].dt.hour
        df['dia_semana'] = df['fecha_desde_utc'].dt.dayofweek
        df['estacion'] = df['fecha_desde_utc'].dt.month.map({
            12: 'Verano', 1: 'Verano', 2: 'Verano',
            3: 'Otoño', 4: 'Otoño', 5: 'Otoño',
            6: 'Invierno', 7: 'Invierno', 8: 'Invierno',
            9: 'Primavera', 10: 'Primavera', 11: 'Primavera'
        })
        
        return df
        
    except FileNotFoundError:
        print("✗ No se encontró el archivo de datos")
        return None

def definir_umbrales_contaminacion():
    """
    Definir umbrales de contaminación según estándares internacionales
    """
    print(f"\n=== DEFINIENDO UMBRALES DE CONTAMINACIÓN ===")
    
    umbrales = {
        'pm25': {
            'excelente': 0,      # µg/m³
            'bueno': 12,         # µg/m³
            'moderado': 35.4,    # µg/m³
            'malo': 55.4,        # µg/m³
            'muy_malo': 150.4,   # µg/m³
            'peligroso': 250.4   # µg/m³
        },
        'pm10': {
            'excelente': 0,      # µg/m³
            'bueno': 54,         # µg/m³
            'moderado': 154,     # µg/m³
            'malo': 254,         # µg/m³
            'muy_malo': 354,     # µg/m³
            'peligroso': 424     # µg/m³
        },
        'no2': {
            'excelente': 0,      # ppb
            'bueno': 53,         # ppb
            'moderado': 100,     # ppb
            'malo': 360,         # ppb
            'muy_malo': 649,     # ppb
            'peligroso': 1249    # ppb
        },
        'o3': {
            'excelente': 0,      # ppb
            'bueno': 54,         # ppb
            'moderado': 70,      # ppb
            'malo': 85,          # ppb
            'muy_malo': 105,     # ppb
            'peligroso': 200     # ppb
        },
        'so2': {
            'excelente': 0,      # ppb
            'bueno': 35,         # ppb
            'moderado': 75,      # ppb
            'malo': 185,         # ppb
            'muy_malo': 304,     # ppb
            'peligroso': 604     # ppb
        },
        'co': {
            'excelente': 0,      # ppm
            'bueno': 4.4,        # ppm
            'moderado': 9.4,     # ppm
            'malo': 12.4,        # ppm
            'muy_malo': 15.4,    # ppm
            'peligroso': 30.4    # ppm
        }
    }
    
    print(f"✓ Umbrales definidos para {len(umbrales)} contaminantes")
    return umbrales

def clasificar_calidad_aire(valor, parametro, umbrales):
    """
    Clasificar la calidad del aire según el valor y parámetro
    """
    if parametro not in umbrales:
        return 'desconocido'
    
    umbral_param = umbrales[parametro]
    
    if valor <= umbral_param['excelente']:
        return 'excelente'
    elif valor <= umbral_param['bueno']:
        return 'bueno'
    elif valor <= umbral_param['moderado']:
        return 'moderado'
    elif valor <= umbral_param['malo']:
        return 'malo'
    elif valor <= umbral_param['muy_malo']:
        return 'muy_malo'
    elif valor <= umbral_param['peligroso']:
        return 'peligroso'
    else:
        return 'peligroso'

def generar_recomendaciones_salud(calidad, parametro):
    """
    Generar recomendaciones de salud según la calidad del aire
    """
    recomendaciones = {
        'excelente': {
            'actividad_fisica': '✅ Actividad física normal sin restricciones',
            'exposicion_exterior': '✅ Exposición exterior sin limitaciones',
            'ventilacion': '✅ Ventilación normal de espacios',
            'grupos_sensibles': '✅ Sin precauciones especiales necesarias'
        },
        'bueno': {
            'actividad_fisica': '✅ Actividad física normal',
            'exposicion_exterior': '✅ Exposición exterior normal',
            'ventilacion': '✅ Ventilación normal',
            'grupos_sensibles': '⚠ Personas sensibles pueden experimentar síntomas leves'
        },
        'moderado': {
            'actividad_fisica': '⚠ Reducir actividad física intensa al aire libre',
            'exposicion_exterior': '⚠ Limitada para personas sensibles',
            'ventilacion': '⚠ Ventilación moderada',
            'grupos_sensibles': '❌ Personas con problemas cardíacos o pulmonares deben limitar actividad'
        },
        'malo': {
            'actividad_fisica': '❌ Evitar actividad física al aire libre',
            'exposicion_exterior': '❌ Limitar exposición exterior',
            'ventilacion': '❌ Ventilación reducida',
            'grupos_sensibles': '❌ Permanecer en interiores, consultar médico si síntomas'
        },
        'muy_malo': {
            'actividad_fisica': '❌ NO realizar actividad física al aire libre',
            'exposicion_exterior': '❌ Minimizar exposición exterior',
            'ventilacion': '❌ Ventilación mínima',
            'grupos_sensibles': '❌ Permanecer en interiores, usar purificadores de aire'
        },
        'peligroso': {
            'actividad_fisica': '🚨 PROHIBIDO actividad física al aire libre',
            'exposicion_exterior': '🚨 EVITAR exposición exterior',
            'ventilacion': '🚨 Sin ventilación exterior',
            'grupos_sensibles': '🚨 Permanecer en interiores, considerar evacuación'
        }
    }
    
    return recomendaciones.get(calidad, {})

def generar_recomendaciones_especificas_parametro(parametro, valor, calidad):
    """
    Generar recomendaciones específicas por parámetro
    """
    recomendaciones_especificas = {
        'pm25': {
            'descripcion': 'Material particulado fino (2.5 micrómetros)',
            'fuentes': 'Combustión de vehículos, industrias, incendios forestales',
            'efectos': 'Penetra profundamente en los pulmones, afecta sistema cardiovascular',
            'acciones': 'Usar mascarilla N95, evitar zonas de alto tráfico'
        },
        'pm10': {
            'descripcion': 'Material particulado grueso (10 micrómetros)',
            'fuentes': 'Polvo, construcción, agricultura, tráfico',
            'efectos': 'Irrita vías respiratorias, puede agravar asma',
            'acciones': 'Usar mascarilla, mantener ventanas cerradas'
        },
        'no2': {
            'descripcion': 'Dióxido de nitrógeno',
            'fuentes': 'Tráfico vehicular, centrales eléctricas, industrias',
            'efectos': 'Irrita pulmones, reduce función pulmonar',
            'acciones': 'Evitar zonas de alto tráfico, usar transporte público'
        },
        'o3': {
            'descripcion': 'Ozono troposférico',
            'fuentes': 'Reacciones químicas con contaminantes en presencia de luz solar',
            'efectos': 'Irrita vías respiratorias, reduce función pulmonar',
            'acciones': 'Limitar actividad al aire libre en horas de sol intenso'
        },
        'so2': {
            'descripcion': 'Dióxido de azufre',
            'fuentes': 'Combustión de carbón, petróleo, industrias',
            'efectos': 'Irrita vías respiratorias, puede agravar asma',
            'acciones': 'Usar mascarilla, evitar zonas industriales'
        },
        'co': {
            'descripcion': 'Monóxido de carbono',
            'fuentes': 'Combustión incompleta, tráfico, calefacción',
            'efectos': 'Reduce oxigenación de la sangre, puede ser fatal',
            'acciones': 'Evitar zonas de alto tráfico, verificar calefacción'
        }
    }
    
    return recomendaciones_especificas.get(parametro, {})

def analizar_patrones_temporales(df, parametro, localidad):
    """
    Analizar patrones temporales para generar alertas
    """
    print(f"\n=== ANALIZANDO PATRONES TEMPORALES PARA {parametro} en {localidad} ===")
    
    # Filtrar datos
    df_filtrado = df[(df['parametro_nombre'] == parametro) & 
                     (df['localidad_buscada'] == localidad)].copy()
    
    if len(df_filtrado) < 100:
        print(f"⚠ Datos insuficientes para análisis temporal")
        return None
    
    # Crear pivot table temporal
    pivot_df = df_filtrado.pivot_table(
        index='fecha_desde_utc',
        values='valor',
        aggfunc='mean'
    ).fillna(method='ffill').fillna(method='bfill')
    
    # Análisis por hora del día
    df_filtrado['hora'] = df_filtrado['fecha_desde_utc'].dt.hour
    patrones_hora = df_filtrado.groupby('hora')['valor'].agg(['mean', 'std', 'max']).round(2)
    
    # Análisis por día de la semana
    df_filtrado['dia_semana'] = df_filtrado['fecha_desde_utc'].dt.dayofweek
    dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    patrones_dia = df_filtrado.groupby('dia_semana')['valor'].agg(['mean', 'std', 'max']).round(2)
    patrones_dia.index = dias_semana
    
    # Análisis por mes/estación
    patrones_mes = df_filtrado.groupby('mes')['valor'].agg(['mean', 'std', 'max']).round(2)
    
    print(f"✓ Patrones temporales analizados")
    print(f"\nPatrones por hora del día (Top 5 más contaminadas):")
    print(patrones_hora.sort_values('mean', ascending=False).head())
    
    print(f"\nPatrones por día de la semana:")
    print(patrones_dia.sort_values('mean', ascending=False))
    
    print(f"\nPatrones por mes:")
    print(patrones_mes.sort_values('mean', ascending=False))
    
    return {
        'patrones_hora': patrones_hora,
        'patrones_dia': patrones_dia,
        'patrones_mes': patrones_mes,
        'serie_temporal': pivot_df
    }

def generar_sistema_alertas(df, umbrales, parametro='pm25', localidad='Indura'):
    """
    Generar sistema de alertas para usuarios
    """
    print(f"\n=== GENERANDO SISTEMA DE ALERTAS PARA {parametro} en {localidad} ===")
    
    # Filtrar datos recientes (últimos 30 días)
    fecha_limite = datetime.now() - timedelta(days=30)
    df_reciente = df[(df['parametro_nombre'] == parametro) & 
                     (df['localidad_buscada'] == localidad) &
                     (df['fecha_desde_utc'] >= fecha_limite)].copy()
    
    if len(df_reciente) == 0:
        print(f"⚠ No hay datos recientes para generar alertas")
        return None
    
    # Clasificar calidad del aire
    df_reciente['calidad'] = df_reciente['valor'].apply(
        lambda x: clasificar_calidad_aire(x, parametro, umbrales)
    )
    
    # Generar alertas
    alertas = []
    
    # Alerta por calidad actual
    calidad_actual = df_reciente['calidad'].iloc[-1]
    valor_actual = df_reciente['valor'].iloc[-1]
    
    alertas.append({
        'tipo': 'calidad_actual',
        'nivel': 'info',
        'mensaje': f'Calidad del aire actual: {calidad_actual.upper()}',
        'valor': valor_actual,
        'parametro': parametro,
        'localidad': localidad,
        'fecha': df_reciente['fecha_desde_utc'].iloc[-1]
    })
    
    # Alerta por tendencia
    if len(df_reciente) >= 7:
        ultima_semana = df_reciente.tail(7)['valor'].mean()
        semana_anterior = df_reciente.iloc[-14:-7]['valor'].mean()
        
        if ultima_semana > semana_anterior * 1.2:
            alertas.append({
                'tipo': 'tendencia',
                'nivel': 'warning',
                'mensaje': '⚠ Tendencia al alza en contaminación',
                'valor_actual': ultima_semana,
                'valor_anterior': semana_anterior,
                'cambio': f"+{((ultima_semana/semana_anterior - 1) * 100):.1f}%"
            })
        elif ultima_semana < semana_anterior * 0.8:
            alertas.append({
                'tipo': 'tendencia',
                'nivel': 'success',
                'mensaje': '✅ Mejora en la calidad del aire',
                'valor_actual': ultima_semana,
                'valor_anterior': semana_anterior,
                'cambio': f"-{((1 - ultima_semana/semana_anterior) * 100):.1f}%"
            })
    
    # Alerta por valores extremos
    valor_max = df_reciente['valor'].max()
    if valor_max > umbrales[parametro]['muy_malo']:
        alertas.append({
            'tipo': 'valor_extremo',
            'nivel': 'danger',
            'mensaje': '🚨 Valores extremadamente altos detectados',
            'valor_max': valor_max,
            'fecha_max': df_reciente.loc[df_reciente['valor'].idxmax(), 'fecha_desde_utc']
        })
    
    print(f"✓ Sistema de alertas generado: {len(alertas)} alertas")
    
    # Mostrar alertas
    for alerta in alertas:
        nivel_icono = {
            'info': 'ℹ️',
            'success': '✅',
            'warning': '⚠️',
            'danger': '🚨'
        }
        print(f"\n{nivel_icono.get(alerta['nivel'], 'ℹ️')} {alerta['mensaje']}")
        if 'valor' in alerta:
            print(f"   Valor: {alerta['valor']:.2f}")
        if 'cambio' in alerta:
            print(f"   Cambio: {alerta['cambio']}")
    
    return alertas

def crear_dashboard_recomendaciones(df, umbrales, parametro='pm25', localidad='Indura'):
    """
    Crear dashboard visual de recomendaciones
    """
    print(f"\n=== CREANDO DASHBOARD DE RECOMENDACIONES ===")
    
    # Configurar subplots
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle(f'Dashboard de Calidad del Aire - {parametro} en {localidad}', fontsize=16)
    
    # Filtrar datos
    df_filtrado = df[(df['parametro_nombre'] == parametro) & 
                     (df['localidad_buscada'] == localidad)].copy()
    
    if len(df_filtrado) == 0:
        print(f"⚠ No hay datos para crear dashboard")
        return
    
    # 1. Evolución temporal con umbrales
    ax1 = axes[0, 0]
    df_filtrado = df_filtrado.sort_values('fecha_desde_utc')
    
    # Graficar valores
    ax1.plot(df_filtrado['fecha_desde_utc'], df_filtrado['valor'], 
             alpha=0.7, linewidth=1, label='Valor medido')
    
    # Graficar umbrales
    umbral_param = umbrales[parametro]
    colores = ['green', 'yellow', 'orange', 'red', 'purple', 'brown']
    niveles = ['bueno', 'moderado', 'malo', 'muy_malo', 'peligroso']
    
    for i, nivel in enumerate(niveles):
        if nivel in umbral_param:
            ax1.axhline(y=umbral_param[nivel], color=colores[i], linestyle='--', 
                       alpha=0.7, label=f'Umbral {nivel}')
    
    ax1.set_xlabel('Fecha')
    ax1.set_ylabel(f'{parametro.upper()} ({df_filtrado["unidad"].iloc[0]})')
    ax1.set_title('Evolución Temporal con Umbrales de Calidad')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
    
    # 2. Distribución de valores por calidad
    ax2 = axes[0, 1]
    df_filtrado['calidad'] = df_filtrado['valor'].apply(
        lambda x: clasificar_calidad_aire(x, parametro, umbrales)
    )
    
    calidad_counts = df_filtrado['calidad'].value_counts()
    colores_calidad = ['green', 'lightgreen', 'yellow', 'orange', 'red', 'darkred']
    
    ax2.bar(calidad_counts.index, calidad_counts.values, 
            color=colores_calidad[:len(calidad_counts)], alpha=0.8)
    ax2.set_xlabel('Calidad del Aire')
    ax2.set_ylabel('Número de Mediciones')
    ax2.set_title('Distribución por Calidad del Aire')
    ax2.grid(True, alpha=0.3)
    
    # 3. Patrones por hora del día
    ax3 = axes[1, 0]
    df_filtrado['hora'] = df_filtrado['fecha_desde_utc'].dt.hour
    patrones_hora = df_filtrado.groupby('hora')['valor'].mean()
    
    ax3.plot(patrones_hora.index, patrones_hora.values, 
             marker='o', linewidth=2, markersize=6)
    ax3.set_xlabel('Hora del Día')
    ax3.set_ylabel(f'{parametro.upper()} Promedio')
    ax3.set_title('Patrones por Hora del Día')
    ax3.grid(True, alpha=0.3)
    ax3.set_xticks(range(0, 24, 2))
    
    # 4. Patrones por mes
    ax4 = axes[1, 1]
    df_filtrado['mes'] = df_filtrado['fecha_desde_utc'].dt.month
    patrones_mes = df_filtrado.groupby('mes')['valor'].mean()
    
    meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 
             'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    
    ax4.bar(patrones_mes.index, patrones_mes.values, alpha=0.8)
    ax4.set_xlabel('Mes')
    ax4.set_ylabel(f'{parametro.upper()} Promedio')
    ax4.set_title('Patrones por Mes')
    ax4.grid(True, alpha=0.3)
    ax4.set_xticks(range(1, 13))
    ax4.set_xticklabels(meses)
    
    plt.tight_layout()
    plt.savefig('dashboard_recomendaciones_calidad_aire.png', dpi=300, bbox_inches='tight')
    print(f"✓ Dashboard guardado en: dashboard_recomendaciones_calidad_aire.png")
    
    plt.show()

def generar_reporte_final(df, umbrales, parametro='pm25', localidad='Indura'):
    """
    Generar reporte final completo de recomendaciones
    """
    print(f"\n=== GENERANDO REPORTE FINAL DE RECOMENDACIONES ===")
    
    # Filtrar datos
    df_filtrado = df[(df['parametro_nombre'] == parametro) & 
                     (df['localidad_buscada'] == localidad)].copy()
    
    if len(df_filtrado) == 0:
        print(f"⚠ No hay datos para generar reporte")
        return
    
    # Clasificar calidad del aire
    df_filtrado['calidad'] = df_filtrado['valor'].apply(
        lambda x: clasificar_calidad_aire(x, parametro, umbrales)
    )
    
    # Estadísticas generales
    valor_actual = df_filtrado['valor'].iloc[-1]
    calidad_actual = df_filtrado['calidad'].iloc[-1]
    valor_promedio = df_filtrado['valor'].mean()
    valor_max = df_filtrado['valor'].max()
    valor_min = df_filtrado['valor'].min()
    
    # Distribución de calidad
    distribucion_calidad = df_filtrado['calidad'].value_counts()
    
    # Generar reporte
    reporte = f"""
REPORTE FINAL DE RECOMENDACIONES - CALIDAD DEL AIRE
{'='*60}

📍 INFORMACIÓN GENERAL:
  - Parámetro: {parametro.upper()}
  - Localidad: {localidad}
  - Período analizado: {df_filtrado['fecha_desde_utc'].min()} a {df_filtrado['fecha_desde_utc'].max()}
  - Total de mediciones: {len(df_filtrado):,}

📊 ESTADÍSTICAS ACTUALES:
  - Valor actual: {valor_actual:.2f} {df_filtrado['unidad'].iloc[0]}
  - Calidad actual: {calidad_actual.upper()}
  - Valor promedio: {valor_promedio:.2f} {df_filtrado['unidad'].iloc[0]}
  - Valor máximo: {valor_max:.2f} {df_filtrado['unidad'].iloc[0]}
  - Valor mínimo: {valor_min:.2f} {df_filtrado['unidad'].iloc[0]}

🎯 DISTRIBUCIÓN DE CALIDAD:
"""
    
    for calidad, count in distribucion_calidad.items():
        porcentaje = (count / len(df_filtrado)) * 100
        reporte += f"  - {calidad.upper()}: {count} mediciones ({porcentaje:.1f}%)\n"
    
    # Recomendaciones de salud
    recomendaciones_salud = generar_recomendaciones_salud(calidad_actual, parametro)
    reporte += f"""
🏥 RECOMENDACIONES DE SALUD ACTUALES:
  - Actividad física: {recomendaciones_salud.get('actividad_fisica', 'N/A')}
  - Exposición exterior: {recomendaciones_salud.get('exposicion_exterior', 'N/A')}
  - Ventilación: {recomendaciones_salud.get('ventilacion', 'N/A')}
  - Grupos sensibles: {recomendaciones_salud.get('grupos_sensibles', 'N/A')}

🔍 INFORMACIÓN ESPECÍFICA DEL CONTAMINANTE:
"""
    
    info_parametro = generar_recomendaciones_especificas_parametro(parametro, valor_actual, calidad_actual)
    for key, value in info_parametro.items():
        reporte += f"  - {key.replace('_', ' ').title()}: {value}\n"
    
    # Alertas
    alertas = generar_sistema_alertas(df, umbrales, parametro, localidad)
    if alertas:
        reporte += f"""
🚨 ALERTAS ACTIVAS:
"""
        for alerta in alertas:
            reporte += f"  - {alerta['mensaje']}\n"
    
    # Recomendaciones generales
    reporte += f"""
💡 RECOMENDACIONES GENERALES:
  1. Monitorear calidad del aire regularmente
  2. Seguir las recomendaciones de salud según el nivel actual
  3. Planificar actividades al aire libre en horarios de mejor calidad
  4. Usar mascarillas cuando sea necesario
  5. Mantener espacios interiores bien ventilados
  6. Considerar purificadores de aire para espacios cerrados

📱 ACCIONES INMEDIATAS:
  - Nivel actual: {calidad_actual.upper()}
  - Acción recomendada: {recomendaciones_salud.get('actividad_fisica', 'Consultar médico')}
  - Próxima verificación: En 1-2 horas

---
Reporte generado el: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Parámetro: {parametro.upper()}
Localidad: {localidad}
"""
    
    # Guardar reporte
    nombre_archivo = f'reporte_recomendaciones_{parametro}_{localidad}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
    with open(nombre_archivo, 'w', encoding='utf-8') as f:
        f.write(reporte)
    
    print(f"✓ Reporte guardado en: {nombre_archivo}")
    
    # Mostrar resumen
    print(f"\n📋 RESUMEN DEL REPORTE:")
    print(f"  - Calidad actual: {calidad_actual.upper()}")
    print(f"  - Valor: {valor_actual:.2f} {df_filtrado['unidad'].iloc[0]}")
    print(f"  - Alertas activas: {len(alertas) if alertas else 0}")
    print(f"  - Recomendación principal: {recomendaciones_salud.get('actividad_fisica', 'N/A')}")
    
    return reporte

def main():
    """
    Función principal del generador de recomendaciones
    """
    print("🚀 INICIANDO GENERADOR DE RECOMENDACIONES PARA USUARIOS FINALES")
    
    # 1. Cargar datos
    df = cargar_datos_analizados()
    if df is None:
        return
    
    # 2. Definir umbrales
    umbrales = definir_umbrales_contaminacion()
    
    # 3. Parámetros y localidades a analizar
    parametros_analizar = ['pm25', 'pm10', 'no2', 'o3']
    localidades_analizar = ['Indura', 'JUNJI', 'ENAP Price', 'Bocatoma']
    
    # 4. Generar análisis para cada combinación
    for parametro in parametros_analizar:
        for localidad in localidades_analizar:
            print(f"\n{'='*60}")
            print(f"ANALIZANDO: {parametro.upper()} en {localidad}")
            print(f"{'='*60}")
            
            # Analizar patrones temporales
            patrones = analizar_patrones_temporales(df, parametro, localidad)
            
            # Generar sistema de alertas
            alertas = generar_sistema_alertas(df, umbrales, parametro, localidad)
            
            # Crear dashboard
            crear_dashboard_recomendaciones(df, umbrales, parametro, localidad)
            
            # Generar reporte final
            reporte = generar_reporte_final(df, umbrales, parametro, localidad)
            
            print(f"\n✅ Análisis completado para {parametro} en {localidad}")
    
    print(f"\n🎉 GENERACIÓN DE RECOMENDACIONES COMPLETADA")
    print(f"Se han generado reportes para {len(parametros_analizar)} parámetros")
    print(f"en {len(localidades_analizar)} localidades")

if __name__ == "__main__":
    main()
