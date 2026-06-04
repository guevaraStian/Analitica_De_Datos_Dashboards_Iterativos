# Dashboard con informacion de los ultimos 20 ataques que sucedieron en el mundo
# Se solicita la informacion a una API web con los datos de los ataques belicos
# Una tabla, un json, con datos de cada registro
# pip install flask pandas requests dash
# pip 26.1.1
# Python 3.13.9
# apt update
# apt install python3-venv -y
# python3 -m venv venv
# source venv/bin/activate
# pip install --upgrade pip
# pip install streamlit pandas requests plotly

import requests
import json
import time
import random
from datetime import datetime, timedelta, timezone
import pandas as pd
import streamlit as st

# =========================
# 🎨 ESTILO GLOBAL (NEGRO + ROJO)
# =========================

st.markdown("""
<style>
    body {
        background-color: black;
        color: red;
    }

    .stApp {
        background-color: black;
        color: red;
    }

    h1, h2, h3, h4, h5, p, span, label {
        color: red !important;
    }

    /* Botones */
    div.stButton > button {
        background-color: gray;
        color: red;
        border: 1px solid red;
        border-radius: 6px;
    }

    div.stButton > button:hover {
        background-color: #444;
        color: red;
    }

    /* DataFrame styling */
    .dataframe {
        background-color: gray !important;
        color: black !important;
    }
</style>
""", unsafe_allow_html=True)

# =========================
# CONFIGURACIÓN
# =========================

BASE_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
MAX_RECORDS = 20

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; GDELT-Python-Client/1.0)"
}

# =========================
# OPCIÓN 18: ASALTOS O ATAQUES
# =========================

OPCION = 18

if OPCION == 18:
    QUERY = "(assault OR attack OR asalto OR ataques OR robbery OR violence OR shooting)"
else:
    QUERY = "(investigation OR report OR corruption OR inquiry)"

# =========================
# FECHA (AYER)
# =========================

ayer = datetime.now(timezone.utc) - timedelta(days=1)

start_date = ayer.strftime("%Y%m%d000000")
end_date = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")

# =========================
# PARAMETROS
# =========================

params = {
    "query": QUERY,
    "mode": "ArtList",
    "format": "json",
    "maxrecords": MAX_RECORDS,
    "startdatetime": start_date,
    "enddatetime": end_date,
    "sort": "DateDesc"
}

# =========================
# CONSULTA SEGURA
# =========================

def consultar_gdelt(max_intentos=6):
    intento = 0

    while intento < max_intentos:
        try:
            response = requests.get(
                BASE_URL,
                params=params,
                headers=HEADERS,
                timeout=30
            )

            if response.status_code == 429:
                wait_time = (2 ** intento) + random.uniform(0.5, 2.0)
                time.sleep(wait_time)
                intento += 1
                continue

            if response.status_code != 200:
                time.sleep(2)
                intento += 1
                continue

            if not response.text or response.text.strip() == "":
                return None

            try:
                return response.json()
            except:
                return None

        except:
            intento += 1
            time.sleep(2)

    return None

# =========================
# FUNCION PARA DATAFRAME
# =========================

def procesar_datos(articles):
    data = []

    now_utc = datetime.now(timezone.utc)

    for art in articles:
        fecha_raw = art.get("seendate")

        if not fecha_raw:
            continue

        try:
            fecha_dt = datetime.strptime(fecha_raw, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
        except:
            continue

        if fecha_dt > now_utc:
            continue

        data.append({
            "source country": art.get("sourceCountry"),
            "title": art.get("title"),
            "send date": fecha_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "language": art.get("language"),
            "url": art.get("url"),
            "domain": art.get("domain")
        })

    df = pd.DataFrame(data)

    if not df.empty:
        df = df.sort_values(by="send date", ascending=False).head(20)

    return df

# =========================
# STREAMLIT DASHBOARD
# =========================

st.title("🚨 ULTIMOS ATAQUES EN EL MUNDO")

st.caption(f"🕒 Actualizado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

refresh = st.button("🔄 Refrescar datos")

# =========================
# CONSULTA API
# =========================

with st.spinner("Consultando GDELT..."):
    data = consultar_gdelt()

if data is None or not isinstance(data, dict):
    st.error("⚠️ La API no respondió correctamente (posible 429 o bloqueo temporal).")
    st.stop()

articles = data.get("articles")

if not articles or not isinstance(articles, list):
    st.warning("No hay datos de ataques disponibles en este momento.")
    st.stop()

# =========================
# DATAFRAME PROCESADO
# =========================

df = procesar_datos(articles)

# =========================
# TABLA PERSONALIZADA
# =========================

st.subheader("📊 Tabla de ataques (formato personalizado)")

if not df.empty:
    # estilo: índice rojo + fondo gris + texto negro
    styled_df = df.style.set_properties(**{
        'background-color': 'gray',
        'color': 'black',
        'border-color': 'black'
    }).set_table_styles([
        {
            'selector': 'th',
            'props': [('background-color', 'red'), ('color', 'black')]
        },
        {
            'selector': 'index_name',
            'props': [('background-color', 'red'), ('color', 'black')]
        }
    ])

    st.dataframe(styled_df, use_container_width=True)
else:
    st.warning("No hay registros válidos para mostrar.")

# =========================
# TABLA RAW
# =========================

st.subheader("📋 JSON completo sin procesar")

df_raw = pd.DataFrame(articles)

st.dataframe(df_raw, use_container_width=True)

# =========================
# GUARDAR JSON
# =========================

now = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"ataques_mundo_{now}.json"

with open(filename, "w", encoding="utf-8") as f:
    json.dump(articles, f, ensure_ascii=False, indent=4)

st.success(f"📁 JSON guardado: {filename}")

# =========================
# DETALLE JSON
# =========================

with st.expander("🔎 Ver JSON completo"):
    st.json(articles)