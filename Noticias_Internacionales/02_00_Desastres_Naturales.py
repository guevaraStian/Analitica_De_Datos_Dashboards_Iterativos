# Dashboard con informacion de desastres ambientales en el mundo desde el mas reciente al mas antiguo
# Se solicita la informacion a una API web con los datos de las desastres de medio ambiente mas recientes
# Se logra una tabla con los datos y se guarda un json con la informacion
# Python 3.13.9
# pip 26.1.1
# apt update
# apt install python3-venv -y
# python3 -m venv venv
# source venv/bin/activate
# pip install --upgrade pip
# pip install streamlit pandas requests plotlyf

from datetime import datetime
from pathlib import Path
import json
import time
import requests

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

import pandas as pd
import streamlit as st


# Configuracion Streamlit sobre sus titulo


st.set_page_config(
    page_title="Desastres Ambientales Internacionales",
    layout="wide"
)

# Codigo CSS para el dashboard

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

    p,span,label,div{
        color:red !important;
    }

    .stButton>button{
        background-color:black;
        color:red;
        border:2px solid red;
        font-weight:bold;
        width:100%;
    }

    .stButton>button:hover{
        background-color:red;
        color:black;
    }

    table{
        color:red !important;
    }

    .dataframe{
        color:red !important;
    }

    </style>
    """,
    unsafe_allow_html=True
)

# Asignacion de variables

TEMAS = [
    "EARTHQUAKE",
    "FLOOD",
    "DROUGHT",
    "HURRICANE"
]

# Traducción para mostrar en pantalla
TEMAS_ES = {
    "EARTHQUAKE": "TEMBLORES",
    "FLOOD": "INUNDACIONES",
    "DROUGHT": "SEQUÍAS",
    "HURRICANE": "HURACANES"
}

BASE_URL = "https://api.gdeltproject.org/api/v2/doc/doc"

NOTICIAS_POR_TEMA = 5

PAUSA_ENTRE_CONSULTAS = 5

MAX_REINTENTOS = 5


# Codigo relacionado a la sesion requests

session = requests.Session()

retries = Retry(
    total=MAX_REINTENTOS,
    backoff_factor=2,
    status_forcelist=[
        429,
        500,
        502,
        503,
        504
    ],
    allowed_methods=["GET"]
)

adapter = HTTPAdapter(
    max_retries=retries
)

session.mount(
    "http://",
    adapter
)

session.mount(
    "https://",
    adapter
)

session.headers.update(
    {
        "User-Agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
)


# Consulta a la base de datos api GDEL

def obtener_noticias(
    tema: str,
    cantidad: int = 5
) -> list:

    params = {
        "query": tema,
        "mode": "artlist",
        "format": "json",
        "maxrecords": cantidad,
        "sort": "datedesc"
    }

    intento = 0

    while intento < MAX_REINTENTOS:

        try:

            response = session.get(
                BASE_URL,
                params=params,
                timeout=30
            )

            # Codigo por si sale el error mas comun de 429

            if response.status_code == 429:

                retry_after = response.headers.get(
                    "Retry-After"
                )

                if retry_after:
                    espera = int(retry_after)
                else:
                    espera = 10 * (intento + 1)

                time.sleep(espera)

                intento += 1

                continue

            response.raise_for_status()

            data = response.json()

            articulos = data.get(
                "articles",
                []
            )

            noticias = []

            for articulo in articulos:

                noticia = {
                    "titulo":
                        articulo.get("title"),

                    "fecha":
                        articulo.get("seendate"),

                    "url":
                        articulo.get("url"),

                    "fuente":
                        articulo.get("domain"),

                    "idioma":
                        articulo.get("language"),

                    "pais":
                        articulo.get(
                            "sourcecountry",
                            "Desconocido"
                        )
                }

                noticias.append(
                    noticia
                )

            return noticias

        except requests.exceptions.RequestException:

            espera = 5 * (intento + 1)

            time.sleep(espera)

            intento += 1

    return []


# Logica de como guardar el json con los datos

def guardar_json(resultado):

    ahora = datetime.now()

    nombre_archivo = (
        f"Desastre_Natural_"
        f"{ahora:%Y%m%d_%H%M%S}.json"
    )

    ruta = Path(nombre_archivo)

    with open(
        ruta,
        "w",
        encoding="utf-8"
    ) as archivo:

        json.dump(
            resultado,
            archivo,
            ensure_ascii=False,
            indent=4
        )

    return ruta


# Codigo relacionado al dashboar

st.markdown(
    """
    <h1>
    DESASTRES AMBIENTALES INTERNACIONALES
    </h1>
    """,
    unsafe_allow_html=True
)

fecha_actual = datetime.now().strftime(
    "%d/%m/%Y %H:%M:%S"
)

st.markdown(
    f"""
    <h3>
    {fecha_actual}
    </h3>
    """,
    unsafe_allow_html=True
)

# Logica del boton de refrescar

if st.button("Actualizar Consulta"):

    resultado = {}

    barra = st.progress(0)

    estado = st.empty()

    total_temas = len(TEMAS)

    for indice, tema in enumerate(TEMAS):

        estado.markdown(
            f"### Consultando {TEMAS_ES.get(tema, tema)}..."
        )

        noticias = obtener_noticias(
            tema=tema,
            cantidad=NOTICIAS_POR_TEMA
        )

        resultado[tema] = noticias

        progreso = int(
            ((indice + 1) / total_temas) * 100
        )

        barra.progress(progreso)

        if tema != TEMAS[-1]:
            time.sleep(
                PAUSA_ENTRE_CONSULTAS
            )

    ruta_json = guardar_json(
        resultado
    )

    estado.success(
        f"JSON generado: {ruta_json}"
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # Organizados de tablas

    for tema in TEMAS:

        titulo_es = TEMAS_ES.get(
            tema,
            tema
        )

        st.markdown(
            f"""
            <h2>{titulo_es}</h2>
            """,
            unsafe_allow_html=True
        )

        datos = resultado.get(
            tema,
            []
        )

        if len(datos) > 0:

            df = pd.DataFrame(
                datos
            )

            # Orden de la informacion de cada noticia

            columnas_ordenadas = [
                "fecha",
                "pais",
                "titulo",
                "fuente",
                "url",
                "idioma"
            ]

            df = df.reindex(
                columns=columnas_ordenadas
            )

            st.dataframe(
                df,
                use_container_width=True,
                height=250
            )

        else:

            st.warning(
                "No se encontraron noticias."
            )

        st.markdown(
            "<br><br>",
            unsafe_allow_html=True
        )

    # Resumen de los datos que se muestran en pantalla

    total_noticias = sum(
        len(lista)
        for lista in resultado.values()
    )

    st.markdown(
        f"""
        <h2>
        TOTAL NOTICIAS: {total_noticias}
        </h2>
        """,
        unsafe_allow_html=True
    )