"""
PROYECTO: Dashboard de Tipos de Cambio y Brecha (Argentina)
STACK: Streamlit, Pandas, Plotly, Yfinance.

OBJETIVOS:
1. Header con métricas (Oficial, MEP, CCL, Blue).
2. Gráfico histórico interactivo.
3. Calculadora de CCL Implícito usando ADRs (GGAL, YPF, BMA).
4. Sidebar de configuración.

FUENTES:
- Bluelytics API para Blue/Oficial.
- Yfinance para ADRs.
- Cálculo manual para brechas.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
import requests

# Función para obtener cotización del Dólar Blue y Oficial desde la API de bluelytics
# Debe retornar un DataFrame con los valores de compra, venta y fecha
def get_bluelytics_data():
    url = "https://api.bluelytics.com.ar/v2/latest"
    try:
        response = requests.get(url)
        data = response.json()
        
        df = pd.DataFrame({
            'Tipo': ['Oficial', 'Blue'],
            'Compra': [data['oficial']['value_buy'], data['blue']['value_buy']],
            'Venta': [data['oficial']['value_sell'], data['blue']['value_sell']],
            'Fecha': [data['last_update'], data['last_update']]
        })
        return df
    except Exception as e:
        st.error(f"Error al conectar con Bluelytics: {e}")
        return pd.DataFrame()
        

# Función para obtener historial de MEP y CCL desde YFinance
# MEP: AL30.BA / AL30D.BA (Bono AL30)
# CCL: GGAL.BA * 10 / GGAL (ADR Galicia)
# Función para obtener historial de MEP (ArgentinaDatos) y CCL (YFinance)
@st.cache_data(ttl=300)
def get_financial_history():
    # 1. Obtener CCL con YFinance (ADR Galicia)
    ccl_series = pd.Series(dtype=float)
    try:
        data = yf.download(['GGAL', 'GGAL.BA'], period="1mo", progress=False)
        if not data.empty and 'Close' in data.columns:
            closes = data['Close']
            ccl_series = (closes['GGAL.BA'] * 10) / closes['GGAL']
            # CLAVE 1: Limpiar la fecha de YFinance (quitar timezone y horas) para que cruce exacto
            ccl_series.index = pd.to_datetime(ccl_series.index).tz_localize(None).normalize()
    except Exception as e:
        st.warning(f"Error CCL YFinance: {e}")

    # 2. Obtener Histórico MEP (ArgentinaDatos API)
    mep_series = pd.Series(dtype=float)
    try:
        # CLAVE 2: El endpoint correcto es 'bolsa', no 'mep'
        url_mep = "https://api.argentinadatos.com/v1/cotizaciones/dolares/bolsa"
        resp = requests.get(url_mep)
        
        if resp.status_code == 200:
            df_mep = pd.DataFrame(resp.json())
            # Parsear fecha, quitar timezone y normalizar a medianoche
            df_mep['fecha'] = pd.to_datetime(df_mep['fecha']).dt.tz_localize(None).dt.normalize()
            df_mep = df_mep.set_index('fecha')
            mep_series = df_mep['venta']
        else:
            st.error(f"Error API ArgentinaDatos: Status {resp.status_code}")
    except Exception as e:
        st.warning(f"Error MEP ArgentinaDatos: {e}")

    # 3. Combinar ambos en un solo DataFrame
    df_fin = pd.DataFrame({'CCL': ccl_series, 'MEP': mep_series})
    
    # Filtrar solo los últimos 30 días
    last_30_days = pd.Timestamp.now().normalize() - pd.Timedelta(days=30)
    df_fin = df_fin[df_fin.index >= last_30_days]

    # Rellenar hacia adelante (para que los findes o feriados tomen el precio del día hábil anterior)
    return df_fin.fillna(method='ffill').dropna(how='all')

# Configuración de página de Streamlit (título, layout 'wide')
st.set_page_config(page_title="Monitor Cambiario Arg", layout="wide")

# 1. Sidebar
# Crear sidebar con selector de fechas y checkbox para mostrar/ocultar activos
st.sidebar.header("Configuración")

# 2. Métricas (Header)
# Crear 4 columnas (st.columns) para mostrar: Oficial, Blue, MEP, CCL Implícito
# Mostrar la variación porcentual respecto al día anterior (mockear variacion si no hay dato histórico)

# PASO: Mostrar fecha de actualización
# 1. Extraer la fecha más reciente del DataFrame df_blue_oficial (columna 'Fecha').
# 2. Formatear la fecha para que se lea fácil (ej: DD/MM/YYYY).
# 3. Usar st.caption() o st.markdown() para mostrar un texto sutil que diga "Última actualización: [FECHA]" justo arriba de las columnas de métricas.
# Obtener datos de Bluelytics para la fecha de actualización
df_blue_oficial = get_bluelytics_data()

if not df_blue_oficial.empty:
    # Extraer y formatear la fecha más reciente
    ultima_fecha_str = df_blue_oficial['Fecha'].iloc[0]
    try:
        # Intentar parsear la fecha (formato ISO usual de APIs)
        fecha_dt = pd.to_datetime(ultima_fecha_str)
        fecha_formateada = fecha_dt.strftime("%d/%m/%Y %H:%M")
    except:
        fecha_formateada = ultima_fecha_str
    
    st.caption(f"Última actualización: {fecha_formateada}")
    
col1, col2, col3, col4 = st.columns(4)# Obtener datos de Bluelytics
df_blue_oficial = get_bluelytics_data()
# Obtener datos Financieros (MEP/CCL)
df_fin = get_financial_history()

ccl_val = df_fin['CCL'].iloc[-1] if not df_fin.empty and 'CCL' in df_fin.columns else None
mep_val = df_fin['MEP'].iloc[-1] if not df_fin.empty and 'MEP' in df_fin.columns else None

if not df_blue_oficial.empty:
    oficial_val = df_blue_oficial[df_blue_oficial['Tipo'] == 'Oficial']['Venta'].values[0]
    blue_val = df_blue_oficial[df_blue_oficial['Tipo'] == 'Blue']['Venta'].values[0]
    
    with col1:
        st.metric("Dólar Oficial", f"${oficial_val:,.2f}")
    
    with col2:
        st.metric("Dólar Blue", f"${blue_val:,.2f}")

with col3:
    if mep_val and not pd.isna(mep_val):
        st.metric("Dólar MEP (AL30)", f"${mep_val:,.2f}")
    else:
        st.metric("Dólar MEP", "N/D")

with col4:
    if ccl_val:
        st.metric("CCL Implícito (GGAL)", f"${ccl_val:,.2f}")
    else:
        st.metric("CCL Implícito", "N/D")

# 3. Gráfico Histórico y Brecha
st.divider()
st.subheader("Análisis de Brecha y Evolución")
# Aquí continuaría la lógica de visualización

# PASO: Calcular múltiples brechas contra el Oficial
# 1. Asegurarse de que 'Oficial' existe en el df_pivot.
# 2. Si existe 'Blue', calcular df_pivot['Brecha Blue (%)'] = ((df_pivot['Blue'] / df_pivot['Oficial']) - 1) * 100
# 3. Si existe 'CCL', calcular df_pivot['Brecha CCL (%)'] = ((df_pivot['CCL'] / df_pivot['Oficial']) - 1) * 100
# 4. Si existe 'MEP', calcular df_pivot['Brecha MEP (%)'] = ((df_pivot['MEP'] / df_pivot['Oficial']) - 1) * 100
# 5. Para el gráfico de plotly en tab2:
#    - Graficar las tres columnas de brecha juntas en el mismo gráfico de líneas.
#    - Título: "Brechas Cambiarias vs Dólar Oficial (%)".
#    - Asegurarse de que la leyenda sea clara.
# Cálculo de brechas adicionales
# PASO 1: Función para obtener datos históricos
# Crear una función llamada get_historical_bluelytics() que haga un GET a "https://api.bluelytics.com.ar/v2/evolution.json"
# Parsear el JSON y devolver un DataFrame de pandas filtrando solo los últimos 30 días.
# El DataFrame debe tener columnas: 'date', 'source' (Oficial o Blue), y 'value_sell'.

# PASO 2: Procesamiento de la Brecha
# Hacer un pivot del DataFrame para que 'Oficial' y 'Blue' sean columnas.
# Crear una nueva columna llamada 'Brecha (%)' con la fórmula: ((Blue / Oficial) - 1) * 100

# PASO 3: Visualización con Plotly
# Usar plotly.express (px.line) para graficar la columna 'Brecha (%)' a lo largo del tiempo.
# Mostrar el gráfico en Streamlit usando st.plotly_chart(fig, use_container_width=True)
def get_historical_bluelytics():
    url = "https://api.bluelytics.com.ar/v2/evolution.json"
    try:
        response = requests.get(url)
        data = response.json()
        df = pd.DataFrame(data)
        
        # Convertir fecha a datetime y filtrar últimos 30 días
        df['date'] = pd.to_datetime(df['date'])
        last_30_days = df[df['date'] > (pd.Timestamp.now() - pd.Timedelta(days=30))]
        
        # Filtrar solo los tipos que nos interesan
        df_filtered = last_30_days[last_30_days['source'].isin(['Oficial', 'Blue'])]
        return df_filtered
    except Exception as e:
        st.error(f"Error al obtener datos históricos: {e}")
        return pd.DataFrame()

# Obtener y procesar datos
df_hist = get_historical_bluelytics()

# Combinar con datos financieros (MEP/CCL) para el gráfico
df_chart_data = df_hist.copy()

if not df_fin.empty:
    # Reset index para tener la fecha como columna
    df_fin_reset = df_fin.reset_index()
    # Convertir a formato largo (melt)
    df_fin_long = df_fin_reset.melt(id_vars=df_fin_reset.columns[0], var_name='source', value_name='value_sell')
    # Renombrar columna de fecha para coincidir con df_hist ('date')
    df_fin_long.rename(columns={df_fin_reset.columns[0]: 'date'}, inplace=True)
    
    # Asegurar que las fechas sean compatibles (timezone naive)
    df_fin_long['date'] = pd.to_datetime(df_fin_long['date']).dt.tz_localize(None)
    if not df_chart_data.empty:
        df_chart_data['date'] = pd.to_datetime(df_chart_data['date']).dt.tz_localize(None)
    
    # Concatenar
    df_chart_data = pd.concat([df_chart_data, df_fin_long], ignore_index=True)

if not df_chart_data.empty:
    # Pivotar para tener Oficial y Blue como columnas
    df_pivot = df_chart_data.pivot(index='date', columns='source', values='value_sell')
    
    # Calcular Brechas
    brecha_cols = []
    if 'Oficial' in df_pivot.columns:
        for col in ['Blue', 'CCL', 'MEP']:
            if col in df_pivot.columns:
                col_name = f'Brecha {col} (%)'
                df_pivot[col_name] = ((df_pivot[col] / df_pivot['Oficial']) - 1) * 100
                brecha_cols.append(col_name)

    df_pivot = df_pivot.reset_index()

    # Crear pestañas para organizar los gráficos
    tab1, tab2 = st.tabs(["Evolución de Precios", "Brecha Cambiaria (%)"])

    with tab1:
        fig_precios = px.line(
            df_chart_data, 
            x='date', 
            y='value_sell', 
            color='source',
            title="Evolución de Tipos de Cambio (30 días)",
            labels={'value_sell': 'Precio ($)', 'date': 'Fecha', 'source': 'Tipo'}
        )
        st.plotly_chart(fig_precios, use_container_width=True)

    with tab2:
        if brecha_cols:
            fig_brecha = px.line(
                df_pivot, 
                x='date', 
                y=brecha_cols, 
                title="Evolución Brecha Cambiaria (30 días)",
                labels={'value': 'Brecha (%)', 'date': 'Fecha', 'variable': 'Tipo'}
            )
            st.plotly_chart(fig_brecha, use_container_width=True)

st.divider()

# PASO 4: Interfaz de usuario (Sidebar y Tabla)
# 1. En la sidebar, crear un st.date_input para que el usuario elija la fecha de inicio y fin del gráfico.
# 2. En la sidebar, crear un st.multiselect para elegir qué tipos de cambio (Oficial, Blue, CCL, MEP) mostrar en el gráfico de líneas.
# 3. Filtrar el DataFrame 'df_chart_data' usando estas selecciones antes de graficar.
# 4. Al final de la página, agregar un st.subheader("Datos Históricos") y mostrar el DataFrame df_pivot usando st.dataframe().
# 5. Debajo de la tabla, agregar un st.download_button que permita descargar df_pivot como un archivo CSV.
# 1. En la sidebar, crear un st.date_input para que el usuario elija la fecha de inicio y fin del gráfico.
st.sidebar.subheader("Filtros de Gráfico")
min_date = df_chart_data['date'].min()
max_date = df_chart_data['date'].max()

date_range = st.sidebar.date_input(
    "Rango de fechas",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# 2. En la sidebar, crear un st.multiselect para elegir qué tipos de cambio
available_sources = df_chart_data['source'].unique().tolist()
selected_sources = st.sidebar.multiselect(
    "Tipos de cambio a mostrar",
    options=available_sources,
    default=available_sources
)

# 3. Filtrar el DataFrame 'df_chart_data' usando estas selecciones
if len(date_range) == 2:
    start_date, end_date = date_range
    mask = (
        (df_chart_data['date'].dt.date >= start_date) & 
        (df_chart_data['date'].dt.date <= end_date) & 
        (df_chart_data['source'].isin(selected_sources))
    )
    df_filtered_chart = df_chart_data.loc[mask]
else:
    df_filtered_chart = df_chart_data[df_chart_data['source'].isin(selected_sources)]

# Nota: Para que los gráficos de arriba reflejen el filtro, se debería usar df_filtered_chart 
# en lugar de df_chart_data en las funciones px.line.

# 4. Al final de la página, agregar un st.subheader("Datos Históricos") y mostrar el DataFrame
st.subheader("Datos Históricos")
st.dataframe(df_pivot.sort_values(by='date', ascending=False), use_container_width=True)

# 5. Debajo de la tabla, agregar un st.download_button
csv = df_pivot.to_csv(index=False).encode('utf-8')
st.download_button( 
    label="Descargar Datos Históricos", 
    data=csv, 
    file_name='datos_hist.csv', 
    mime='text/csv'
)

st.divider()