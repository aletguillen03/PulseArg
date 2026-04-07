# core/duck.py
# ── DuckDB — almacenamiento persistente de históricos de mercado ──────────────
# Tabla principal: ohlcv (ticker, date, open, high, low, close, volume)
# Tabla alertas:   price_alerts (ticker, threshold, direction)

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import duckdb
import pandas as pd
from datetime import date, timedelta

from core.config import DATA_DIR

DB_PATH = DATA_DIR / "markets.duckdb"


# ── Conexión ──────────────────────────────────────────────────────────────────

def _connect() -> duckdb.DuckDBPyConnection:
    """Abre una conexión a la base de datos DuckDB."""
    return duckdb.connect(str(DB_PATH))


# ── Inicialización ────────────────────────────────────────────────────────────

def init_db() -> None:
    """Crea las tablas si no existen. Idempotente."""
    con = _connect()
    try:
        con.execute("""
            CREATE TABLE IF NOT EXISTS ohlcv (
                ticker  VARCHAR NOT NULL,
                date    DATE    NOT NULL,
                open    DOUBLE,
                high    DOUBLE,
                low     DOUBLE,
                close   DOUBLE,
                volume  BIGINT,
                PRIMARY KEY (ticker, date)
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS price_alerts (
                ticker      VARCHAR NOT NULL,
                threshold   DOUBLE  NOT NULL,
                direction   VARCHAR NOT NULL,
                PRIMARY KEY (ticker, direction)
            )
        """)
    finally:
        con.close()


# ── Escritura de históricos ───────────────────────────────────────────────────

def upsert_history(ticker: str, df: pd.DataFrame) -> None:
    """
    Inserta o reemplaza datos OHLCV para un ticker.
    Solo actualiza el rango de fechas presente en df (preserva datos anteriores).
    Silencioso en caso de error para no bloquear el flujo principal.
    """
    if df is None or df.empty:
        return
    try:
        init_db()

        tmp = df.copy().reset_index()
        # Normalizar nombres de columnas a minúsculas
        tmp.columns = [str(c).lower() for c in tmp.columns]
        date_col = next(
            (c for c in tmp.columns if c in ("date", "datetime")), tmp.columns[0]
        )
        tmp = tmp.rename(columns={date_col: "date"})
        tmp["ticker"] = ticker
        tmp["date"]   = pd.to_datetime(tmp["date"]).dt.normalize().dt.date

        # Columnas disponibles en orden esperado por la tabla
        want = [c for c in ["ticker", "date", "open", "high", "low", "close", "volume"]
                if c in tmp.columns]
        tmp  = tmp[want]

        if tmp.empty:
            return

        min_date = tmp["date"].min()
        max_date = tmp["date"].max()

        con = _connect()
        try:
            # Borrar rango existente para hacer upsert limpio
            con.execute(
                "DELETE FROM ohlcv WHERE ticker = ? AND date >= ? AND date <= ?",
                [ticker, min_date, max_date],
            )
            con.register("_upsert_tmp", tmp)
            cols_sql = ", ".join(want)
            con.execute(
                f"INSERT INTO ohlcv ({cols_sql}) SELECT {cols_sql} FROM _upsert_tmp"
            )
            con.unregister("_upsert_tmp")
        finally:
            con.close()

    except Exception:
        pass  # silencioso — no bloquear el flujo principal


# ── Lectura de históricos ─────────────────────────────────────────────────────

def read_history(ticker: str, days: int = 90) -> pd.DataFrame:
    """
    Lee historial OHLCV desde DuckDB.
    Devuelve DataFrame con índice 'Date' (sin tz) o DataFrame vacío.
    Columnas capitalizadas: Open, High, Low, Close, Volume.
    """
    try:
        init_db()
        cutoff = date.today() - timedelta(days=days)
        con = _connect()
        try:
            df = con.execute("""
                SELECT date, open, high, low, close, volume
                FROM ohlcv
                WHERE ticker = ? AND date >= ?
                ORDER BY date ASC
            """, [ticker, cutoff]).df()
        finally:
            con.close()

        if df.empty:
            return pd.DataFrame()

        df["date"]    = pd.to_datetime(df["date"])
        df            = df.set_index("date")
        df.index.name = "Date"
        # Capitalizar columnas para compatibilidad con yfinance
        df.columns = [c.capitalize() for c in df.columns]
        return df

    except Exception:
        return pd.DataFrame()


def has_fresh_data(ticker: str, max_stale_days: int = 1) -> bool:
    """
    True si DuckDB contiene datos del ticker actualizados
    hace menos de max_stale_days días.
    """
    try:
        init_db()
        con = _connect()
        try:
            row = con.execute(
                "SELECT MAX(date) FROM ohlcv WHERE ticker = ?", [ticker]
            ).fetchone()
        finally:
            con.close()
        if not row or row[0] is None:
            return False
        return row[0] >= date.today() - timedelta(days=max_stale_days)
    except Exception:
        return False


# ── Alertas de precio ─────────────────────────────────────────────────────────

def get_alerts() -> list[dict]:
    """Retorna todas las alertas guardadas: [{ticker, threshold, direction}, ...]."""
    try:
        init_db()
        con = _connect()
        try:
            rows = con.execute(
                "SELECT ticker, threshold, direction FROM price_alerts ORDER BY ticker"
            ).fetchall()
        finally:
            con.close()
        return [{"ticker": r[0], "threshold": r[1], "direction": r[2]} for r in rows]
    except Exception:
        return []


def set_alert(ticker: str, threshold: float, direction: str) -> None:
    """Agrega o reemplaza una alerta de precio. direction: 'above' | 'below'."""
    try:
        init_db()
        con = _connect()
        try:
            con.execute(
                "DELETE FROM price_alerts WHERE ticker = ? AND direction = ?",
                [ticker, direction],
            )
            con.execute(
                "INSERT INTO price_alerts (ticker, threshold, direction) VALUES (?, ?, ?)",
                [ticker, threshold, direction],
            )
        finally:
            con.close()
    except Exception:
        pass


def delete_alert(ticker: str, direction: str) -> None:
    """Elimina una alerta de precio."""
    try:
        init_db()
        con = _connect()
        try:
            con.execute(
                "DELETE FROM price_alerts WHERE ticker = ? AND direction = ?",
                [ticker, direction],
            )
        finally:
            con.close()
    except Exception:
        pass
