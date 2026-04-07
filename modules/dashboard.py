# modules/dashboard.py
# ── Dashboard Maestro — PulseArg ─────────────────────────────────────────────
# Punto de entrada unificado que orquesta todos los módulos.
#
# Ejecución:
#   cd ~/Proyectos/PulseArg && streamlit run modules/dashboard.py

import sys
from pathlib import Path
from datetime import datetime

# ── sys.path: agrega el root del proyecto antes de cualquier import local ──────
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st

# ── Config global (debe ser el primer comando de Streamlit) ───────────────────
st.set_page_config(
    page_title="PulseArg",
    page_icon="🇦🇷",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS global (inyectado una sola vez aquí) ──────────────────────────────────
from modules.constants import GLOBAL_CSS
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# ── Imports de módulos (post-set_page_config) ─────────────────────────────────
from modules.pulse.dashboard      import render_pulse_module
from modules.markets.dashboard    import render_markets_module
from modules.infowar.dashboard    import render_infowar_module
from modules.regionwatch.dashboard import render_regionwatch_module
from modules.crisislab.dashboard  import render_crisislab_module
from core.config import RAW_DIR


# ══════════════════════════════════════════════════════════════════════════════
# ── Helpers ───────────────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

def _limpiar_cache() -> int:
    """Elimina todos los archivos de caché JSON para forzar refresh completo."""
    eliminados = 0
    for f in RAW_DIR.glob("*.json"):
        try:
            f.unlink()
            eliminados += 1
        except OSError:
            pass
    return eliminados


def _estado_cache() -> dict[str, bool]:
    """Retorna un mapa de clave → tiene_cache para los datos principales."""
    claves = ["dolar", "bcra_1", "bcra_27", "news", "snapshot"]
    return {k: (RAW_DIR / f"{k}.json").exists() for k in claves}


# ══════════════════════════════════════════════════════════════════════════════
# ── Sidebar de control global ─────────────────────────────────════════════════
# ══════════════════════════════════════════════════════════════════════════════

with st.sidebar:

    # Logo y título
    st.markdown("""
    <div style="padding: 8px 0 20px;">
        <div style="font-size: 1.3rem; font-weight: 700; color: #F1F5F9; letter-spacing: -0.3px;">
            🇦🇷 PulseArg
        </div>
        <div style="font-size: 0.68rem; color: #64748B; margin-top: 2px;">
            Dashboard de inteligencia — Argentina
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # ── Refresh settings ──────────────────────────────────────────────────────
    st.markdown("**⚙️ Refresh settings**")

    refresh_interval = st.selectbox(
        "Intervalo de actualización",
        options=[5, 15, 30, 60],
        index=2,          # 30 min por defecto
        format_func=lambda x: f"{x} min",
        key="sb_refresh_interval",
    )

    if st.button("🔄 Refresh Now", use_container_width=True, key="sb_refresh_btn"):
        n = _limpiar_cache()
        st.success(f"Caché limpiado ({n} archivo{'s' if n != 1 else ''}).")
        st.rerun()

    st.divider()

    # ── Toggles ───────────────────────────────────────────────────────────────
    st.markdown("**🎛️ Opciones**")

    live_mode   = st.toggle("Live mode",    value=True,  key="sb_live_mode",
                             help="Activa el badge 'Live' en los módulos.")
    show_details = st.toggle("Show details", value=True,  key="sb_show_details",
                              help="Muestra gráficos y secciones extendidas.")
    alerts_only  = st.toggle("Alerts only",  value=False, key="sb_alerts_only",
                              help="Oculta datos sin anomalías detectadas.")

    st.divider()

    # ── Estado de caché ───────────────────────────────────────────────────────
    st.markdown("**📡 Estado de datos**")

    estado = _estado_cache()
    labels = {
        "dolar":    "Dólar / TC",
        "bcra_1":   "Reservas BCRA",
        "bcra_27":  "Inflación BCRA",
        "news":     "Noticias RSS",
        "snapshot": "Activos",
    }
    for clave, tiene in estado.items():
        dot_cls = "dot-ok" if tiene else "dot-error"
        dot_txt = "OK" if tiene else "Sin caché"
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:8px;'
            f'font-size:0.72rem;color:#94A3B8;margin-bottom:4px;">'
            f'<span class="status-dot {dot_cls}"></span>'
            f'{labels.get(clave, clave)}'
            f'<span style="margin-left:auto;color:#475569;">{dot_txt}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.divider()

    # ── Timestamp sidebar ─────────────────────────────────────────────────────
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    st.markdown(
        f'<div style="font-size:0.65rem;color:#475569;text-align:center;">'
        f'Cargado: {now}</div>',
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
# ── Navbar superior ───────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

st.markdown(f"""
<div style="display:flex; align-items:center; justify-content:space-between;
            margin-bottom:20px; padding-bottom:16px; border-bottom:1px solid #334155;">
    <div style="display:flex; align-items:baseline; gap:12px;">
        <span style="font-size:1.4rem; font-weight:700; color:#F1F5F9; letter-spacing:-0.3px;">
            PulseArg
        </span>
        <span style="background:rgba(59,130,246,0.15); color:#60A5FA;
                     border:1px solid rgba(59,130,246,0.3);
                     border-radius:99px; font-size:0.6rem; font-weight:700;
                     letter-spacing:1.2px; padding:2px 9px; text-transform:uppercase;">
            {'LIVE' if st.session_state.get('sb_live_mode', True) else 'PAUSED'}
        </span>
    </div>
    <div style="font-size:0.72rem; color:#64748B;">
        {datetime.now().strftime('%d/%m/%Y  %H:%M')}
    </div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# ── Tabs principales ──────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

tab_pulse, tab_markets, tab_infowar, tab_rw, tab_crisis = st.tabs([
    "🇦🇷 ArgentinaPulse",
    "📈 Markets",
    "🗺️ InfoWarMapper",
    "🌎 RegionWatch",
    "🧪 CrisisLab",
])

# Leer settings del sidebar (con defaults seguros)
_refresh  = st.session_state.get("sb_refresh_interval", 30)
_details  = st.session_state.get("sb_show_details",     True)
_alerts   = st.session_state.get("sb_alerts_only",      False)

with tab_pulse:
    render_pulse_module(
        refresh_interval=_refresh,
        show_details=_details,
        alerts_only=_alerts,
    )

with tab_markets:
    render_markets_module(
        refresh_interval=_refresh,
        show_details=_details,
        alerts_only=_alerts,
    )

with tab_infowar:
    render_infowar_module(
        refresh_interval=_refresh,
        show_details=_details,
        alerts_only=_alerts,
    )

with tab_rw:
    render_regionwatch_module(
        refresh_interval=_refresh,
        show_details=_details,
        alerts_only=_alerts,
    )

with tab_crisis:
    render_crisislab_module(
        refresh_interval=_refresh,
        show_details=_details,
        alerts_only=_alerts,
    )


# ══════════════════════════════════════════════════════════════════════════════
# ── Footer ────────────────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

estado_footer = _estado_cache()
n_ok = sum(estado_footer.values())
n_total = len(estado_footer)
status_cls  = "dot-ok" if n_ok == n_total else ("dot-warn" if n_ok > 0 else "dot-error")
status_txt  = f"{n_ok}/{n_total} fuentes con caché"

st.markdown(f"""
<div class="pulse-footer">
    <span>
        <span class="status-dot {status_cls}"></span>
        {status_txt}
    </span>
    <span>PulseArg · Open Source · 100% local</span>
    <span>Intervalo: {_refresh} min</span>
</div>
""", unsafe_allow_html=True)
