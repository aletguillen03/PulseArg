from pathlib import Path
from os import environ

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR  = DATA_DIR / "raw"

RAW_DIR.mkdir(parents=True, exist_ok=True)

# ── Modo offline ──────────────────────────────────────────────────────
# True → nunca hace requests HTTP; sirve exclusivamente desde caché.
OFFLINE_MODE = environ.get("OFFLINE_MODE", "false").lower() == "true"

# ── TTL de caché (segundos) ───────────────────────────────────────────
CACHE_TTL_DOLAR   = int(environ.get("CACHE_TTL_DOLAR",   "300"))   # 5 min
CACHE_TTL_BCRA    = int(environ.get("CACHE_TTL_BCRA",    "3600"))  # 1 hora
CACHE_TTL_NEWS    = int(environ.get("CACHE_TTL_NEWS",    "1800"))  # 30 min
CACHE_TTL_MARKETS = int(environ.get("CACHE_TTL_MARKETS", "300"))   # 5 min
CACHE_TTL_HISTORY = int(environ.get("CACHE_TTL_HISTORY", "3600"))  # 1 hora

# ── SSL ───────────────────────────────────────────────────────────────
# El certificado de BCRA es inestable; desactivado por defecto.
# Setear BCRA_VERIFY_SSL=true solo en entornos donde el cert sea válido.
BCRA_VERIFY_SSL = environ.get("BCRA_VERIFY_SSL", "false").lower() == "true"

# ── URLs de APIs (sobreescribibles para tests o proxies) ──────────────
BLUELYTICS_URL = environ.get("BLUELYTICS_URL", "https://api.bluelytics.com.ar/v2/latest")
DOLARAPI_URL   = environ.get("DOLARAPI_URL",   "https://dolarapi.com/v1/dolares")
BCRA_URL_V4    = environ.get("BCRA_URL_V4",    "https://api.bcra.gob.ar/estadisticas/v4.0/monetarias")
BCRA_URL_V2    = environ.get("BCRA_URL_V2",    "https://api.bcra.gob.ar/estadisticas/v2.0/datosvariable")
