from datetime import datetime
import json
import time
import pandas as pd
import plotly.express as px
import requests
import streamlit as st

# La siguiente configuracion indica el titulo y el tipo de letra del dashboard
st.set_page_config(page_title="Delitos Informáticos Colombia", layout="wide")

# El siguiente st indica el codigo CSS que va a tener la pagina web
st.markdown(
    """
    <style>
    /* Fondo principal y de la barra lateral */
    .stApp, [data-testid="stSidebar"] {
        background-color: #000000 !important;
    }
    /* Forzar color rojo (#FF0000) en textos, títulos y etiquetas */
    h1, h2, h3, h4, h5, h6, p, span, label, .stMarkdown, .stSelectbox, .stButton, div {
        color: #FF0000 !important;
    }
    /* Estilo específico para los inputs y botones */
    div[data-baseweb="input"], div[data-baseweb="select"], button {
        background-color: #111111 !important;
        border: 1px solid #FF0000 !important;
    }
    /* Color de datos dentro de la tabla */
    .stDataFrame div {
        color: #FF0000 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Titulos y datos de la pagina web
st.title("Delitos informáticos colombia")

# Mostrar fecha y hora actual en formato legible
ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
st.write(f"**Fecha y hora actual:** {ahora}")

# Filtro de las columnas de la tabla de los datos
col1, col2 = st.columns([1, 3])

with col2:
    # Selector de fecha (Calendario)
    fecha_seleccionada = st.date_input(
        "Escoger la fecha que uno quiere consultar", datetime(2026, 1, 1)
    )

with col1:
    # Botón para ejecutar la consulta
    st.write("##")  # Espaciador para alinear con el input
    consultar_btn = st.button("Consultar")

# Asignar la fecha seleccionada a la variable del sistema (formato YYYY-MM-DD)
DATE_FIELD_VALUE = fecha_seleccionada.strftime("%Y-%m-%d")


# La siguiente funcion indica los datos de la consulta a la API de datos colombia
def consultar_datos(fecha_consulta):
    DATASET_ID = "4v6r-wu98"
    BASE_URL = f"https://www.datos.gov.co/resource/{DATASET_ID}.json"
    DATE_FIELD = "fecha_hecho"

    LIMIT = 50000
    OFFSET = 0
    registros = []

    # Crear estado de carga visual en Streamlit
    status_text = st.empty()

    while True:
        # Filtrar exactamente por el día seleccionado (desde las 00:00 hasta las 23:59)
        params = {
            "$where": f"{DATE_FIELD} >= '{fecha_consulta}T00:00:00' AND {DATE_FIELD} <= '{fecha_consulta}T23:59:59'",
            "$limit": LIMIT,
            "$offset": OFFSET,
        }

        status_text.text(f"Descargando registros desde el offset {OFFSET}...")

        try:
            r = requests.get(BASE_URL, params=params, timeout=60)
            r.raise_for_status()
            datos = r.json()
        except Exception as e:
            st.error(f"Error al conectarse a la API: {e}")
            break

        if not datos:
            break

        registros.extend(datos)
        OFFSET += LIMIT
        time.sleep(0.2)

    status_text.empty()  # Limpiar texto de estado
    return registros


# El siguiente codigo indica la renderizacion de la pagina
if consultar_btn:
    st.write(f"### Resultados para el día: {DATE_FIELD_VALUE}")

    # Obtener registros de la API
    datos_crudos = consultar_datos(DATE_FIELD_VALUE)

    if datos_crudos:
        # Guardar en archivo local JSON como lo hacía el script original
        with open(
            "delitos_informaticos_2026.json", "w", encoding="utf-8"
        ) as f:
            json.dump(datos_crudos, f, ensure_ascii=False, indent=2)

        # Convertir a DataFrame de Pandas para procesar las visualizaciones
        df = pd.DataFrame(datos_crudos)

        # 1. TABLA DE DATOS
        st.write("#### Tabla de datos encontrados")
        st.dataframe(df, use_container_width=True)

        # 2. GRÁFICA DE BARRAS
        st.write("#### Total de crímenes por departamento")

        # Asegurar que existan las columnas esperadas (ajusta 'departamento' si la API usa otro nombre)
        # Socrata suele usar nombres en minúsculas como 'departamento' o 'departamento_hecho'
        col_depto = (
            "departamento" if "departamento" in df.columns else df.columns[0]
        )

        # Agrupar y contar delitos por departamento
        df_counts = (
            df.groupby(col_depto).size().reset_index(name="Cantidad de Delitos")
        )
        df_counts = df_counts.sort_values(
            by="Cantidad de Delitos", ascending=True
        )

        # Crear la gráfica con escala de color Azul (mínimo) a Rojo (máximo)
        fig = px.bar(
            df_counts,
            x=col_depto,
            y="Cantidad de Delitos",
            color="Cantidad de Delitos",
            color_continuous_scale=["#0000FF", "#FF0000"],  # Azul a Rojo
            labels={col_depto: "Departamento"},
        )

        # Estilizar la gráfica para que combine con el entorno oscuro y texto rojo
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,1)",
            plot_bgcolor="rgba(0,0,0,1)",
            font=dict(color="#FF0000"),
            xaxis=dict(gridcolor="#222222", tickangle=45),
            yaxis=dict(gridcolor="#222222"),
            coloraxis_showscale=True,
        )

        st.plotly_chart(fig, use_container_width=True)

    else:
        st.warning(
            f"No se encontraron registros de delitos informáticos para el día {DATE_FIELD_VALUE}."
        )