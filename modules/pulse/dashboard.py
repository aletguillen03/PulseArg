# modules/pulse/dashboard.py
# ── Dashboard del módulo ArgentinaPulse ─────────────────────────────────────
# Punto de entrada principal: render_pulse_module()
# Para testing standalone: streamlit run modules/pulse/dashboard.py

import sys
from pathlib import Path

# ── sys.path: agrega el root del proyecto (necesario para imports absolutos) ──
_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# ── Imports internos del módulo pulse (relativos cuando se importa, absolutos standalone) ──
try:
    from .fetchers import fetch_dolar, fetch_bcra, fetch_news
    from .anomaly import detect_anomalies
    from .markets import fetch_snapshot, fetch_history, fetch_correlation
    from .constants import (
        SECTOR_LABELS, BRECHA_BAJA, BRECHA_MODERADA,
        CARD, BORDER, BLUE, BLUE_LT, TEXT, TEXT_MUT, TEXT_DIM, TEXT_DARK,
    )
except ImportError:
    from modules.pulse.fetchers import fetch_dolar, fetch_bcra, fetch_news
    from modules.pulse.anomaly import detect_anomalies
    from modules.pulse.markets import fetch_snapshot, fetch_history, fetch_correlation
    from modules.pulse.constants import (
        SECTOR_LABELS, BRECHA_BAJA, BRECHA_MODERADA,
        CARD, BORDER, BLUE, BLUE_LT, TEXT, TEXT_MUT, TEXT_DIM, TEXT_DARK,
    )


# ══════════════════════════════════════════════════════════════════════════════
# ── Helpers de renderizado ────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

def fmt(v, prefix="$") -> str:
    """Formatea un valor numérico como moneda. Retorna — si es None."""
    if v is None:
        return '<span class="na">—</span>'
    return f"{prefix}{v:,.0f}"


def fmt_pct(v) -> str:
    """Formatea un valor como porcentaje. Retorna — si es None."""
    if v is None:
        return '<span class="na">—</span>'
    return f"{v:.1f}%"


def render_tile(label: str, value_html: str, accent: str = "accent-blue",
                badge_text: str = "", badge_cls: str = "b-blue", sub: str = "") -> None:
    """Renderiza una tile card con acento de color, valor y badge opcional."""
    badge    = f'<div class="tile-badge {badge_cls}">{badge_text}</div>' if badge_text else ""
    sub_html = f'<div class="tile-sub">{sub}</div>' if sub else ""
    st.markdown(f"""
    <div class="tile-card {accent}">
        <div class="tile-label">{label}</div>
        <div class="tile-val">{value_html}</div>
        {badge}
        {sub_html}
    </div>
    """, unsafe_allow_html=True)


def render_market_card(nombre: str, ticker: str, precio, var_pct, moneda: str) -> None:
    """Renderiza una card compacta de activo financiero con precio y variación."""
    if precio is None:
        price_html  = '<span class="na">—</span>'
        change_html = ""
    else:
        price_html = f"{moneda} {precio:,.2f}" if moneda else f"${precio:,.2f}"
        if var_pct is not None:
            sign  = "+" if var_pct > 0 else ""
            cls   = "mc-up" if var_pct > 0 else ("mc-down" if var_pct < 0 else "mc-flat")
            change_html = f'<span class="mc-change {cls}">{sign}{var_pct:.2f}%</span>'
        else:
            change_html = ""

    st.markdown(f"""
    <div class="market-card">
        <div class="mc-header">
            <span class="mc-name">{nombre}</span>
            <span class="mc-ticker">{ticker}</span>
        </div>
        <div>
            <span class="mc-price">{price_html}</span>
            {change_html}
        </div>
    </div>
    """, unsafe_allow_html=True)


def _brecha_badge(brecha) -> tuple[str, str]:
    """Retorna (texto_badge, clase_badge) según el nivel de brecha."""
    if brecha is None:
        return "", "b-blue"
    if brecha < BRECHA_BAJA:
        return "Baja", "b-green"
    if brecha < BRECHA_MODERADA:
        return "Moderada", "b-amber"
    return "Alta", "b-red"


# ══════════════════════════════════════════════════════════════════════════════
# ── Función principal del módulo ──────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

def render_pulse_module(refresh_interval: int = 30,
                        show_details: bool = True,
                        alerts_only: bool = False) -> None:
    """
    Renderiza el módulo ArgentinaPulse como componente reutilizable.

    Parámetros
    ----------
    refresh_interval : int
        Intervalo de actualización en minutos (informativo, no fuerza rerun).
    show_details : bool
        Si True muestra gráficos y secciones extendidas.
    alerts_only : bool
        Si True muestra solo tiles con anomalías detectadas.
    """

    # ── Fetch de datos ────────────────────────────────────────────────────────
    with st.spinner("Actualizando datos…"):
        dolar    = fetch_dolar()
        bcra_r   = fetch_bcra(1,  days=60)
        bcra_inf = fetch_bcra(27, days=400)
        noticias = fetch_news(max_per_feed=10)
        df_snap  = fetch_snapshot()

    # ── Header del módulo ─────────────────────────────────────────────────────
    ts = datetime.now().strftime("%d/%m/%Y  %H:%M")
    st.markdown(f"""
    <div class="pulse-header">
        <span class="pulse-title">🇦🇷 ArgentinaPulse</span>
        <span class="pulse-badge">Live</span>
    </div>
    <div class="pulse-ts">Última actualización: {ts} · Intervalo: {refresh_interval} min</div>
    """, unsafe_allow_html=True)

    # ── Pestañas internas del módulo ──────────────────────────────────────────
    tab_panorama, tab_finanzas, tab_noticias = st.tabs(
        ["📊 Panorama", "💹 Finanzas", "📰 Noticias"]
    )

    # ══════════════════════════════════════════════════════════════════════
    # ── TAB: PANORAMA ────────────────────────────────────────────────────
    # ══════════════════════════════════════════════════════════════════════
    with tab_panorama:

        # Cálculo de variables comunes
        blue_v    = dolar.get("blue")
        oficial_v = dolar.get("oficial")
        brecha    = ((blue_v / oficial_v) - 1) * 100 if blue_v and oficial_v else None
        ult_res   = bcra_r["data"][-1]["valor"]   if bcra_r["data"]   else None
        ult_inf   = bcra_inf["data"][-1]["valor"] if bcra_inf["data"] else None
        inf_fecha = bcra_inf["data"][-1].get("fecha", "")[:7] if bcra_inf["data"] else ""

        # ── Resumen rápido ────────────────────────────────────────────────
        st.markdown('<div class="sec-label">Resumen rápido</div>', unsafe_allow_html=True)

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            render_tile("Dólar Blue", fmt(blue_v), "accent-blue", "Paralelo", "b-blue")
        with c2:
            br_badge, br_cls = _brecha_badge(brecha)
            render_tile("Brecha cambiaria", fmt_pct(brecha), "accent-rose", br_badge, br_cls)
        with c3:
            res_html = f"USD {ult_res:,.0f}M" if ult_res is not None else '<span class="na">—</span>'
            render_tile("Reservas BCRA", res_html, "accent-green", "Internacionales", "b-green")
        with c4:
            render_tile("Inflación mensual", fmt_pct(ult_inf), "accent-red", inf_fecha, "b-red")

        # ── Top movers del día ────────────────────────────────────────────
        st.markdown('<div class="sec-label">Top movers del día</div>', unsafe_allow_html=True)

        df_movers = df_snap.dropna(subset=["var_pct"]).copy() if not df_snap.empty else pd.DataFrame()
        if not df_movers.empty:
            top_up   = df_movers.nlargest(4, "var_pct")
            top_down = df_movers.nsmallest(4, "var_pct")

            cols_up = st.columns(4)
            for i, (_, row) in enumerate(top_up.iterrows()):
                with cols_up[i]:
                    sign = "+" if row["var_pct"] > 0 else ""
                    render_tile(
                        row["nombre"],
                        f'{sign}{row["var_pct"]:.2f}%',
                        "accent-green",
                        row["ticker"], "b-green",
                        sub=f'{row.get("moneda", "")} {row["precio"]:,.2f}' if row["precio"] else "",
                    )

            st.markdown('<div style="height:2px"></div>', unsafe_allow_html=True)

            cols_down = st.columns(4)
            for i, (_, row) in enumerate(top_down.iterrows()):
                with cols_down[i]:
                    sign = "+" if row["var_pct"] > 0 else ""
                    render_tile(
                        row["nombre"],
                        f'{sign}{row["var_pct"]:.2f}%',
                        "accent-red",
                        row["ticker"], "b-red",
                        sub=f'{row.get("moneda", "")} {row["precio"]:,.2f}' if row["precio"] else "",
                    )

        # ── Últimas noticias (preview) ────────────────────────────────────
        st.markdown('<div class="sec-label">Últimas noticias</div>', unsafe_allow_html=True)
        for art in noticias[:5]:
            titulo = art.get("titulo", "Sin título") or "Sin título"
            medio  = art.get("medio", "").upper()
            link   = art.get("link", "")
            st.markdown(
                f'<div style="padding:6px 0;border-bottom:1px solid {BORDER};">'
                f'<span style="color:{TEXT_DIM};font-size:0.62rem;font-weight:700;letter-spacing:0.8px;">{medio}</span> '
                f'<a href="{link}" style="color:{TEXT};font-size:0.82rem;text-decoration:none;">{titulo}</a>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # ══════════════════════════════════════════════════════════════════════
    # ── TAB: FINANZAS ────────────────────────────────────────────────────
    # ══════════════════════════════════════════════════════════════════════
    with tab_finanzas:

        # ── Tipos de cambio ───────────────────────────────────────────────
        st.markdown('<div class="sec-label">Tipos de cambio</div>', unsafe_allow_html=True)

        blue_v   = dolar.get("blue")
        oficial_v = dolar.get("oficial")
        mep_v    = dolar.get("mep")
        ccl_v    = dolar.get("ccl")
        cripto_v = dolar.get("cripto")
        brecha   = ((blue_v / oficial_v) - 1) * 100 if blue_v and oficial_v else None

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            render_tile("Dólar Blue",    fmt(blue_v),    "accent-blue",   "Paralelo", "b-blue")
        with c2:
            render_tile("Dólar Oficial", fmt(oficial_v), "accent-teal",   "BNA",      "b-teal")
        with c3:
            render_tile("Dólar MEP",     fmt(mep_v),     "accent-sky",    "Bolsa",    "b-sky")
        with c4:
            render_tile("Dólar CCL",     fmt(ccl_v),     "accent-purple", "C/Liqui",  "b-purple")

        st.markdown('<div style="height:2px"></div>', unsafe_allow_html=True)

        c5, c6, c7, c8 = st.columns(4)
        with c5:
            render_tile("Cripto USD", fmt(cripto_v), "accent-amber", "USDT/ARS", "b-amber")
        with c6:
            br_badge, br_cls = _brecha_badge(brecha)
            render_tile("Brecha cambiaria", fmt_pct(brecha), "accent-rose", br_badge, br_cls)
        with c7:
            ult_res  = bcra_r["data"][-1]["valor"] if bcra_r["data"] else None
            res_html = f"USD {ult_res:,.0f}M" if ult_res is not None else '<span class="na">—</span>'
            render_tile("Reservas BCRA", res_html, "accent-green", "Internacionales", "b-green")
        with c8:
            ult_inf   = bcra_inf["data"][-1]["valor"] if bcra_inf["data"] else None
            inf_fecha = bcra_inf["data"][-1].get("fecha", "")[:7] if bcra_inf["data"] else ""
            render_tile("Inflación mensual", fmt_pct(ult_inf), "accent-red", inf_fecha, "b-red")

        if not show_details:
            return

        # ── Reservas BCRA (gráfico) ───────────────────────────────────────
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
                anom    = detect_anomalies(history, current)
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
                                line=dict(color="#0F172A", width=2)),
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

        # ── Activos por sector (cards) ─────────────────────────────────────
        st.markdown('<div class="sec-label">Activos del mercado argentino</div>',
                    unsafe_allow_html=True)

        if not df_snap.empty:
            sectores          = df_snap["sector"].unique().tolist()
            sector_tab_labels = [SECTOR_LABELS.get(s, (s.title(), "accent-blue"))[0] for s in sectores]
            sector_tabs       = st.tabs(sector_tab_labels)

            for stab, sector in zip(sector_tabs, sectores):
                with stab:
                    df_sec    = df_snap[df_snap["sector"] == sector].copy()
                    rows_list = df_sec.to_dict("records")

                    for i in range(0, len(rows_list), 3):
                        chunk = rows_list[i:i+3]
                        cols  = st.columns(3)
                        for j, row in enumerate(chunk):
                            with cols[j]:
                                render_market_card(
                                    row.get("nombre", ""),
                                    row.get("ticker", ""),
                                    row.get("precio"),
                                    row.get("var_pct"),
                                    row.get("moneda", ""),
                                )
                        st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
        else:
            st.info("Sin datos de activos disponibles.")

        # ── Histórico de precios ───────────────────────────────────────────
        st.markdown('<div class="sec-label">Histórico de precios</div>', unsafe_allow_html=True)

        col_sel1, col_sel2 = st.columns([2, 1])
        with col_sel1:
            todos = {
                f"{r['nombre']} ({r['ticker']})": r["ticker"]
                for _, r in df_snap.dropna(subset=["precio"]).iterrows()
            } if not df_snap.empty else {}
            seleccion = st.multiselect(
                "Seleccioná activos",
                options=list(todos.keys()),
                default=[k for k in ["Merval (^MERV)", "MercadoLibre (MELI)", "YPF (YPF)"] if k in todos],
                key="pulse_historico_activos",
            )
        with col_sel2:
            periodo = st.selectbox(
                "Período", ["1mo", "3mo", "6mo", "1y"], index=1,
                key="pulse_historico_periodo",
            )

        if seleccion:
            fig2 = go.Figure()
            for label in seleccion:
                ticker = todos[label]
                hist   = fetch_history(ticker, period=periodo)
                if not hist.empty:
                    close = hist["Close"]
                    norm  = (close / close.iloc[0]) * 100
                    fig2.add_trace(go.Scatter(
                        x=norm.index, y=norm.values,
                        mode="lines", name=label,
                    ))
            fig2.update_layout(
                height=380,
                yaxis_title="Retorno indexado (base 100)",
                margin=dict(l=0, r=0, t=20, b=0),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter", color=TEXT_DIM, size=11),
                xaxis=dict(showgrid=False, tickfont=dict(color=TEXT_DARK, size=10)),
                yaxis=dict(gridcolor="rgba(128,128,128,0.1)",
                           tickfont=dict(color=TEXT_DARK, size=10)),
                legend=dict(orientation="h", y=-0.15,
                            font=dict(color=TEXT_MUT, size=11)),
                hoverlabel=dict(bgcolor=CARD, bordercolor=BORDER,
                                font=dict(color=TEXT, size=12)),
            )
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

        # ── Matriz de correlación ──────────────────────────────────────────
        with st.expander("Matriz de correlación entre activos"):
            tickers_corr = ["YPF", "MELI", "GGAL", "PAM", "GLOB", "ZS=F"]
            corr_df = fetch_correlation(tickers_corr, period=periodo)
            if corr_df.empty:
                st.info("Sin datos suficientes para calcular la correlación.")
            else:
                fig3 = px.imshow(
                    corr_df,
                    color_continuous_scale="RdYlGn",
                    zmin=-1, zmax=1,
                    text_auto=True,
                )
                fig3.update_layout(
                    height=380,
                    margin=dict(l=0, r=0, t=20, b=0),
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="Inter", color=TEXT_MUT, size=11),
                )
                st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})
            st.caption("Correlación de retornos diarios. Verde = mueven juntos, Rojo = inversos.")

    # ══════════════════════════════════════════════════════════════════════
    # ── TAB: NOTICIAS ────────────────────────────────────────────────────
    # ══════════════════════════════════════════════════════════════════════
    with tab_noticias:

        st.markdown('<div class="sec-label">Noticias económicas</div>', unsafe_allow_html=True)

        arts_infobae  = [n for n in noticias if n["medio"] == "infobae"]
        arts_lanacion = [n for n in noticias if n["medio"] == "lanacion"]
        arts_ambito   = [n for n in noticias if n["medio"] == "ambito"]
        arts_cronista = [n for n in noticias if n["medio"] == "cronista"]

        def _news_feed(arts: list[dict]) -> None:
            """Renderiza un feed de noticias con expanders."""
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


# ══════════════════════════════════════════════════════════════════════════════
# ── Entry point standalone ────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    from modules.constants import GLOBAL_CSS

    st.set_page_config(
        page_title="ArgentinaPulse",
        page_icon="🇦🇷",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
    render_pulse_module()
