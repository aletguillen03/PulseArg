# modules/constants.py
# ── Paleta y CSS global del dashboard PulseArg ──────────────────────────────
# Importar en cada módulo para mantener coherencia visual.

# ── Paleta dark theme ─────────────────────────────────────────────────────────
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

# ── Tipografía ────────────────────────────────────────────────────────────────
FONT_FAMILY     = "Inter"
FONT_SIZE_TITLE = "1.6rem"
FONT_SIZE_LABEL = "0.66rem"
FONT_SIZE_VAL   = "1.55rem"
FONT_SIZE_SMALL = "0.78rem"

# ── CSS global (inyectar una sola vez en el dashboard maestro) ────────────────
GLOBAL_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* ── Base ── */
.stApp {{ background-color: {BG} !important; font-family: 'Inter', sans-serif; }}
#MainMenu, footer {{ visibility: hidden; }}
/* Ocultar header pero mantener visible el botón de expand del sidebar */
header {{ visibility: hidden; }}
[data-testid="stExpandSidebarButton"] {{
    visibility: visible !important;
    background: {CARD} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 0 8px 8px 0 !important;
    width: 32px !important;
    height: 32px !important;
    cursor: pointer !important;
}}
[data-testid="stExpandSidebarButton"]:hover {{
    border-color: {BLUE} !important;
    background: rgba(59,130,246,0.12) !important;
}}
[data-testid="stExpandSidebarButton"] svg {{
    fill: {TEXT_MUT} !important;
}}
.block-container {{ padding: 2rem 2.5rem 3rem !important; max-width: 1400px !important; }}

/* ── Header / navbar ── */
.pulse-header {{ display: flex; align-items: baseline; gap: 14px; margin-bottom: 6px; }}
.pulse-title {{
    font-size: {FONT_SIZE_TITLE}; font-weight: 700; color: {TEXT};
    letter-spacing: -0.4px; margin: 0;
}}
.pulse-badge {{
    background: rgba(59,130,246,0.15); color: {BLUE_LT};
    border: 1px solid rgba(59,130,246,0.3);
    border-radius: 99px; font-size: 0.62rem; font-weight: 700;
    letter-spacing: 1.2px; padding: 3px 10px; text-transform: uppercase;
}}
.pulse-ts {{ font-size: {FONT_SIZE_SMALL}; color: {TEXT_DARK}; margin-bottom: 24px; }}

/* ── Section labels ── */
.sec-label {{
    font-size: {FONT_SIZE_LABEL}; font-weight: 700; color: {TEXT_DIM};
    text-transform: uppercase; letter-spacing: 1.6px;
    margin: 20px 0 10px; display: flex; align-items: center; gap: 10px;
}}
.sec-label::after {{ content: ''; flex: 1; height: 1px; background: {CARD}; }}

/* ── Tile card ── */
.tile-card {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: 12px;
    padding: 18px 20px 16px;
    position: relative;
    overflow: hidden;
    transition: border-color 0.2s, transform 0.15s;
    height: 100%;
    min-height: 128px !important;
}}
.tile-card:hover {{ border-color: {BLUE}; transform: translateY(-2px); }}

/* Barra de acento superior */
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
    font-size: {FONT_SIZE_LABEL}; font-weight: 700; color: {TEXT_DIM};
    text-transform: uppercase; letter-spacing: 1.2px; margin-bottom: 10px;
}}
.tile-val {{
    font-size: {FONT_SIZE_VAL}; font-weight: 700; color: {TEXT};
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

/* Badge de colores */
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

/* ── Tabs de navegación ── */
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

/* ── Expanders ── */
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

/* ── Alerts ── */
div[data-testid="stAlert"] {{
    background: rgba(245,158,11,0.08) !important;
    border: 1px solid rgba(245,158,11,0.3) !important;
    border-radius: 10px !important;
    color: #FCD34D !important;
}}

/* ── Links ── */
a {{ color: {BLUE_LT} !important; }}
a:hover {{ color: #93C5FD !important; }}

/* ── Spinner ── */
.stSpinner > div {{ color: {BLUE} !important; }}

/* ── Column gaps y equal height ── */
div[data-testid="stHorizontalBlock"] {{ gap: 12px !important; }}
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

/* ── Market card (activos financieros) ── */
.market-card {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: 12px;
    padding: 14px 18px 12px;
    position: relative;
    overflow: hidden;
    transition: border-color 0.2s, transform 0.15s;
}}
.market-card:hover {{ border-color: {BLUE}; transform: translateY(-1px); }}
.market-card .mc-header {{
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: 6px;
}}
.market-card .mc-name {{
    font-size: 0.82rem; font-weight: 600; color: {TEXT};
}}
.market-card .mc-ticker {{
    font-size: 0.66rem; font-weight: 700; color: {TEXT_DIM};
    text-transform: uppercase; letter-spacing: 0.8px;
}}
.market-card .mc-price {{
    font-size: 1.3rem; font-weight: 700; color: {TEXT};
    font-variant-numeric: tabular-nums;
}}
.market-card .mc-change {{
    display: inline-block; padding: 2px 8px; border-radius: 99px;
    font-size: 0.68rem; font-weight: 700; margin-left: 8px;
}}
.mc-up   {{ background: rgba(16,185,129,0.15); color: #34D399; }}
.mc-down {{ background: rgba(239,68,68,0.15);  color: #FCA5A5; }}
.mc-flat {{ background: rgba(148,163,184,0.15); color: {TEXT_MUT}; }}
.market-card .mc-currency {{
    font-size: 0.62rem; color: {TEXT_DIM}; margin-top: 4px;
}}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {{
    background: {CARD} !important;
    border-right: 1px solid {BORDER} !important;
}}
section[data-testid="stSidebar"] * {{ color: {TEXT_MUT} !important; }}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {{ color: {TEXT} !important; }}
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stSlider label,
section[data-testid="stSidebar"] .stToggle label {{ color: {TEXT_MUT} !important; font-size: 0.78rem !important; }}

/* ── Footer personalizado ── */
.pulse-footer {{
    margin-top: 48px;
    padding: 14px 0 0;
    border-top: 1px solid {BORDER};
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.68rem;
    color: {TEXT_DIM};
}}
.status-dot {{
    display: inline-block;
    width: 7px; height: 7px;
    border-radius: 50%;
    margin-right: 5px;
}}
.dot-ok     {{ background: {GREEN}; }}
.dot-warn   {{ background: {AMBER}; }}
.dot-error  {{ background: {RED}; }}
</style>
"""
