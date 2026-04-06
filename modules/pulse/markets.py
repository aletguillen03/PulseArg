# modules/pulse/markets.py
import yfinance as yf
import pandas as pd
from datetime import datetime

# ── Universo de activos PulseArg ────────────────────────────────────
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
        "Galicia":       "GGAL",
        "Macro":         "BMA",
        "BBVA Arg":      "BBAR.BA",
        "Supervielle":   "SUPV",
        "Loma Negra":    "LOMA",
        "Soc. Comercial":"COME.BA",
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
        "Adecoagro":     "AGRO",
        "Soja CME":      "ZS=F",
        "Maíz CME":      "ZC=F",
    },
}

# ── Snapshot actual ─────────────────────────────────────────────────
def fetch_snapshot() -> pd.DataFrame:
    """
    Retorna un DataFrame con precio, variación % diaria y volumen
    para todos los activos del universo.
    """
    rows = []
    for sector, tickers in ASSETS.items():
        for nombre, ticker in tickers.items():
            try:
                t    = yf.Ticker(ticker)
                info = t.fast_info          # más rápido que .info completo
                rows.append({
                    "sector":   sector,
                    "nombre":   nombre,
                    "ticker":   ticker,
                    "precio":   round(info.last_price, 2),
                    "var_pct":  round(
                        (info.last_price / info.previous_close - 1) * 100, 2
                    ),
                    "volumen":  info.three_month_average_volume,
                    "moneda":   info.currency,
                })
            except Exception as e:
                rows.append({
                    "sector": sector, "nombre": nombre,
                    "ticker": ticker, "precio": None,
                    "var_pct": None,  "error": str(e),
                })
    return pd.DataFrame(rows)

# ── Helper: aplanar columnas MultiIndex de yfinance ≥0.2.31 ───────
def _flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    yfinance ≥0.2.31 devuelve MultiIndex ('Close','TICKER').
    Esta función lo aplana a columnas simples ('Close','Open',...).
    """
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

# ── Serie histórica para un ticker ─────────────────────────────────
def fetch_history(ticker: str, period: str = "3mo") -> pd.DataFrame:
    """
    period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y
    """
    df = yf.download(ticker, period=period, progress=False)
    df = _flatten_columns(df)
    df.index = pd.to_datetime(df.index)
    return df

# ── Correlación entre activos ───────────────────────────────────────
def fetch_correlation(tickers: list[str], period: str = "3mo") -> pd.DataFrame:
    """
    Matriz de correlación de retornos diarios.
    Útil para ver si el dólar blue se mueve con YPF, por ejemplo.
    """
    closes = {}
    for ticker in tickers:
        try:
            df = yf.download(ticker, period=period, progress=False)
            df = _flatten_columns(df)
            if not df.empty and "Close" in df.columns:
                series = df["Close"].squeeze()   # DataFrame → Series si queda 1 col
                if isinstance(series, pd.Series) and len(series) > 1:
                    closes[ticker] = series
        except Exception:
            continue

    if len(closes) < 2:
        return pd.DataFrame()

    combined = pd.DataFrame(closes)
    returns  = combined.pct_change().dropna()
    return returns.corr().round(3)
