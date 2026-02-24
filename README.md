# 📊 Monitor Cambiario Argentino & Análisis de Brechas

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.31+-red.svg)
![Pandas](https://img.shields.io/badge/Pandas-Data_Manipulation-150458.svg)
![Plotly](https://img.shields.io/badge/Plotly-Data_Visualization-3f4f75.svg)

Una herramienta analítica interactiva desarrollada en Python orientada al monitoreo en tiempo real de los múltiples tipos de cambio en Argentina, el cálculo de paridades implícitas y el análisis de spread (brechas cambiarias). 

Ideal para analistas financieros, equipos de research y gestión de carteras que requieren visualizar distorsiones de mercado de forma ágil.

> **Nota:** Podés incluir acá un GIF o una captura de pantalla (screenshot) de tu dashboard funcionando. `![Dashboard Preview](ruta-a-tu-imagen.png)`

## 🎯 Objetivos del Proyecto

- **Monitoreo Unificado:** Centralizar las cotizaciones del Dólar Oficial, Blue, MEP y Contado con Liquidación (CCL) en un solo panel.
- **Análisis de Distorsiones:** Visualizar interactivamente la evolución histórica de las brechas cambiarias contra el tipo de cambio oficial mayorista/minorista.
- **Valuación de Paridades (ADRs):** Calcular el tipo de cambio implícito (CCL) en tiempo real utilizando activos de referencia cruzada (ej. Grupo Financiero Galicia).
- **Exportación de Datos:** Proveer un pipeline limpio para descargar las series de tiempo y utilizarlas en modelos econométricos o de riesgo externos.

## 🧮 Metodología Financiera y Fuentes de Datos

La solidez de este dashboard radica en la diversificación y robustez de sus fuentes de datos para sortear la volatilidad y los vacíos de información del mercado local:

1. **CCL Implícito (Vía ADRs):** - Se calcula el Contado con Liquidación utilizando el ratio de conversión del Grupo Financiero Galicia ($GGAL).
   - **Fórmula:** `(Precio GGAL.BA * 10) / Precio GGAL (Nasdaq) = CCL Implícito`
   - **Fuente:** `yfinance` (Yahoo Finance API).
   
2. **Dólar MEP (Bolsa):** - Histórico de cotizaciones basado en la operatoria de bonos soberanos locales (AL30 / AL30D).
   - **Fuente:** [ArgentinaDatos API](https://argentinadatos.com/) (Resuelve los problemas de latencia y volumen faltante de BYMA en plataformas internacionales).

3. **Dólar Oficial y Dólar Blue:** - Tipos de cambio nominales minoristas e informales.
   - **Fuente:** [Bluelytics API](https://bluelytics.com.ar/).

## 🛠️ Stack Tecnológico

- **Frontend & App Framework:** `Streamlit`
- **Manipulación de Datos:** `Pandas`, `NumPy`
- **Visualización:** `Plotly Express` (Gráficos interactivos y responsivos).
- **Extracción de Datos:** `Requests` (APIs REST), `yfinance` (Datos de mercado).

## 🚀 Instalación y Uso Local

Para correr este proyecto en tu máquina local, se recomienda utilizar un entorno virtual para no generar conflictos de dependencias.

1. **Clonar el repositorio:**
   ```bash
   git clone [https://github.com/tu-usuario/monitor-cambiario-arg.git](https://github.com/tu-usuario/monitor-cambiario-arg.git)
   cd monitor-cambiario-arg
