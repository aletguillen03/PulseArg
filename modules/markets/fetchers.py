# modules/markets/fetchers.py
# ── Fetchers del módulo Markets ───────────────────────────────────────────────
# Flujo de datos: JSON cache (fresco) → DuckDB → yfinance → stale fallback

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import yfinance as yf
import pandas as pd

from core import cache
from core.config import RAW_DIR, OFFLINE_MODE, CACHE_TTL_MARKETS, CACHE_TTL_HISTORY
from core.duck import upsert_history, read_history, has_fresh_data

try:
    from .constants import ADR_TICKERS, COMMODITY_TICKERS, MERVAL_COMPONENTS, PERIODO_DIAS
except ImportError:
    from modules.markets.constants import (
        ADR_TICKERS, COMMODITY_TICKERS, MERVAL_COMPONENTS, PERIODO_DIAS,
    )


# ── Helpers de DataFrame ──────────────────────────────────────────────────────

def _flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    """yfinance ≥0.2.31 devuelve MultiIndex — lo aplana a columnas simples."""
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df


def _df_to_records(df: pd.DataFrame) -> list[dict]:
    """Serializa DataFrame con índice de fechas a lista de dicts JSON-friendly."""
    records = df.reset_index().to_dict(orient="records")
    for r in records:
        for k, v in r.items():
            if hasattr(v, "isoformat"):
                r[k] = v.isoformat()
    return records


def _records_to_df(records: list[dict]) -> pd.DataFrame:
    """Reconstruye DataFrame de serie histórica desde lista de dicts."""
    if not records:
        return pd.DataFrame()
    df       = pd.DataFrame(records)
    date_col = next(
        (c for c in df.columns if c.lower() in ("date", "datetime")), df.columns[0]
    )
    parsed = pd.to_datetime(df[date_col])
    if parsed.dt.tz is not None:
        parsed = parsed.dt.tz_convert(None)
    df[date_col]  = parsed
    df            = df.set_index(date_col)
    df.index.name = "Date"
    return df


# ── Merval ────────────────────────────────────────────────────────────────────

def fetch_merval(*, cache_dir=None, offline=None) -> dict:
    """
    Retorna snapshot del índice Merval (^MERV).
    Claves: precio, var_pct, max_52w, min_52w, moneda.
    """
    _dir     = cache_dir if cache_dir is not None else RAW_DIR
    _offline = offline   if offline   is not None else OFFLINE_MODE

    raw, fresh = cache.read("mkt_merval", _dir)
    if fresh:
        return raw or {}

    if _offline:
        stale, _ = cache.read("mkt_merval", _dir, allow_stale=True)
        return stale or {}

    try:
        info   = yf.Ticker("^MERV").fast_info
        result = {
            "precio":  round(float(info.last_price), 0),
            "var_pct": round((float(info.last_price) / float(info.previous_close) - 1) * 100, 2),
            "max_52w": round(float(info.year_high), 0) if info.year_high else None,
            "min_52w": round(float(info.year_low),  0) if info.year_low  else None,
            "moneda":  info.currency or "ARS",
        }
    except Exception:
        stale, _ = cache.read("mkt_merval", _dir, allow_stale=True)
        return stale or {}

    cache.write("mkt_merval", result, CACHE_TTL_MARKETS, _dir)
    return result


# ── ADRs ──────────────────────────────────────────────────────────────────────

def fetch_adrs(*, cache_dir=None, offline=None) -> pd.DataFrame:
    """
    Snapshot de todos los ADRs argentinos en NYSE/NASDAQ.
    Columnas: ticker, nombre, sector, exchange, emoji, precio, var_pct, volumen, moneda.
    """
    _dir     = cache_dir if cache_dir is not None else RAW_DIR
    _offline = offline   if offline   is not None else OFFLINE_MODE

    raw, fresh = cache.read("mkt_adrs", _dir)
    if fresh:
        return pd.DataFrame(raw) if raw else pd.DataFrame()

    if _offline:
        stale, _ = cache.read("mkt_adrs", _dir, allow_stale=True)
        return pd.DataFrame(stale) if stale else pd.DataFrame()

    rows = []
    for ticker, meta in ADR_TICKERS.items():
        try:
            info = yf.Ticker(ticker).fast_info
            rows.append({
                "ticker":   ticker,
                "nombre":   meta["nombre"],
                "sector":   meta["sector"],
                "exchange": meta["exchange"],
                "emoji":    meta.get("emoji", ""),
                "precio":   round(float(info.last_price), 2),
                "var_pct":  round(
                    (float(info.last_price) / float(info.previous_close) - 1) * 100, 2
                ),
                "volumen":  (
                    int(info.three_month_average_volume)
                    if info.three_month_average_volume else None
                ),
                "moneda":   info.currency or "USD",
            })
        except Exception:
            rows.append({
                "ticker":   ticker,
                "nombre":   meta["nombre"],
                "sector":   meta["sector"],
                "exchange": meta["exchange"],
                "emoji":    meta.get("emoji", ""),
                "precio":   None,
                "var_pct":  None,
                "volumen":  None,
                "moneda":   "USD",
            })

    if rows:
        cache.write("mkt_adrs", rows, CACHE_TTL_MARKETS, _dir)
    else:
        stale, _ = cache.read("mkt_adrs", _dir, allow_stale=True)
        return pd.DataFrame(stale) if stale else pd.DataFrame()

    return pd.DataFrame(rows)


# ── Commodities ───────────────────────────────────────────────────────────────

def fetch_commodities(*, cache_dir=None, offline=None) -> pd.DataFrame:
    """
    Snapshot de soja (ZS=F), maíz (ZC=F), trigo (ZW=F) y petróleo WTI (CL=F).
    Columnas: ticker, nombre, unidad, emoji, accent, cls, precio, var_pct, moneda.
    """
    _dir     = cache_dir if cache_dir is not None else RAW_DIR
    _offline = offline   if offline   is not None else OFFLINE_MODE

    raw, fresh = cache.read("mkt_commodities", _dir)
    if fresh:
        return pd.DataFrame(raw) if raw else pd.DataFrame()

    if _offline:
        stale, _ = cache.read("mkt_commodities", _dir, allow_stale=True)
        return pd.DataFrame(stale) if stale else pd.DataFrame()

    rows = []
    for ticker, meta in COMMODITY_TICKERS.items():
        try:
            info = yf.Ticker(ticker).fast_info
            rows.append({
                "ticker":  ticker,
                "nombre":  meta["nombre"],
                "unidad":  meta["unidad"],
                "emoji":   meta.get("emoji", ""),
                "accent":  meta.get("accent", "accent-green"),
                "cls":     meta.get("cls", ""),
                "precio":  round(float(info.last_price), 2),
                "var_pct": round(
                    (float(info.last_price) / float(info.previous_close) - 1) * 100, 2
                ),
                "moneda":  info.currency or "USD",
            })
        except Exception:
            rows.append({
                "ticker":  ticker,
                "nombre":  meta["nombre"],
                "unidad":  meta["unidad"],
                "emoji":   meta.get("emoji", ""),
                "accent":  meta.get("accent", "accent-green"),
                "cls":     meta.get("cls", ""),
                "precio":  None,
                "var_pct": None,
                "moneda":  "USD",
            })

    if rows:
        cache.write("mkt_commodities", rows, CACHE_TTL_MARKETS, _dir)
    else:
        stale, _ = cache.read("mkt_commodities", _dir, allow_stale=True)
        return pd.DataFrame(stale) if stale else pd.DataFrame()

    return pd.DataFrame(rows)


# ── Histórico con DuckDB ──────────────────────────────────────────────────────

def fetch_history_ddb(ticker: str, period: str = "3mo",
                      *, cache_dir=None, offline=None) -> pd.DataFrame:
    """
    Obtiene serie histórica de precios con persistencia DuckDB.

    Flujo:
      1. DuckDB fresco (≤1 día) → retorna inmediatamente
      2. JSON cache fresco → retorna
      3. Offline → DuckDB stale o JSON stale
      4. yfinance → persiste en DuckDB + JSON cache → retorna
      5. Fallback: DuckDB stale, JSON stale, DataFrame vacío
    """
    _dir     = cache_dir if cache_dir is not None else RAW_DIR
    _offline = offline   if offline   is not None else OFFLINE_MODE
    days     = PERIODO_DIAS.get(period, 95)
    cache_key = f"mkt_hist_{ticker}_{period}"

    # 1. DuckDB fresco
    if has_fresh_data(ticker, max_stale_days=1):
        df = read_history(ticker, days=days)
        if not df.empty:
            return df

    # 2. JSON cache fresco
    raw, fresh = cache.read(cache_key, _dir)
    if fresh:
        return _records_to_df(raw)

    # 3. Modo offline
    if _offline:
        df_stale = read_history(ticker, days=days)
        if not df_stale.empty:
            return df_stale
        stale, _ = cache.read(cache_key, _dir, allow_stale=True)
        return _records_to_df(stale) if stale else pd.DataFrame()

    # 4. yfinance
    df = pd.DataFrame()
    try:
        df = yf.download(ticker, period=period, progress=False)
        df = _flatten_columns(df)
        df.index = pd.to_datetime(df.index)
        if df.index.tz is not None:
            df.index = df.index.tz_convert(None)
    except Exception:
        pass

    if not df.empty:
        upsert_history(ticker, df)
        cache.write(cache_key, _df_to_records(df), CACHE_TTL_HISTORY, _dir)
        return df

    # 5. Stale fallbacks
    df_stale = read_history(ticker, days=days)
    if not df_stale.empty:
        return df_stale
    stale, _ = cache.read(cache_key, _dir, allow_stale=True)
    return _records_to_df(stale) if stale else pd.DataFrame()


# ── Sparklines batch ─────────────────────────────────────────────────────────

def fetch_sparklines(tickers: list[str], period: str = "1mo",
                     *, cache_dir=None, offline=None) -> dict[str, list[float]]:
    """
    Retorna series de cierre para sparklines: {ticker: [precio, ...]}
    Usa DuckDB para lecturas rápidas si los datos ya están cacheados;
    si no, fetcha de yfinance y persiste.
    """
    _dir      = cache_dir if cache_dir is not None else RAW_DIR
    _offline  = offline   if offline   is not None else OFFLINE_MODE
    days      = PERIODO_DIAS.get(period, 35)

    # Intentar leer de DuckDB primero (rápido, sin red)
    result: dict[str, list[float]] = {}
    missing: list[str] = []

    for ticker in tickers:
        df = read_history(ticker, days=days)
        if not df.empty and "Close" in df.columns:
            vals = df["Close"].dropna().tolist()
            if len(vals) >= 2:
                result[ticker] = [round(v, 2) for v in vals]
                continue
        missing.append(ticker)

    if not missing or _offline:
        return result

    # Fetch de yfinance para los que faltan
    for ticker in missing:
        try:
            df = yf.download(ticker, period=period, progress=False)
            df = _flatten_columns(df)
            df.index = pd.to_datetime(df.index)
            if df.index.tz is not None:
                df.index = df.index.tz_convert(None)
            if not df.empty and "Close" in df.columns:
                upsert_history(ticker, df)
                vals = df["Close"].dropna().tolist()
                if vals:
                    result[ticker] = [round(v, 2) for v in vals]
        except Exception:
            pass

    return result
