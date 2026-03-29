import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from modules.pulse.fetchers import fetch_dolar, fetch_bcra, fetch_news
from modules.pulse.anomaly import detect_anomalies

# ── Config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ArgentinaPulse",
    page_icon="🇦🇷",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Paleta ────────────────────────────────────────────────────────────
BG        = "#0F172A"
CARD      = "#1E293B"
BORDER    = "#334155"
BLUE      = "#3B82F6"
BLUE_LT   = "#60A5FA"
SKY       = "#38BDF8"
TEAL      = "#14B8A6"
GREEN     = "#10B981"
AMBER     = "#F59E0B"
RED       = "#EF4444"
PURPLE    = "#A78BFA"
ROSE      = "#FB7185"
TEXT      = "#F1F5F9"
TEXT_MUT  = "#94A3B8"
TEXT_DIM  = "#64748B"
TEXT_DARK = "#475569"

# ── CSS global ────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* Base */
.stApp {{ background-color: {BG} !important; font-family: 'Inter', sans-serif; }}
#MainMenu, footer, header {{ visibility: hidden; }}
.block-container {{ padding: 2rem 2.5rem 3rem !important; max-width: 1400px !important; }}

/* Header */
.pulse-header {{ display: flex; align-items: baseline; gap: 14px; margin-bottom: 6px; }}
.pulse-title {{ font-size: 1.6rem; font-weight: 700; color: {TEXT}; letter-spacing: -0.4px; margin: 0; }}
.pulse-badge {{
    background: rgba(59,130,246,0.15); color: {BLUE_LT};
    border: 1px solid rgba(59,130,246,0.3);
    border-radius: 99px; font-size: 0.62rem; font-weight: 700;
    letter-spacing: 1.2px; padding: 3px 10px; text-transform: uppercase;
}}
.pulse-ts {{ font-size: 0.78rem; color: {TEXT_DARK}; margin-bottom: 24px; }}

/* Section labels */
.sec-label {{
    font-size: 0.66rem; font-weight: 700; color: {TEXT_DIM};
    text-transform: uppercase; letter-spacing: 1.6px;
    margin: 20px 0 10px; display: flex; align-items: center; gap: 10px;
}}
.sec-label::after {{ content: ''; flex: 1; height: 1px; background: {CARD}; }}

/* Tile card */
.tile-card {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: 12px;
    padding: 18px 20px 16px;
    position: relative;
    overflow: hidden;
    transition: border-color 0.2s, transform 0.15s;
    height: 100%;
}}
.tile-card:hover {{ border-color: {BLUE}; transform: translateY(-2px); }}

/* Top accent bar */
.tile-card::before {{
    content: '';
    position: absolute; top: 0; left: 0; right: 0;
    height: 3px; border-radius: 12px 12px 0 0;
}}
.accent-blue::before    {{ background: linear-gradient(90deg, #1D4ED8, {BLUE_LT}); }}
.accent-teal::before    {{ background: linear-gradient(90deg, #0F766E, #5EEAD4); }}
.accent-sky::before     {{ background: linear-gradient(90deg, #0284C7, #7DD3FC); }}
.accent-purple::before  {{ background: linear-gradient(90deg, #7C3AED, #C4B5FD); }}
.accent-amber::before   {{ background: linear-gradient(90deg, #D97706, #FCD34D); }}
.accent-rose::before    {{ background: linear-gradient(90deg, #E11D48, #FDA4AF); }}
.accent-green::before   {{ background: linear-gradient(90deg, #059669, #34D399); }}
.accent-red::before     {{ background: linear-gradient(90deg, #DC2626, #FCA5A5); }}

.tile-label {{
    font-size: 0.66rem; font-weight: 700; color: {TEXT_DIM};
    text-transform: uppercase; letter-spacing: 1.2px; margin-bottom: 10px;
}}
.tile-val {{
    font-size: 1.55rem; font-weight: 700; color: {TEXT};
    line-height: 1; font-variant-numeric: tabular-nums;
}}
.tile-val-sm {{
    font-size: 1.2rem; font-weight: 700; color: {TEXT};
    line-height: 1; font-variant-numeric: tabular-nums;
}}
.tile-badge {{
    display: inline-block; padding: 3px 9px; border-radius: 99px;
    font-size: 0.62rem; font-weight: 700; margin-top: 10px;
}}
.b-blue   {{ background: rgba(59,130,246,0.15);  color: {BLUE_LT}; }}
.b-teal   {{ background: rgba(20,184,166,0.15);  color: #5EEAD4; }}
.b-sky    {{ background: rgba(56,189,248,0.15);  color: #7DD3FC; }}
.b-purple {{ background: rgba(139,92,246,0.15);  color: #C4B5FD; }}
.b-amber  {{ background: rgba(245,158,11,0.15);  color: #FCD34D; }}
.b-green  {{ background: rgba(16,185,129,0.15);  color: #34D399; }}
.b-red    {{ background: rgba(239,68,68,0.15);   color: #FCA5A5; }}
.b-rose   {{ background: rgba(251,113,133,0.15); color: #FDA4AF; }}
.tile-sub {{ font-size: 0.68rem; color: {TEXT_DARK}; margin-top: 8px; }}
.na {{ color: {BORDER}; font-style: italic; }}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {{
    background: {CARD} !important;
    border-radius: 10px !important;
    padding: 4px 6px !important; gap: 4px !important;
    border: 1px solid {BORDER} !important;
}}
.stTabs [data-baseweb="tab"] {{
    color: {TEXT_DIM} !important; font-size: 0.8rem !important;
    font-weight: 600 !important; border-radius: 7px !important;
    padding: 7px 16px !important; background: transparent !important;
}}
.stTabs [aria-selected="true"] {{
    background: {BLUE} !important; color: #FFF !important;
}}
.stTabs [data-baseweb="tab-panel"] {{ padding: 14px 0 0 !important; }}
.stTabs [data-baseweb="tab-border"] {{ display: none !important; }}

/* Expanders */
div[data-testid="stExpander"] {{
    background: {CARD} !important;
    border: 1px solid #2D3F55 !important;
    border-radius: 10px !important;
    margin-bottom: 6px !important;
}}
div[data-testid="stExpander"] summary {{
    color: #CBD5E1 !important; font-size: 0.84rem !important;
    font-weight: 500 !important;
}}
div[data-testid="stExpander"] summary:hover {{ color: {TEXT} !important; }}

/* Alerts */
div[data-testid="stAlert"] {{
    background: rgba(245,158,11,0.08) !important;
    border: 1px solid rgba(245,158,11,0.3) !important;
    border-radius: 10px !important;
    color: #FCD34D !important;
}}

/* Links */
a {{ color: {BLUE_LT} !important; }}
a:hover {{ color: #93C5FD !important; }}

/* Spinner */
.stSpinner > div {{ color: {BLUE} !important; }}

/* Column gaps */
div[data-testid="stHorizontalBlock"] {{ gap: 12px !important; }}

/* ── Tiles: equal height across all columns ── */
div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {{
    display: flex !important;
    flex-direction: column !important;
}}
div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] > div {{
    flex: 1 !important;
    display: flex !important;
    flex-direction: column !important;
}}
div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] > div > div.stMarkdown {{
    flex: 1 !important;
}}
div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] > div > div.stMarkdown > div {{
    height: 100% !important;
}}
.tile-card {{
    min-height: 128px !important;
}}
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────
def fmt(v, prefix="$"):
    if v is None:
        return '<span class="na">—</span>'
    return f"{prefix}{v:,.0f}"

def fmt_pct(v):
    if v is None:
        return '<span class="na">—</span>'
    return f"{v:.1f}%"

def render_tile(label, value_html, accent="accent-blue",
                badge_text="", badge_cls="b-blue", sub=""):
    """Renders one tile card via st.markdown (call inside a st.column)."""
    badge = f'<div class="tile-badge {badge_cls}">{badge_text}</div>' if badge_text else ""
    sub_html = f'<div class="tile-sub">{sub}</div>' if sub else ""
    st.markdown(f"""
    <div class="tile-card {accent}">
        <div class="tile-label">{label}</div>
        <div class="tile-val">{value_html}</div>
        {badge}
        {sub_html}
    </div>
    """, unsafe_allow_html=True)


# ── Fetch datos ───────────────────────────────────────────────────────
with st.spinner("Actualizando datos…"):
    dolar    = fetch_dolar()
    bcra_r   = fetch_bcra(1,  days=60)   # reservas
    bcra_inf = fetch_bcra(27, days=400)  # inflación mensual (dato mensual, lag de publicación)
    noticias = fetch_news(max_per_feed=10)


# ── Header ────────────────────────────────────────────────────────────
ts = datetime.now().strftime("%d/%m/%Y  %H:%M")
st.markdown(f"""
<div class="pulse-header">
    <span class="pulse-title">🇦🇷 ArgentinaPulse</span>
    <span class="pulse-badge">Live</span>
</div>
<div class="pulse-ts">Última actualización: {ts}</div>
""", unsafe_allow_html=True)


# ── Sección: Tipos de cambio ──────────────────────────────────────────
st.markdown('<div class="sec-label">Tipos de cambio</div>', unsafe_allow_html=True)

blue_v    = dolar.get("blue")
oficial_v = dolar.get("oficial")
mep_v     = dolar.get("mep")
ccl_v     = dolar.get("ccl")
cripto_v  = dolar.get("cripto")

brecha = None
if blue_v and oficial_v:
    brecha = ((blue_v / oficial_v) - 1) * 100

# Fila 1: 4 columnas
c1, c2, c3, c4 = st.columns(4)
with c1:
    render_tile("Dólar Blue", fmt(blue_v), "accent-blue", "Paralelo", "b-blue")
with c2:
    render_tile("Dólar Oficial", fmt(oficial_v), "accent-teal", "BNA", "b-teal")
with c3:
    render_tile("Dólar MEP", fmt(mep_v), "accent-sky", "Bolsa", "b-sky")
with c4:
    render_tile("Dólar CCL", fmt(ccl_v), "accent-purple", "C/Liqui", "b-purple")

# Fila 2: 4 columnas
st.markdown('<div style="height:2px"></div>', unsafe_allow_html=True)
c5, c6, c7, c8 = st.columns(4)
with c5:
    render_tile("Cripto USD", fmt(cripto_v), "accent-amber", "USDT/ARS", "b-amber")
with c6:
    if brecha is not None:
        if brecha < 20:
            br_badge, br_cls = "Baja", "b-green"
        elif brecha < 50:
            br_badge, br_cls = "Moderada", "b-amber"
        else:
            br_badge, br_cls = "Alta", "b-red"
    else:
        br_badge, br_cls = "", "b-blue"
    render_tile("Brecha cambiaria", fmt_pct(brecha), "accent-rose", br_badge, br_cls)
with c7:
    ult_res = bcra_r["data"][-1]["valor"] if bcra_r["data"] else None
    # Nota: usar "is not None" para no ocultar el valor 0
    res_html = f"USD {ult_res:,.0f}M" if ult_res is not None else '<span class="na">—</span>'
    render_tile("Reservas BCRA", res_html, "accent-green",
                "Internacionales", "b-green")
with c8:
    ult_inf = bcra_inf["data"][-1]["valor"] if bcra_inf["data"] else None
    inf_fecha = bcra_inf["data"][-1].get("fecha", "")[:7] if bcra_inf["data"] else ""
    render_tile("Inflación mensual", fmt_pct(ult_inf), "accent-red",
                inf_fecha, "b-red")


# ── Sección: Reservas BCRA (gráfico) ─────────────────────────────────
st.markdown('<div class="sec-label">Reservas internacionales — BCRA</div>',
            unsafe_allow_html=True)

if bcra_r["data"]:
    df = pd.DataFrame(bcra_r["data"])
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df = df.dropna(subset=["fecha"]).sort_values("fecha")

    if df.empty or len(df) < 2:
        st.info("Sin suficientes datos de reservas para graficar.")
    else:
        history = df["valor"].tolist()[:-1]
        current = df["valor"].tolist()[-1]
        anom = detect_anomalies(history, current)
        if anom["anomaly"]:
            st.warning(f"⚠ Reservas: {anom['message']}")

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df["fecha"], y=df["valor"],
            fill="tozeroy",
            fillcolor="rgba(59,130,246,0.07)",
            line=dict(color=BLUE, width=2),
            mode="lines",
            name="Reservas (MM USD)",
            hovertemplate="<b>%{x|%d %b %Y}</b><br>USD %{y:,.0f}M<extra></extra>",
        ))
        fig.add_trace(go.Scatter(
            x=[df["fecha"].iloc[-1]], y=[df["valor"].iloc[-1]],
            mode="markers",
            marker=dict(color=BLUE_LT, size=8,
                        line=dict(color=BG, width=2)),
            showlegend=False,
            hovertemplate="<b>Último:</b> USD %{y:,.0f}M<extra></extra>",
        ))
        fig.update_layout(
            height=260,
            margin=dict(l=0, r=0, t=8, b=0),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter", color=TEXT_DIM, size=11),
            xaxis=dict(showgrid=False, zeroline=False,
                       tickfont=dict(color=TEXT_DARK, size=10),
                       tickformat="%d %b"),
            yaxis=dict(gridcolor="rgba(51,65,85,0.4)", zeroline=False,
                       tickfont=dict(color=TEXT_DARK, size=10),
                       ticksuffix="M"),
            hovermode="x unified",
            hoverlabel=dict(bgcolor=CARD, bordercolor=BORDER,
                            font=dict(color=TEXT, size=12)),
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
else:
    st.info("Sin datos de reservas disponibles. La API del BCRA puede estar temporalmente inaccesible.")


# ── Sección: Noticias ─────────────────────────────────────────────────
st.markdown('<div class="sec-label">Noticias económicas</div>', unsafe_allow_html=True)

# Agrupar noticias por fuente
arts_infobae  = [n for n in noticias if n["medio"] == "infobae"]
arts_lanacion = [n for n in noticias if n["medio"] == "lanacion"]
arts_ambito   = [n for n in noticias if n["medio"] == "ambito"]
arts_cronista = [n for n in noticias if n["medio"] == "cronista"]

def _news_feed(arts):
    """Renderiza un feed de artículos expandibles."""
    if not arts:
        st.markdown(
            f'<p style="color:{TEXT_DIM};font-size:0.82rem;padding:12px 0 4px;">'
            'Sin noticias disponibles en este momento.</p>',
            unsafe_allow_html=True,
        )
        return
    for art in arts:
        titulo = art.get("titulo", "Sin título") or "Sin título"
        with st.expander(titulo):
            resumen = art.get("resumen", "")
            if resumen:
                st.write(resumen)
            col_link, col_fecha = st.columns([3, 1])
            with col_link:
                link = art.get("link", "")
                if link:
                    st.markdown(f"[Ver nota completa →]({link})")
            with col_fecha:
                pub = art.get("publicado", "")
                if pub:
                    st.caption(pub[:16])

tab_infobae, tab_lanacion, tab_ambito, tab_cronista = st.tabs(
    ["Infobae", "La Nación", "Ámbito", "Cronista"]
)

with tab_infobae:
    _news_feed(arts_infobae)

with tab_lanacion:
    _news_feed(arts_lanacion)

with tab_ambito:
    _news_feed(arts_ambito)

with tab_cronista:
    _news_feed(arts_cronista)
