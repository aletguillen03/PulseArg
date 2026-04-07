# modules/pulse/constants.py
# ── Constantes específicas del módulo ArgentinaPulse ────────────────────────
# Extiende la paleta global definida en modules/constants.py.

import sys
from pathlib import Path

# Asegura que el root del proyecto esté en sys.path
_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from modules.constants import (   # noqa: F401 — reexportar para comodidad
    BG, CARD, BORDER,
    BLUE, BLUE_LT, SKY, TEAL, GREEN, AMBER, RED, PURPLE, ROSE,
    TEXT, TEXT_MUT, TEXT_DIM, TEXT_DARK,
)

# ── Etiquetas de sectores (mapa sector_id → (label, accent_class)) ────────────
SECTOR_LABELS: dict[str, tuple[str, str]] = {
    "indices":       ("📈 Índices",           "accent-rose"),
    "energia":       ("⚡ Energía",            "accent-amber"),
    "finanzas":      ("🏦 Finanzas",           "accent-teal"),
    "tech_consumer": ("💻 Tech & Consumer",    "accent-purple"),
    "agro":          ("🌾 Agro / Commodities", "accent-green"),
}

# ── Mapa de acento para tiles ────────────────────────────────────────────────
TILE_ACCENTS = {
    "blue":   ("accent-blue",   "b-blue"),
    "teal":   ("accent-teal",   "b-teal"),
    "sky":    ("accent-sky",    "b-sky"),
    "purple": ("accent-purple", "b-purple"),
    "amber":  ("accent-amber",  "b-amber"),
    "rose":   ("accent-rose",   "b-rose"),
    "green":  ("accent-green",  "b-green"),
    "red":    ("accent-red",    "b-red"),
}

# ── Thresholds de brecha cambiaria ────────────────────────────────────────────
BRECHA_BAJA       = 20   # % — brecha verde
BRECHA_MODERADA   = 50   # % — brecha amarilla (>= moderada y < alta)
# >= BRECHA_MODERADA → "Alta" (rojo)
