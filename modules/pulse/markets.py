# modules/pulse/markets.py
import yfinance as yf
import pandas as pd

from core import cache
from core.config import (
    RAW_DIR, OFFLINE_MODE,
    CACHE_TTL_MARKETS, CACHE_TTL_HISTORY,
)

# ── Universo de activos PulseArg ──────────────────────────────────────
ASSETS = {
    "indices": {
        "Merval":        "^MERV",
        "Merval USD":    "M.BA",
        "BYMA General":  "^BYMA",
    },
    "energia": {
        "YPF":           "YPF",
        "Pampa Energía": "PAM",
        "Vista Energy":  "VIST",
        "Edenor":        "EDN",
        "TGS":           "TGSU2.BA",
        "Tecpetrol":     "TECO2.BA",
    },
    "finanzas": {
        "Galicia":        "GGAL",
        "Macro":          "BMA",
        "BBVA Arg":       "BBAR.BA",
        "Supervielle":    "SUPV",
        "Loma Negra":     "LOMA",
        "Soc. Comercial": "COME.BA",
    },
    "tech_consumer": {
        "MercadoLibre":  "MELI",
        "Globant":       "GLOB",
        "Despegar":      "DESP",
        "Telecom Arg":   "TEO",
        "Arcos Dorados": "ARCO",
        "Cresud":        "CRESY",
    },
    "agro": {
        "Adecoagro": "AGRO",
        "Soja CME":  "ZS=F",
        "Maíz CME":  "ZC=F",
    },
}

# ── Snapshot actual ───────────────────────────────────────────────────

def fetch_snapshot(*, cache_dir=None, offline=None) -> pd.DataFrame:
    """
    Precio, variación % diaria y volumen de todos los activos.
    Serializa como lista de registros para persistir en caché JSON.
    """
    _dir     = cache_dir if cache_dir is not None else RAW_DIR
    _offline = offline   if offline   is not None else OFFLINE_MODE

    raw, fresh = cache.read("snapshot", _dir)
    if fresh:
        return pd.DataFrame(raw)

    if _offline:
        stale, _ = cache.read("snapshot", _dir, allow_stale=True)
        return pd.DataFrame(stale) if stale else pd.DataFrame()

    rows = []
    for sector, tickers in ASSETS.items():
        for nombre, ticker in tickers.items():
            try:
                info = yf.Ticker(ticker).fast_info
                rows.append({
                    "sector":  sector,
                    "nombre":  nombre,
                    "ticker":  ticker,
                    "precio":  round(info.last_price, 2),
                    "var_pct": round(
                        (info.last_price / info.previous_close - 1) * 100, 2
                    ),
                    "volumen": info.three_month_average_volume,
                    "moneda":  info.currency,
                })
            except Exception as e:
                rows.append({
                    "sector":  sector, "nombre": nombre,
                    "ticker":  ticker, "precio": None,
                    "var_pct": None,   "error":  str(e),
                })

    if rows:
        cache.write("snapshot", rows, CACHE_TTL_MARKETS, _dir)
    else:
        stale, _ = cache.read("snapshot", _dir, allow_stale=True)
        return pd.DataFrame(stale) if stale else pd.DataFrame()

    return pd.DataFrame(rows)


# ── Helpers de DataFrame ──────────────────────────────────────────────

def _flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    """yfinance ≥0.2.31 devuelve MultiIndex — lo aplana a columnas simples."""
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df


def _df_to_records(df: pd.DataFrame) -> list[dict]:
    """Serializa un DataFrame con índice de fechas a lista de dicts."""
    records = df.reset_index().to_dict(orient="records")
    for r in records:
        for k, v in r.items():
            if hasattr(v, "isoformat"):
                r[k] = v.isoformat()
    return records


def _records_to_df(records: list[dict]) -> pd.DataFrame:
    """Reconstruye un DataFrame de serie histórica desde lista de dicts."""
    if not records:
        return pd.DataFrame()
    df       = pd.DataFrame(records)
    date_col = next((c for c in df.columns if c.lower() in ("date", "datetime")), df.columns[0])
    parsed   = pd.to_datetime(df[date_col])
    if parsed.dt.tz is not None:
        parsed = parsed.dt.tz_convert(None)
    df[date_col]   = parsed
    df             = df.set_index(date_col)
    df.index.name  = "Date"
    return df


# ── Serie histórica ───────────────────────────────────────────────────

def fetch_history(ticker: str, period: str = "3mo",
                  *, cache_dir=None, offline=None) -> pd.DataFrame:
    """Serie de cierre para un ticker. period: 1d 5d 1mo 3mo 6mo 1y 2y 5y."""
    _dir     = cache_dir if cache_dir is not None else RAW_DIR
    _offline = offline   if offline   is not None else OFFLINE_MODE
    key      = f"history_{ticker}_{period}"

    raw, fresh = cache.read(key, _dir)
    if fresh:
        return _records_to_df(raw)

    if _offline:
        stale, _ = cache.read(key, _dir, allow_stale=True)
        return _records_to_df(stale) if stale else pd.DataFrame()

    df = yf.download(ticker, period=period, progress=False)
    df = _flatten_columns(df)
    df.index = pd.to_datetime(df.index)

    if not df.empty:
        cache.write(key, _df_to_records(df), CACHE_TTL_HISTORY, _dir)
    else:
        stale, _ = cache.read(key, _dir, allow_stale=True)
        return _records_to_df(stale) if stale else pd.DataFrame()

    return df


# ── Correlación entre activos ─────────────────────────────────────────

def fetch_correlation(tickers: list[str], period: str = "3mo",
                      *, cache_dir=None, offline=None) -> pd.DataFrame:
    """Matriz de correlación de retornos diarios."""
    _dir     = cache_dir if cache_dir is not None else RAW_DIR
    _offline = offline   if offline   is not None else OFFLINE_MODE
    key      = f"corr_{'_'.join(tickers)}_{period}"

    raw, fresh = cache.read(key, _dir)
    if fresh:
        return pd.DataFrame(raw) if raw else pd.DataFrame()

    if _offline:
        stale, _ = cache.read(key, _dir, allow_stale=True)
        return pd.DataFrame(stale) if stale else pd.DataFrame()

    closes = {}
    for ticker in tickers:
        try:
            df = yf.download(ticker, period=period, progress=False)
            df = _flatten_columns(df)
            if not df.empty and "Close" in df.columns:
                series = df["Close"].squeeze()
                if isinstance(series, pd.Series) and len(series) > 1:
                    closes[ticker] = series
        except Exception:
            continue

    if len(closes) < 2:
        stale, _ = cache.read(key, _dir, allow_stale=True)
        return pd.DataFrame(stale) if stale else pd.DataFrame()

    combined = pd.DataFrame(closes)
    corr_df  = combined.pct_change().dropna().corr().round(3)

    cache.write(key, corr_df.to_dict(orient="index"), CACHE_TTL_HISTORY, _dir)
    return corr_df
