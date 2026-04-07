# modules/regionwatch/dashboard.py
# ── Dashboard del módulo RegionWatch ─────────────────────────────────────────
# Scaffold — implementación futura.
# Para testing standalone: streamlit run modules/regionwatch/dashboard.py

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st


def render_regionwatch_module(refresh_interval: int = 30,
                               show_details: bool = True,
                               alerts_only: bool = False) -> None:
    """
    Renderiza el módulo RegionWatch como componente reutilizable.

    Pendiente de implementación — monitoreará indicadores económicos y
    políticos de los países vecinos y socios comerciales de Argentina.
    """
    st.markdown("""
    <div style="
        background: #1E293B;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 32px;
        text-align: center;
        margin-top: 16px;
    ">
        <div style="font-size: 2.4rem; margin-bottom: 12px;">🌎</div>
        <div style="font-size: 1.1rem; font-weight: 700; color: #F1F5F9; margin-bottom: 8px;">
            RegionWatch — En construcción
        </div>
        <div style="font-size: 0.82rem; color: #64748B; max-width: 420px; margin: 0 auto;">
            Monitoreará indicadores económicos, riesgo país y eventos relevantes
            en Brasil, Chile, Uruguay, Bolivia, Paraguay y otros socios regionales.
        </div>
    </div>
    """, unsafe_allow_html=True)


# ── Entry point standalone ────────────────────────────────────────────────────

if __name__ == "__main__":
    from modules.constants import GLOBAL_CSS

    st.set_page_config(
        page_title="RegionWatch — PulseArg",
        page_icon="🌎",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
    render_regionwatch_module()
