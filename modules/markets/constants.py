# modules/markets/constants.py
# ── Constantes del módulo Markets ────────────────────────────────────────────

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from modules.constants import (  # noqa: F401
    BG, CARD, BORDER,
    BLUE, BLUE_LT, SKY, TEAL, GREEN, AMBER, RED, PURPLE, ROSE,
    TEXT, TEXT_MUT, TEXT_DIM, TEXT_DARK,
)

# ── ADRs argentinos en NYSE / NASDAQ ─────────────────────────────────────────
ADR_TICKERS: dict[str, dict] = {
    "YPF":  {"nombre": "YPF S.A.",         "sector": "energia",  "exchange": "NYSE",   "emoji": "🛢️"},
    "PAM":  {"nombre": "Pampa Energía",     "sector": "energia",  "exchange": "NYSE",   "emoji": "⚡"},
    "VIST": {"nombre": "Vista Energy",      "sector": "energia",  "exchange": "NYSE",   "emoji": "🔋"},
    "MELI": {"nombre": "MercadoLibre",      "sector": "tech",     "exchange": "NASDAQ", "emoji": "🛒"},
    "GLOB": {"nombre": "Globant",           "sector": "tech",     "exchange": "NYSE",   "emoji": "💻"},
    "GGAL": {"nombre": "Galicia",           "sector": "finanzas", "exchange": "NASDAQ", "emoji": "🏦"},
    "BMA":  {"nombre": "Banco Macro",       "sector": "finanzas", "exchange": "NYSE",   "emoji": "🏛️"},
    "SUPV": {"nombre": "Supervielle",       "sector": "finanzas", "exchange": "NYSE",   "emoji": "💳"},
    "DESP": {"nombre": "Despegar",          "sector": "tech",     "exchange": "NYSE",   "emoji": "✈️"},
    "TEO":  {"nombre": "Telecom Argentina", "sector": "tech",     "exchange": "NYSE",   "emoji": "📡"},
}

# ── Commodities (futuros CME + WTI) ──────────────────────────────────────────
COMMODITY_TICKERS: dict[str, dict] = {
    "ZS=F": {"nombre": "Soja",         "unidad": "USC/bu",  "emoji": "🌱", "accent": "accent-green", "cls": "st-soja"},
    "ZC=F": {"nombre": "Maíz",         "unidad": "USC/bu",  "emoji": "🌽", "accent": "accent-amber", "cls": "st-maiz"},
    "ZW=F": {"nombre": "Trigo",        "unidad": "USC/bu",  "emoji": "🌾", "accent": "accent-teal",  "cls": "st-trigo"},
    "CL=F": {"nombre": "Petróleo WTI", "unidad": "USD/bbl", "emoji": "🛢️", "accent": "accent-rose",  "cls": "st-wti"},
}

# ── Composición del Merval (principales componentes) ─────────────────────────
MERVAL_COMPONENTS: list[str] = ["YPF", "GGAL", "PAM", "BMA", "SUPV", "VIST", "MELI", "GLOB"]

# ── Etiquetas y acento por sector de ADRs ────────────────────────────────────
ADR_SECTOR_LABELS: dict[str, tuple[str, str]] = {
    "energia":  ("⚡ Energía",  "accent-amber",  "st-energia"),
    "finanzas": ("🏦 Finanzas", "accent-teal",   "st-finanzas"),
    "tech":     ("💻 Tech",     "accent-purple",  "st-tech"),
}

# ── Períodos disponibles ──────────────────────────────────────────────────────
PERIODOS: list[str] = ["1mo", "3mo", "6mo", "1y"]

PERIODO_DIAS: dict[str, int] = {
    "1mo": 35,
    "3mo": 95,
    "6mo": 185,
    "1y":  370,
    "2y":  740,
}

# ── Tipos de activos (para roadmap y display) ─────────────────────────────────
ASSET_TYPES = {
    "merval":      ("Merval",      "accent-rose"),
    "adrs":        ("ADRs",        "accent-blue"),
    "commodities": ("Commodities", "accent-green"),
}

# ── CSS adicional del módulo Markets ──────────────────────────────────────────
MARKETS_CSS = f"""
<style>
/* ── Spark Tile ── */
.spark-tile {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: 12px;
    padding: 14px 16px 10px;
    transition: border-color 0.2s, transform 0.15s;
    position: relative;
    overflow: hidden;
    min-height: 118px;
}}
.spark-tile:hover {{ border-color: {BLUE}; transform: translateY(-2px); }}
.spark-tile::before {{
    content: '';
    position: absolute; top: 0; left: 0; right: 0;
    height: 3px; border-radius: 12px 12px 0 0;
}}
.st-energia::before  {{ background: linear-gradient(90deg, #D97706, #FCD34D); }}
.st-finanzas::before {{ background: linear-gradient(90deg, #0F766E, #5EEAD4); }}
.st-tech::before     {{ background: linear-gradient(90deg, #7C3AED, #C4B5FD); }}
.st-soja::before     {{ background: linear-gradient(90deg, #059669, #34D399); }}
.st-maiz::before     {{ background: linear-gradient(90deg, #D97706, #FCD34D); }}
.st-trigo::before    {{ background: linear-gradient(90deg, #0F766E, #5EEAD4); }}
.st-wti::before      {{ background: linear-gradient(90deg, #E11D48, #FDA4AF); }}

.st-header {{
    display: flex; justify-content: space-between; align-items: flex-start;
    margin-bottom: 3px;
}}
.st-name   {{ font-size: 0.79rem; font-weight: 600; color: {TEXT}; line-height: 1.2; }}
.st-ticker {{
    font-size: 0.59rem; font-weight: 700; color: {TEXT_DIM};
    text-transform: uppercase; letter-spacing: 0.8px; white-space: nowrap;
}}
.st-exch {{ font-size: 0.57rem; color: {TEXT_DARK}; }}
.st-price {{
    font-size: 1.18rem; font-weight: 700; color: {TEXT};
    font-variant-numeric: tabular-nums; margin: 4px 0 2px; line-height: 1;
}}
.st-up   {{ display:inline-block; padding:2px 7px; border-radius:99px; font-size:0.60rem; font-weight:700;
            background:rgba(16,185,129,0.15); color:#34D399; }}
.st-down {{ display:inline-block; padding:2px 7px; border-radius:99px; font-size:0.60rem; font-weight:700;
            background:rgba(239,68,68,0.15); color:#FCA5A5; }}
.st-flat {{ display:inline-block; padding:2px 7px; border-radius:99px; font-size:0.60rem; font-weight:700;
            background:rgba(148,163,184,0.15); color:{TEXT_MUT}; }}
.st-sparkline {{ margin-top:6px; line-height:0; display:block; }}
.st-unit  {{ font-size:0.57rem; color:{TEXT_DARK}; margin-top:3px; }}
.st-alert-badge {{
    display:inline-block; padding:2px 7px; border-radius:99px; font-size:0.58rem; font-weight:700;
    background:rgba(245,158,11,0.15); color:#FCD34D; margin-left:6px;
}}

/* ── Merval hero ── */
.merval-hero {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: 16px;
    padding: 24px 28px 20px;
    position: relative; overflow: hidden;
    margin-bottom: 4px;
}}
.merval-hero::before {{
    content: '';
    position: absolute; top: 0; left: 0; right: 0;
    height: 4px; border-radius: 16px 16px 0 0;
    background: linear-gradient(90deg, #E11D48, #FDA4AF, #FB7185);
}}
.mh-label  {{
    font-size: 0.66rem; font-weight: 700; color: {TEXT_DIM};
    text-transform: uppercase; letter-spacing: 1.6px;
}}
.mh-price  {{
    font-size: 2.6rem; font-weight: 700; color: {TEXT};
    font-variant-numeric: tabular-nums; line-height: 1.1; margin: 8px 0 4px;
}}
.mh-up   {{ display:inline-block; padding:4px 14px; border-radius:99px; font-size:0.82rem; font-weight:700;
            background:rgba(16,185,129,0.15); color:#34D399; }}
.mh-down {{ display:inline-block; padding:4px 14px; border-radius:99px; font-size:0.82rem; font-weight:700;
            background:rgba(239,68,68,0.15); color:#FCA5A5; }}
.mh-sub  {{ font-size:0.72rem; color:{TEXT_DIM}; margin-top:8px; }}
.mh-stat-label {{ font-size:0.62rem; color:{TEXT_DIM}; text-transform:uppercase; letter-spacing:1px; margin-bottom:4px; }}
.mh-stat-val   {{ font-size:1.05rem; font-weight:700; color:{TEXT}; font-variant-numeric:tabular-nums; }}
</style>
"""
