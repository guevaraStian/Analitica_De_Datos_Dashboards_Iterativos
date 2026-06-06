# Dashboard con informacion de protestas en el mundo desde el mas reciente al mas antiguo
# Se solicita la informacion a una API web con los datos de las protestas mas recientes
# Se logra una tabla con los datos y se guarda un json con la informacion
# Python 3.13.9
# pip 26.1.1
# apt update
# apt install python3-venv -y
# python3 -m venv venv
# source venv/bin/activate
# pip install --upgrade pip
# pip install streamlit pandas requests plotly

import json
import requests
import time
import random
import pandas as pd
import streamlit as st

from datetime import datetime, timezone


# Se guardan variables de consulta a la API de las noticias

MAX_RESULTADOS = 10
QUERY = "(protest OR protests OR demonstration OR riot)"


# Se crea la sesion streamlit

def crear_sesion():

    sesion = requests.Session()

    # Se desactivar retries automáticos de urllib3
    adapter = requests.adapters.HTTPAdapter(max_retries=0)

    sesion.mount("http://", adapter)
    sesion.mount("https://", adapter)

    sesion.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        )
    })

    return sesion


# Consulta GDELT con la variable 429

def obtener_protestas():

    url = "https://api.gdeltproject.org/api/v2/doc/doc"

    params = {
        "query": QUERY,
        "mode": "artlist",
        "format": "json",
        "maxrecords": MAX_RESULTADOS,
        "sort": "DateDesc"
    }

    sesion = crear_sesion()

    max_intentos = 6

    for intento in range(1, max_intentos + 1):

        try:
            respuesta = sesion.get(url, params=params, timeout=30)

            # Tiempo limite 429
            if respuesta.status_code == 429:

                espera = (2 ** intento) + random.uniform(1, 4)

                print(f"[429] Rate limit. Esperando {espera:.1f}s...")

                time.sleep(espera)
                continue

            # Indica los errores
            if respuesta.status_code != 200:

                print(f"[HTTP {respuesta.status_code}] Reintentando...")

                time.sleep(2 * intento)
                continue

            # Se crea el JSON vacio
            if not respuesta.text.strip():

                print("[VACÍO] Respuesta vacía, reintentando...")
                time.sleep(2 * intento)
                continue

            # Se guardan datos en el JSON
            try:
                datos = respuesta.json()
            except Exception:
                print("[JSON ERROR] Respuesta inválida, reintentando...")
                time.sleep(2 * intento)
                continue

            return procesar(datos)

        except requests.exceptions.RequestException as e:

            print(f"[ERROR RED] intento {intento}: {e}")

            time.sleep(2 * intento)

    raise Exception("❌ GDELT bloqueó demasiadas solicitudes (429 persistente)")


# Seprocesan los datos que vienen de la consulta

def procesar(datos):

    articulos = datos.get("articles", [])

    resultados = []

    for i, a in enumerate(articulos[:MAX_RESULTADOS], start=1):

        resultados.append({
            "ID": i,
            "Título": a.get("title"),
            "Fecha": a.get("seendate"),
            "Fuente": a.get("domain"),
            "País": a.get("sourcecountry"),
            "Idioma": a.get("language"),
            "URL": a.get("url"),
            "Tono": a.get("tone"),
        })

    return resultados


# Se guardan los datos en el JSON organizados del mas reciente al mas antiguo

def guardar_json(data):

    nombre = f"protestas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    contenido = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(),
        "query": QUERY,
        "total": len(data),
        "resultados": data
    }

    with open(nombre, "w", encoding="utf-8") as f:
        json.dump(contenido, f, indent=4, ensure_ascii=False)

    return nombre


# Se crea el STREAMLIT UI

st.set_page_config(page_title="PROTESTAS INTERNACIONALES")

st.markdown("""
    <style>
    body, .stApp {
        background-color: black;
        color: red;
    }

    h1, h2, h3, p, div, span {
        color: red !important;
    }

    .stButton button {
        background-color: black;
        color: red;
        border: 2px solid red;
    }
    </style>
""", unsafe_allow_html=True)


st.title("PROTESTAS INTERNACIONALES")
st.write("📅", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


# Cache simple para evitar 429 

if "datos" not in st.session_state:
    st.session_state.datos = None


# Se declara el codigo relacionado al boton refrescar

if st.button("REFRESCAR"):

    with st.spinner("Consultando GDELT (evitando 429)..."):

        datos = obtener_protestas()

        archivo = guardar_json(datos)

        st.session_state.datos = datos

        st.success(f"JSON guardado: {archivo}")


# Cuando llegan los datos se muestra la tabla con la informacion

if st.session_state.datos:

    df = pd.DataFrame(st.session_state.datos)
    st.dataframe(df)

else:
    st.info("Presiona REFRESCAR para cargar datos")