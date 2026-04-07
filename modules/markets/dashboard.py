# modules/markets/dashboard.py
# ── Dashboard del módulo Markets ──────────────────────────────────────────────
# Para testing standalone: streamlit run modules/markets/dashboard.py

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

try:
    from .fetchers import (
        fetch_merval, fetch_adrs, fetch_commodities,
        fetch_history_ddb, fetch_sparklines,
    )
    from .constants import (
        MARKETS_CSS, ADR_TICKERS, COMMODITY_TICKERS, MERVAL_COMPONENTS,
        ADR_SECTOR_LABELS, PERIODOS, PERIODO_DIAS,
        CARD, BORDER, BLUE, BLUE_LT, TEXT, TEXT_MUT, TEXT_DIM, TEXT_DARK,
        GREEN, AMBER, RED, TEAL, PURPLE,
    )
except ImportError:
    from modules.markets.fetchers import (
        fetch_merval, fetch_adrs, fetch_commodities,
        fetch_history_ddb, fetch_sparklines,
    )
    from modules.markets.constants import (
        MARKETS_CSS, ADR_TICKERS, COMMODITY_TICKERS, MERVAL_COMPONENTS,
        ADR_SECTOR_LABELS, PERIODOS, PERIODO_DIAS,
        CARD, BORDER, BLUE, BLUE_LT, TEXT, TEXT_MUT, TEXT_DIM, TEXT_DARK,
        GREEN, AMBER, RED, TEAL, PURPLE,
    )

from core.duck import get_alerts, set_alert, delete_alert


# ══════════════════════════════════════════════════════════════════════════════
# ── Helpers ───────────────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

def _sparkline_svg(values: list[float], width: int = 80, height: int = 26) -> str:
    """Genera un SVG sparkline minimalista a partir de una lista de precios."""
    vals = [v for v in values if v is not None and v == v]  # drop None/NaN
    if len(vals) < 2:
        return ""
    mn, mx = min(vals), max(vals)
    rng     = mx - mn if mx != mn else 1.0
    n       = len(vals)
    pad     = 1.5
    h_inner = height - 2 * pad
    pts     = " ".join(
        f"{i / (n - 1) * width:.1f},{pad + h_inner - (v - mn) / rng * h_inner:.1f}"
        for i, v in enumerate(vals)
    )
    color = "#34D399" if vals[-1] >= vals[0] else "#FCA5A5"
    return (
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'style="display:block;overflow:visible">'
        f'<polyline points="{pts}" fill="none" stroke="{color}" '
        f'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>'
        f'</svg>'
    )


def _change_badge(var_pct) -> str:
    """HTML de badge con variación porcentual."""
    if var_pct is None:
        return f'<span class="st-flat">—</span>'
    sign = "+" if var_pct > 0 else ""
    cls  = "st-up" if var_pct > 0 else ("st-down" if var_pct < 0 else "st-flat")
    return f'<span class="{cls}">{sign}{var_pct:.2f}%</span>'


def _fmt_price(precio, moneda: str = "USD") -> str:
    """Formatea precio con moneda. Retorna — si es None."""
    if precio is None:
        return '<span style="color:#475569;font-style:italic;">—</span>'
    if moneda == "ARS":
        return f"$ {precio:,.0f}"
    return f"$ {precio:,.2f}"


def _plot_defaults() -> dict:
    """Layout base compartido para todos los charts Plotly."""
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color=TEXT_DIM, size=11),
        margin=dict(l=0, r=0, t=20, b=0),
        xaxis=dict(showgrid=False, zeroline=False, tickfont=dict(color=TEXT_DARK, size=10)),
        yaxis=dict(gridcolor="rgba(51,65,85,0.35)", zeroline=False,
                   tickfont=dict(color=TEXT_DARK, size=10)),
        hoverlabel=dict(bgcolor=CARD, bordercolor=BORDER, font=dict(color=TEXT, size=12)),
        hovermode="x unified",
    )


def _render_spark_tile(nombre: str, ticker: str, precio, var_pct,
                       sparkline_vals: list[float], sector_cls: str,
                       exchange: str = "", unidad: str = "",
                       alert_active: bool = False) -> None:
    """Renderiza un spark tile completo con SVG sparkline."""
    spark_svg    = _sparkline_svg(sparkline_vals) if sparkline_vals else ""
    change_badge = _change_badge(var_pct)
    price_html   = _fmt_price(precio, "USD")
    alert_html   = '<span class="st-alert-badge">⚠ Alerta</span>' if alert_active else ""
    sub_line     = (
        f'<div class="st-exch">{exchange}</div>' if exchange
        else f'<div class="st-unit">{unidad}</div>' if unidad
        else ""
    )
    spark_block = f'<div class="st-sparkline">{spark_svg}</div>' if spark_svg else ""

    st.markdown(f"""
    <div class="spark-tile {sector_cls}">
        <div class="st-header">
            <span class="st-name">{nombre}</span>
            <span class="st-ticker">{ticker}</span>
        </div>
        {sub_line}
        <div class="st-price">{price_html}</div>
        {change_badge}{alert_html}
        {spark_block}
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# ── Alertas de precio ─────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

def _check_alerts(df_adrs: pd.DataFrame, df_comm: pd.DataFrame,
                  alerts: list[dict]) -> list[dict]:
    """
    Cruza precios actuales contra umbrales.
    Retorna lista de alertas disparadas: [{ticker, nombre, precio, threshold, direction}, ...].
    """
    if not alerts:
        return []

    prices: dict[str, float] = {}
    names:  dict[str, str]   = {}

    for df, meta_map in [(df_adrs, ADR_TICKERS), (df_comm, COMMODITY_TICKERS)]:
        if df is None or df.empty:
            continue
        for _, row in df.iterrows():
            t = row.get("ticker", "")
            p = row.get("precio")
            if t and p is not None:
                prices[t] = float(p)
                names[t]  = row.get("nombre", t)

    triggered = []
    for alert in alerts:
        t = alert["ticker"]
        precio = prices.get(t)
        if precio is None:
            continue
        if alert["direction"] == "above" and precio > alert["threshold"]:
            triggered.append({**alert, "precio": precio, "nombre": names.get(t, t)})
        elif alert["direction"] == "below" and precio < alert["threshold"]:
            triggered.append({**alert, "precio": precio, "nombre": names.get(t, t)})
    return triggered


def _render_alert_banners(triggered: list[dict]) -> None:
    """Muestra banners de alerta por cada precio disparado."""
    for a in triggered:
        direction_lbl = "subió sobre" if a["direction"] == "above" else "bajó bajo"
        st.warning(
            f"⚠ **{a['nombre']} ({a['ticker']})** {direction_lbl} "
            f"**${a['threshold']:,.2f}** — precio actual: **${a['precio']:,.2f}**"
        )


# ══════════════════════════════════════════════════════════════════════════════
# ── Tab: Merval ───────────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

def _tab_merval(merval: dict, df_adrs: pd.DataFrame, show_details: bool) -> None:
    precio  = merval.get("precio")
    var_pct = merval.get("var_pct")
    max_52w = merval.get("max_52w")
    min_52w = merval.get("min_52w")
    moneda  = merval.get("moneda", "ARS")

    # ── Hero tile ─────────────────────────────────────────────────────────────
    if precio is not None:
        change_cls = "mh-up" if (var_pct or 0) >= 0 else "mh-down"
        sign       = "+" if (var_pct or 0) >= 0 else ""
        price_str  = f"$ {precio:,.0f}"
        change_str = f"{sign}{var_pct:.2f}%" if var_pct is not None else "—"
        sub_str    = f"{moneda} · Bolsa de Comercio de Buenos Aires"
    else:
        change_cls = "mh-flat"
        price_str  = "—"
        change_str = "—"
        sub_str    = "Sin datos disponibles"

    col_hero, col_stats = st.columns([2, 1])
    with col_hero:
        st.markdown(f"""
        <div class="merval-hero">
            <div class="mh-label">ÍNDICE MERVAL</div>
            <div class="mh-price">{price_str}</div>
            <span class="{change_cls}">{change_str}</span>
            <div class="mh-sub">{sub_str}</div>
        </div>
        """, unsafe_allow_html=True)

    with col_stats:
        st.markdown('<div style="height:4px"></div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            max_str = f"$ {max_52w:,.0f}" if max_52w else "—"
            st.markdown(f"""
            <div class="merval-hero" style="padding:16px 20px 14px">
                <div class="mh-stat-label">Máx. 52s</div>
                <div class="mh-stat-val">{max_str}</div>
            </div>""", unsafe_allow_html=True)
        with c2:
            min_str = f"$ {min_52w:,.0f}" if min_52w else "—"
            st.markdown(f"""
            <div class="merval-hero" style="padding:16px 20px 14px">
                <div class="mh-stat-label">Mín. 52s</div>
                <div class="mh-stat-val">{min_str}</div>
            </div>""", unsafe_allow_html=True)

    if not show_details:
        return

    # ── Composición: variación diaria de componentes ──────────────────────────
    st.markdown('<div class="sec-label">Composición — variación del día</div>',
                unsafe_allow_html=True)

    if not df_adrs.empty:
        df_comp = (
            df_adrs[df_adrs["ticker"].isin(MERVAL_COMPONENTS)]
            .dropna(subset=["var_pct"])
            .sort_values("var_pct", ascending=True)
        )
        if not df_comp.empty:
            colors = [GREEN if v >= 0 else RED for v in df_comp["var_pct"]]
            fig = go.Figure(go.Bar(
                x=df_comp["var_pct"],
                y=df_comp["nombre"],
                orientation="h",
                marker_color=colors,
                text=[f"{v:+.2f}%" for v in df_comp["var_pct"]],
                textposition="outside",
                textfont=dict(color=TEXT_MUT, size=11),
                hovertemplate="<b>%{y}</b><br>%{x:+.2f}%<extra></extra>",
            ))
            layout = _plot_defaults()
            layout.update(
                height=280,
                xaxis=dict(
                    showgrid=True, gridcolor="rgba(51,65,85,0.35)", zeroline=True,
                    zerolinecolor=BORDER, ticksuffix="%",
                    tickfont=dict(color=TEXT_DARK, size=10),
                ),
                yaxis=dict(showgrid=False, tickfont=dict(color=TEXT, size=11)),
                hovermode="closest",
            )
            fig.update_layout(**layout)
            st.plotly_chart(fig, use_container_width=True,
                            config={"displayModeBar": False})
        else:
            st.info("Sin datos de componentes.")
    else:
        st.info("Sin datos de ADRs para mostrar composición.")

    # ── Histórico del Merval ──────────────────────────────────────────────────
    st.markdown('<div class="sec-label">Histórico Merval</div>', unsafe_allow_html=True)

    col_p, _ = st.columns([1, 3])
    with col_p:
        periodo = st.selectbox("Período", PERIODOS, index=1, key="mkt_merval_periodo")

    hist = fetch_history_ddb("^MERV", period=periodo)
    if not hist.empty and "Close" in hist.columns:
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=hist.index, y=hist["Close"],
            fill="tozeroy",
            fillcolor="rgba(251,113,133,0.06)",
            line=dict(color="#FB7185", width=2),
            mode="lines",
            hovertemplate="<b>%{x|%d %b %Y}</b><br>$ %{y:,.0f}<extra></extra>",
        ))
        fig2.add_trace(go.Scatter(
            x=[hist.index[-1]], y=[hist["Close"].iloc[-1]],
            mode="markers",
            marker=dict(color="#FDA4AF", size=7,
                        line=dict(color="#0F172A", width=2)),
            showlegend=False,
            hovertemplate="<b>Último:</b> $ %{y:,.0f}<extra></extra>",
        ))
        layout2 = _plot_defaults()
        layout2.update(
            height=300,
            yaxis=dict(
                gridcolor="rgba(51,65,85,0.35)", zeroline=False,
                tickfont=dict(color=TEXT_DARK, size=10),
                tickformat=",.0f",
            ),
            showlegend=False,
        )
        fig2.update_layout(**layout2)
        st.plotly_chart(fig2, use_container_width=True,
                        config={"displayModeBar": False})
    else:
        st.info("Sin historial del Merval disponible.")


# ══════════════════════════════════════════════════════════════════════════════
# ── Tab: ADRs ─────────────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

def _tab_adrs(df_adrs: pd.DataFrame, alerts: list[dict], show_details: bool) -> None:
    if df_adrs.empty:
        st.info("Sin datos de ADRs disponibles.")
        return

    alert_tickers = {a["ticker"] for a in alerts}

    # ── Sub-tabs por sector ───────────────────────────────────────────────────
    sector_options = ["Todos"] + [v[0] for v in ADR_SECTOR_LABELS.values()]
    sector_keys    = ["todos"] + list(ADR_SECTOR_LABELS.keys())
    sub_tabs       = st.tabs(sector_options)

    for stab, sector_key in zip(sub_tabs, sector_keys):
        with stab:
            if sector_key == "todos":
                df_view = df_adrs.copy()
            else:
                df_view = df_adrs[df_adrs["sector"] == sector_key].copy()

            if df_view.empty:
                st.markdown(
                    f'<p style="color:{TEXT_DIM};font-size:0.82rem;padding:12px 0;">'
                    'Sin activos en este sector.</p>',
                    unsafe_allow_html=True,
                )
                continue

            # Cargar sparklines para este grupo
            tickers_view = df_view["ticker"].tolist()
            sparks = fetch_sparklines(tickers_view, period="1mo")

            rows_list = df_view.to_dict("records")
            for i in range(0, len(rows_list), 3):
                chunk = rows_list[i:i+3]
                cols  = st.columns(3)
                for j, row in enumerate(chunk):
                    tk     = row.get("ticker", "")
                    sec    = row.get("sector", "tech")
                    s_info = ADR_SECTOR_LABELS.get(sec, ("", "accent-blue", "st-tech"))
                    s_cls  = s_info[2] if len(s_info) > 2 else "st-tech"
                    with cols[j]:
                        _render_spark_tile(
                            nombre=row.get("nombre", tk),
                            ticker=tk,
                            precio=row.get("precio"),
                            var_pct=row.get("var_pct"),
                            sparkline_vals=sparks.get(tk, []),
                            sector_cls=s_cls,
                            exchange=row.get("exchange", ""),
                            alert_active=(tk in alert_tickers),
                        )
                st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)

    if not show_details:
        return

    # ── Comparación histórica ADRs ────────────────────────────────────────────
    st.markdown('<div class="sec-label">Comparación histórica</div>',
                unsafe_allow_html=True)

    col_sel, col_per = st.columns([3, 1])
    with col_sel:
        opciones = {
            f"{r['nombre']} ({r['ticker']})": r["ticker"]
            for _, r in df_adrs.dropna(subset=["precio"]).iterrows()
        }
        default = [k for k in ["YPF (YPF)", "Galicia (GGAL)", "MercadoLibre (MELI)"]
                   if k in opciones]
        seleccion = st.multiselect(
            "Activos", options=list(opciones.keys()), default=default,
            key="mkt_adrs_seleccion",
        )
    with col_per:
        periodo = st.selectbox("Período", PERIODOS, index=1, key="mkt_adrs_periodo")

    if seleccion:
        fig = go.Figure()
        palette = [BLUE_LT, GREEN, AMBER, TEAL, PURPLE, "#FB7185", "#7DD3FC", "#FCD34D"]
        for idx, label in enumerate(seleccion):
            ticker = opciones[label]
            hist   = fetch_history_ddb(ticker, period=periodo)
            if not hist.empty and "Close" in hist.columns:
                close = hist["Close"].dropna()
                norm  = (close / close.iloc[0]) * 100
                fig.add_trace(go.Scatter(
                    x=norm.index, y=norm.values,
                    mode="lines", name=label,
                    line=dict(color=palette[idx % len(palette)], width=2),
                    hovertemplate=f"<b>{label}</b><br>%{{x|%d %b}}: %{{y:.1f}}<extra></extra>",
                ))
        layout = _plot_defaults()
        layout.update(
            height=360,
            yaxis_title="Retorno indexado (base 100)",
            legend=dict(orientation="h", y=-0.18, font=dict(color=TEXT_MUT, size=11)),
        )
        fig.update_layout(**layout)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.caption("Retornos normalizados a base 100 desde el inicio del período.")


# ══════════════════════════════════════════════════════════════════════════════
# ── Tab: Commodities ──────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

def _tab_commodities(df_comm: pd.DataFrame, show_details: bool) -> None:
    if df_comm.empty:
        st.info("Sin datos de commodities disponibles.")
        return

    # ── Tiles con sparklines ──────────────────────────────────────────────────
    st.markdown('<div class="sec-label">Precios actuales</div>', unsafe_allow_html=True)

    tickers_comm = df_comm["ticker"].tolist()
    sparks = fetch_sparklines(tickers_comm, period="1mo")

    rows_list = df_comm.to_dict("records")
    cols = st.columns(4)
    for j, row in enumerate(rows_list):
        tk = row.get("ticker", "")
        with cols[j % 4]:
            _render_spark_tile(
                nombre=row.get("nombre", tk),
                ticker=tk,
                precio=row.get("precio"),
                var_pct=row.get("var_pct"),
                sparkline_vals=sparks.get(tk, []),
                sector_cls=row.get("cls", "st-soja"),
                unidad=row.get("unidad", ""),
            )

    if not show_details:
        return

    # ── Histórico de commodities ──────────────────────────────────────────────
    st.markdown('<div class="sec-label">Histórico de commodities</div>',
                unsafe_allow_html=True)

    col_sel2, col_per2 = st.columns([3, 1])
    with col_sel2:
        opciones_c = {
            f"{r['emoji']} {r['nombre']} ({r['ticker']})": r["ticker"]
            for _, r in df_comm.dropna(subset=["precio"]).iterrows()
        }
        seleccion_c = st.multiselect(
            "Commodities", options=list(opciones_c.keys()),
            default=list(opciones_c.keys()),
            key="mkt_comm_seleccion",
        )
    with col_per2:
        periodo_c = st.selectbox("Período", PERIODOS, index=1, key="mkt_comm_periodo")

    if seleccion_c:
        fig = go.Figure()
        palette = [GREEN, AMBER, TEAL, "#FB7185"]
        for idx, label in enumerate(seleccion_c):
            ticker = opciones_c[label]
            hist   = fetch_history_ddb(ticker, period=periodo_c)
            if not hist.empty and "Close" in hist.columns:
                close = hist["Close"].dropna()
                norm  = (close / close.iloc[0]) * 100
                fig.add_trace(go.Scatter(
                    x=norm.index, y=norm.values,
                    mode="lines", name=label,
                    line=dict(color=palette[idx % len(palette)], width=2),
                    hovertemplate=f"<b>{label}</b><br>%{{x|%d %b}}: %{{y:.1f}}<extra></extra>",
                ))
        layout = _plot_defaults()
        layout.update(
            height=340,
            yaxis_title="Retorno indexado (base 100)",
            legend=dict(orientation="h", y=-0.18, font=dict(color=TEXT_MUT, size=11)),
        )
        fig.update_layout(**layout)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.caption("Futuros CME (soja, maíz, trigo) y WTI. Normalizados a base 100.")


# ══════════════════════════════════════════════════════════════════════════════
# ── Tab: Comparación ──────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

def _tab_comparacion(df_adrs: pd.DataFrame, df_comm: pd.DataFrame,
                     show_details: bool) -> None:
    # Universo combinado
    all_assets: dict[str, str] = {}
    if not df_adrs.empty:
        for _, r in df_adrs.dropna(subset=["precio"]).iterrows():
            all_assets[f"{r['nombre']} ({r['ticker']})"] = r["ticker"]
    if not df_comm.empty:
        for _, r in df_comm.dropna(subset=["precio"]).iterrows():
            all_assets[f"{r.get('emoji','')} {r['nombre']} ({r['ticker']})"] = r["ticker"]
    all_assets["📈 Merval (^MERV)"] = "^MERV"

    if not all_assets:
        st.info("Sin datos disponibles.")
        return

    col_sel, col_per = st.columns([3, 1])
    with col_sel:
        default_comp = [k for k in [
            "YPF (YPF)", "Galicia (GGAL)", "🌱 Soja (ZS=F)", "📈 Merval (^MERV)"
        ] if k in all_assets]
        seleccion = st.multiselect(
            "Activos a comparar", options=list(all_assets.keys()),
            default=default_comp, key="mkt_comp_seleccion",
        )
    with col_per:
        periodo = st.selectbox("Período", PERIODOS, index=1, key="mkt_comp_periodo")

    # ── Gráfico indexado ──────────────────────────────────────────────────────
    if seleccion:
        fig = go.Figure()
        palette = [BLUE_LT, GREEN, AMBER, TEAL, PURPLE, "#FB7185",
                   "#7DD3FC", "#FCD34D", "#5EEAD4", "#C4B5FD"]
        for idx, label in enumerate(seleccion):
            ticker = all_assets[label]
            hist   = fetch_history_ddb(ticker, period=periodo)
            if not hist.empty and "Close" in hist.columns:
                close = hist["Close"].dropna()
                norm  = (close / close.iloc[0]) * 100
                fig.add_trace(go.Scatter(
                    x=norm.index, y=norm.values,
                    mode="lines", name=label,
                    line=dict(color=palette[idx % len(palette)], width=2),
                    hovertemplate=f"<b>{label}</b><br>%{{x|%d %b}}: %{{y:.1f}}<extra></extra>",
                ))
        layout = _plot_defaults()
        layout.update(
            height=380,
            yaxis_title="Retorno indexado (base 100)",
            legend=dict(orientation="h", y=-0.18, font=dict(color=TEXT_MUT, size=11)),
        )
        fig.update_layout(**layout)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    if not show_details:
        return

    # ── Matriz de correlación ─────────────────────────────────────────────────
    with st.expander("Matriz de correlación entre activos"):
        sel_corr = [all_assets[k] for k in seleccion] if seleccion else []
        if len(sel_corr) < 2:
            st.info("Seleccioná al menos 2 activos para calcular la correlación.")
        else:
            closes = {}
            for label, ticker in [(k, all_assets[k]) for k in seleccion]:
                hist = fetch_history_ddb(ticker, period=periodo)
                if not hist.empty and "Close" in hist.columns:
                    s = hist["Close"].dropna()
                    if len(s) > 5:
                        closes[label] = s
            if len(closes) >= 2:
                combined = pd.DataFrame(closes)
                corr_df  = combined.pct_change().dropna().corr().round(3)
                fig_corr = px.imshow(
                    corr_df,
                    color_continuous_scale="RdYlGn",
                    zmin=-1, zmax=1,
                    text_auto=True,
                )
                fig_corr.update_layout(
                    height=380,
                    margin=dict(l=0, r=0, t=20, b=0),
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="Inter", color=TEXT_MUT, size=11),
                )
                st.plotly_chart(fig_corr, use_container_width=True,
                                config={"displayModeBar": False})
                st.caption(
                    "Correlación de retornos diarios. Verde = mueven juntos, Rojo = inversos."
                )
            else:
                st.info("Sin suficientes datos para la correlación.")


# ══════════════════════════════════════════════════════════════════════════════
# ── Configuración de alertas ─────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

def _alert_config_expander(df_adrs: pd.DataFrame, df_comm: pd.DataFrame,
                           alerts: list[dict]) -> None:
    """Expander para ver y configurar alertas de precio."""
    with st.expander("🔔 Configuración de alertas de precio"):

        # Mostrar alertas activas
        if alerts:
            st.markdown(f'<div class="sec-label">Alertas activas</div>',
                        unsafe_allow_html=True)
            for a in alerts:
                dir_lbl = "sube sobre" if a["direction"] == "above" else "baja bajo"
                col_a, col_b = st.columns([4, 1])
                with col_a:
                    st.markdown(
                        f'**{a["ticker"]}** — cuando {dir_lbl} **${a["threshold"]:,.2f}**',
                        unsafe_allow_html=True,
                    )
                with col_b:
                    if st.button("Eliminar", key=f"del_{a['ticker']}_{a['direction']}"):
                        delete_alert(a["ticker"], a["direction"])
                        st.rerun()
        else:
            st.caption("No hay alertas configuradas.")

        st.divider()

        # Agregar nueva alerta
        st.markdown(f'<div class="sec-label">Nueva alerta</div>',
                    unsafe_allow_html=True)

        all_tickers: list[str] = []
        if not df_adrs.empty:
            all_tickers += df_adrs["ticker"].dropna().tolist()
        if not df_comm.empty:
            all_tickers += df_comm["ticker"].dropna().tolist()

        if all_tickers:
            c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
            with c1:
                new_ticker = st.selectbox("Ticker", options=all_tickers,
                                          key="mkt_alert_ticker")
            with c2:
                new_threshold = st.number_input("Umbral (USD)", min_value=0.01,
                                                value=10.0, step=0.5,
                                                key="mkt_alert_threshold")
            with c3:
                new_direction = st.selectbox("Dirección",
                                             options=["above", "below"],
                                             format_func=lambda x: "↑ Sube sobre" if x == "above" else "↓ Baja bajo",
                                             key="mkt_alert_direction")
            with c4:
                st.markdown('<div style="height:28px"></div>', unsafe_allow_html=True)
                if st.button("Agregar", key="mkt_alert_add"):
                    set_alert(new_ticker, new_threshold, new_direction)
                    st.success(f"Alerta guardada para {new_ticker}.")
                    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# ── Función principal ─────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

def render_markets_module(refresh_interval: int = 30,
                          show_details: bool = True,
                          alerts_only: bool = False) -> None:
    """
    Renderiza el módulo Markets completo.

    Parámetros
    ----------
    refresh_interval : int
        Intervalo de actualización en minutos (informativo).
    show_details : bool
        Si True muestra gráficos y secciones extendidas.
    alerts_only : bool
        Si True muestra solo banners de alertas activas.
    """
    # Inyectar CSS del módulo
    st.markdown(MARKETS_CSS, unsafe_allow_html=True)

    # ── Fetch de datos ────────────────────────────────────────────────────────
    with st.spinner("Cargando datos de mercados…"):
        merval  = fetch_merval()
        df_adrs = fetch_adrs()
        df_comm = fetch_commodities()
        alerts  = get_alerts()

    # ── Header ────────────────────────────────────────────────────────────────
    ts = datetime.now().strftime("%d/%m/%Y  %H:%M")
    st.markdown(f"""
    <div class="pulse-header">
        <span class="pulse-title">📈 Markets</span>
        <span class="pulse-badge">Live</span>
    </div>
    <div class="pulse-ts">Última actualización: {ts} · Intervalo: {refresh_interval} min</div>
    """, unsafe_allow_html=True)

    # ── Alertas disparadas ────────────────────────────────────────────────────
    triggered = _check_alerts(df_adrs, df_comm, alerts)
    if triggered:
        _render_alert_banners(triggered)

    if alerts_only and not triggered:
        st.info("Sin alertas activas en este momento.")
        return

    # ── Tabs principales ──────────────────────────────────────────────────────
    tab_m, tab_a, tab_c, tab_comp = st.tabs([
        "📊 Merval",
        "🏛️ ADRs",
        "🌾 Commodities",
        "📈 Comparación",
    ])

    with tab_m:
        _tab_merval(merval, df_adrs, show_details)

    with tab_a:
        _tab_adrs(df_adrs, alerts, show_details)

    with tab_c:
        _tab_commodities(df_comm, show_details)

    with tab_comp:
        _tab_comparacion(df_adrs, df_comm, show_details)

    # ── Configuración de alertas ──────────────────────────────────────────────
    _alert_config_expander(df_adrs, df_comm, alerts)


# ══════════════════════════════════════════════════════════════════════════════
# ── Entry point standalone ────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    from modules.constants import GLOBAL_CSS

    st.set_page_config(
        page_title="Markets — PulseArg",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
    render_markets_module()
