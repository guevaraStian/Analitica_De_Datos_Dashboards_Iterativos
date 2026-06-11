
# Dashboard con informacion de titulos relacionados con derechos humanos en el mundo
# Se solicita la informacion a una API web con los datos de los titulos de noticias sobre derechos humanos
# Una tabla, y datos relacionados a estos temas
# pip install flask pandas requests dash
# pip 26.1.1
# Python 3.13.9
# apt update
# apt install python3-venv -y
# python3 -m venv venv
# source venv/bin/activate
# pip install --upgrade pip
# pip install streamlit pandas requests plotly
# streamlit run 03_00_Derechos_Humanos_Noticias.py
import json
import time
import requests
import pandas as pd
import streamlit as st

from datetime import datetime
from deep_translator import GoogleTranslator


# Guardamos informacion de las variables relacionadas a el CSS

st.set_page_config(
    page_title="VIOLACIONES A LOS DERECHOS HUMANOS RECIENTES",
    layout="wide"
)

st.markdown(
    """
    <style>

    .stApp{
        background-color:black;
        color:red;
    }

    h1,h2,h3,h4,h5,h6{
        color:red !important;
        text-align:center;
    }

    p,div,label,span{
        color:red !important;
    }

    .stButton button{
        background-color:black;
        color:red;
        border:2px solid red;
        font-weight:bold;
        width:200px;
    }

    .stDataFrame{
        color:red;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# Configuramos las caracteristicas de la consulta a la api

URL = "https://api.gdeltproject.org/api/v2/doc/doc"

PARAMS = {
    "query": '"human rights"',
    "mode": "ArtList",
    "format": "json",
    "maxrecords": 50,
    "sort": "DateDesc",
    "timespan": "24h"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 Python GDELT News Collector"
}


# La siguiente funcion sirve para traducir el titulo de las noticias al español

def traducir_a_espanol(texto):

    if not texto:
        return ""

    try:

        return GoogleTranslator(
            source="auto",
            target="es"
        ).translate(texto)

    except Exception as e:

        print(
            f"Error traduciendo título: {e}"
        )

        return texto


# A continuacion se ejecuta la consulta a la base de datos API

def consultar_gdelt(max_reintentos=5):

    for intento in range(max_reintentos):

        try:

            response = requests.get(
                URL,
                params=PARAMS,
                headers=HEADERS,
                timeout=30
            )

            if response.status_code == 429:

                espera = (2 ** intento) * 5

                time.sleep(
                    espera
                )

                continue

            response.raise_for_status()

            return response.json()

        except requests.exceptions.Timeout:

            time.sleep(5)

        except requests.exceptions.ConnectionError:

            time.sleep(5)

        except requests.exceptions.HTTPError:

            time.sleep(5)

        except Exception:

            time.sleep(5)

    return None


# Se guarda el json con la informacion de las noticias

def guardar_json(resultado):

    ahora = datetime.now()

    anio = ahora.strftime("%Y")
    mes = ahora.strftime("%m")
    dia = ahora.strftime("%d")
    hora = ahora.strftime("%H")
    minuto = ahora.strftime("%M")
    segundo = ahora.strftime("%S")

    nombre_archivo = (
        f"Derechos_Humanos_"
        f"{anio}{mes}{dia}_"
        f"{hora}{minuto}{segundo}.json"
    )

    with open(
        nombre_archivo,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            resultado,
            f,
            ensure_ascii=False,
            indent=4
        )

    return nombre_archivo


# Los siguiente datos procesan la consulta sobre las noticias

def obtener_noticias():

    data = consultar_gdelt()

    if not data:
        return None, None

    articulos = []

    for article in data.get(
        "articles",
        []
    ):

        titulo_original = article.get(
            "title"
        )

        titulo_traducido = (
            traducir_a_espanol(
                titulo_original
            )
        )

        articulos.append({

            "Título":
                titulo_traducido,

            "Fuente":
                article.get(
                    "sourcecountry"
                ),

            "Idioma":
                article.get(
                    "language"
                ),

            "Fecha":
                article.get(
                    "seendate"
                ),

            "URL":
                article.get(
                    "url"
                ),

            "Imagen":
                article.get(
                    "socialimage"
                )
        })

    resultado = {

        "fecha_descarga":
            datetime.utcnow().isoformat(),

        "cantidad":
            len(articulos),

        "noticias":
            articulos
    }

    archivo = guardar_json(
        resultado
    )

    return articulos, archivo


# EL siguiente codigo ayuda a crear el dashboar con la libreria streamlit

st.markdown(
    """
    <h1>
    VIOLACIONES A LOS DERECHOS HUMANOS RECIENTES
    </h1>
    """,
    unsafe_allow_html=True
)

fecha_hora_actual = datetime.now().strftime(
    "%d/%m/%Y %H:%M:%S"
)

st.markdown(
    f"""
    <div style="
    text-align:center;
    color:red;
    font-size:22px;
    margin-bottom:20px;">
    {fecha_hora_actual}
    </div>
    """,
    unsafe_allow_html=True
)

# A continuacion se crea el boton de actualizar que vuelve y cosulta a la base de datos

if st.button("Actualizar"):

    with st.spinner(
        "Consultando API GDELT..."
    ):

        articulos, archivo = (
            obtener_noticias()
        )

    if articulos:

        st.success(
            f"Consulta completada. "
            f"Archivo generado: {archivo}"
        )

        df = pd.DataFrame(
            articulos
        )

        st.dataframe(
            df,
            use_container_width=True,
            height=600
        )

        st.markdown(
            f"""
            <div style="color:red;">
            Registros encontrados:
            {len(df)}
            </div>
            """,
            unsafe_allow_html=True
        )

    else:

        st.error(
            "No fue posible obtener datos de GDELT."
        )

