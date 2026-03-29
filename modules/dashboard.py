import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import json
from pathlib import Path

from modules.pulse.fetchers import fetch_dolar, fetch_bcra, fetch_news
from modules.pulse.anomaly import detect_anomalies
from core.config import RAW_DIR

st.set_page_config(
    page_title="ArgentinaPulse",
    page_icon="🇦🇷",
    layout="wide"
)

# ── Header ──────────────────────────────────────────────────────────
st.title("ArgentinaPulse")
st.caption(f"Última actualización: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

# ── Fetch datos ─────────────────────────────────────────────────────
with st.spinner("Actualizando datos..."):
    dolar  = fetch_dolar()
    bcra_r = fetch_bcra(1)   # reservas
    noticias = fetch_news(5)

# ── Fila 1: métricas dólar ──────────────────────────────────────────
st.subheader("Tipos de cambio")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Dólar Blue",    f"${dolar['blue']}")
with col2:
    st.metric("Dólar Oficial", f"${dolar['oficial']}")
with col3:
    st.metric("Dólar MEP",     f"${dolar['mep']}")
with col4:
    if dolar['blue'] and dolar['oficial']:
        brecha = ((dolar['blue'] / dolar['oficial']) - 1) * 100
        st.metric("Brecha cambiaria", f"{brecha:.1f}%")

# ── Fila 2: Reservas BCRA ───────────────────────────────────────────
st.subheader("Reservas internacionales — BCRA")

if bcra_r["data"]:
    df = pd.DataFrame(bcra_r["data"])
    df["fecha"] = pd.to_datetime(df["fecha"])
    df = df.sort_values("fecha")

    # Detección de anomalía en la última lectura
    history = df["valor"].tolist()[:-1]
    current = df["valor"].tolist()[-1]
    anom    = detect_anomalies(history, current)

    if anom["anomaly"]:
        st.warning(f"Reservas: {anom['message']}")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["fecha"], y=df["valor"],
        mode="lines+markers",
        line=dict(color="#1D9E75", width=2),
        name="Reservas (MM USD)"
    ))
    fig.update_layout(
        height=300,
        margin=dict(l=0, r=0, t=20, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False),
        yaxis=dict(gridcolor="rgba(128,128,128,0.1)")
    )
    st.plotly_chart(fig, use_container_width=True)

# ── Fila 3: Noticias ────────────────────────────────────────────────
st.subheader("Noticias — últimas horas")
for n in noticias[:8]:
    with st.expander(f"[{n['medio'].upper()}] {n['titulo']}"):
        st.write(n["resumen"])
        st.markdown(f"[Ver nota completa]({n['link']})")
