# Dashboard con informacion de noticias de derechos humanos internacionalmente
# Se solicita la informacion a una API web con los datos de los temas relacionados a derechos humanos
# Una tabla con los datos y se descarga un JSON con la informacion descargada
# pip install flask pandas requests dash
# pip 26.1.1
# Python 3.13.9
# apt update
# apt install python3-venv -y
# python3 -m venv venv
# source venv/bin/activate
# pip install --upgrade pip
# pip install streamlit pandas requests plotly
# streamlit run 03_01_Derechos_Humanos_Noticias_Dia.py

# Las librerias que se usan son las siguientes
import json
import time
import requests
import pandas as pd
import streamlit as st

from datetime import datetime, date, timedelta
from deep_translator import GoogleTranslator


# Se guardan los datos de las variables que se usaran
st.set_page_config(
    page_title="VIOLACIONES A LOS DERECHOS HUMANOS RECIENTES",
    layout="wide"
)

st.markdown("""
<style>
.stApp{background-color:black;color:red;}
h1,h2,h3,h4,h5,h6{text-align:center;color:red !important;}
p,div,label,span{color:red !important;}
.stButton button{
    background-color:black;
    color:red;
    border:2px solid red;
    font-weight:bold;
    width:200px;
}
.stDataFrame{color:red;}
</style>
""", unsafe_allow_html=True)


URL = "https://api.gdeltproject.org/api/v2/doc/doc"

HEADERS = {
    "User-Agent": "Mozilla/5.0 Python GDELT News Collector"
}


# La siguiente funcion crea el listado dependiendo la fecha que se indique en el dashboard
def construir_params(fecha_seleccionada: date):

    inicio = fecha_seleccionada.strftime("%Y%m%d000000")
    fin = fecha_seleccionada.strftime("%Y%m%d235959")

    return {
        "query": '"human rights"',
        "mode": "ArtList",
        "format": "json",
        "maxrecords": 50,
        "sort": "DateDesc",
        "startdatetime": inicio,
        "enddatetime": fin
    }

# La siguiente funcion traduce los titulos al idioma español
def traducir_a_espanol(texto):
    if not texto:
        return ""
    try:
        return GoogleTranslator(source="auto", target="es").translate(texto)
    except Exception:
        return texto


def consultar_gdelt(params, max_reintentos=5):

    for intento in range(max_reintentos):
        try:
            response = requests.get(
                URL,
                params=params,
                headers=HEADERS,
                timeout=30
            )

            if response.status_code == 429:
                time.sleep((2 ** intento) * 5)
                continue

            response.raise_for_status()
            return response.json()

        except Exception:
            time.sleep(5)

    return None


# Se organiza el archivo json con la informacion de la fecha que se solicita
def guardar_json(resultado, fecha_dashboard: date):

    ahora = datetime.now()

    fecha_base = fecha_dashboard.strftime("%Y%m%d")

    nombre_archivo = (
        f"Derechos_Humanos_"
        f"{fecha_base}_"
        f"{ahora.strftime('%H%M%S')}.json"
    )

    with open(nombre_archivo, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=4)

    return nombre_archivo


# En la siguiente funcion se solicita el listado de las noticias y se guardan las variables
def obtener_noticias(fecha_seleccionada):

    params = construir_params(fecha_seleccionada)

    data = consultar_gdelt(params)

    if not data:
        return None, None

    articulos = []

    for article in data.get("articles", []):

        articulos.append({
            "Título": traducir_a_espanol(article.get("title")),
            "Fuente": article.get("sourcecountry"),
            "Idioma": article.get("language"),
            "Fecha": article.get("seendate"),
            "URL": article.get("url"),
            "Imagen": article.get("socialimage")
        })

    resultado = {
        "fecha_consulta_dashboard": fecha_seleccionada.strftime("%Y-%m-%d"),
        "fecha_descarga": datetime.utcnow().isoformat(),
        "cantidad": len(articulos),
        "noticias": articulos
    }

    # Se indica la fecha solicitada en el dashboard
    archivo = guardar_json(resultado, fecha_seleccionada)

    return articulos, archivo


# Los siguientes markdown organizan la parte visual del dashboard

st.markdown("<h1>VIOLACIONES A LOS DERECHOS HUMANOS RECIENTES</h1>", unsafe_allow_html=True)

st.markdown(
    f"<div style='text-align:center;color:red;font-size:22px'>{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</div>",
    unsafe_allow_html=True
)


# El siguiente codigo ayuda a elegir la fecha que se va a buscar
fecha_usuario = st.date_input(
    "Selecciona la fecha de consulta",
    value=date.today()
)


# Codigo relacionado al boton actualizar
if st.button("Actualizar"):

    with st.spinner("Consultando API GDELT..."):

        articulos, archivo = obtener_noticias(fecha_usuario)

    if articulos:

        st.success(f"Consulta completada. Archivo generado: {archivo}")

        df = pd.DataFrame(articulos)

        st.dataframe(df, use_container_width=True, height=600)

        st.markdown(
            f"<div style='color:red'>Registros encontrados: {len(df)}</div>",
            unsafe_allow_html=True
        )

    else:
        st.error("No fue posible obtener datos de GDELT.")