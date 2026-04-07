"""
tests/test_markets_offline.py — Tests en frío del módulo de mercados.

Todos los tests corren en OFFLINE_MODE=True con datos de fixtures.
Ninguno invoca yfinance ni hace requests HTTP.
"""
import pytest
import pandas as pd
from pathlib import Path
from core import cache
from modules.pulse.markets import (
    fetch_snapshot,
    fetch_history,
    fetch_correlation,
    _records_to_df,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _load_fixture(name: str, tmp_path: Path) -> None:
    src = FIXTURES / name
    (tmp_path / name).write_bytes(src.read_bytes())


# ── fetch_snapshot ────────────────────────────────────────────────────

class TestFetchSnapshot:
    def test_retorna_dataframe(self, tmp_path):
        _load_fixture("snapshot.json", tmp_path)
        df = fetch_snapshot(cache_dir=tmp_path, offline=True)
        assert isinstance(df, pd.DataFrame)
        assert not df.empty

    def test_columnas_requeridas(self, tmp_path):
        _load_fixture("snapshot.json", tmp_path)
        df = fetch_snapshot(cache_dir=tmp_path, offline=True)
        for col in ("sector", "nombre", "ticker", "precio", "var_pct"):
            assert col in df.columns, f"Columna faltante: {col}"

    def test_todos_los_sectores_presentes(self, tmp_path):
        _load_fixture("snapshot.json", tmp_path)
        df = fetch_snapshot(cache_dir=tmp_path, offline=True)
        sectores = set(df["sector"].unique())
        esperados = {"indices", "energia", "finanzas", "tech_consumer", "agro"}
        assert esperados.issubset(sectores)

    def test_precios_son_numericos(self, tmp_path):
        _load_fixture("snapshot.json", tmp_path)
        df = fetch_snapshot(cache_dir=tmp_path, offline=True)
        df_validos = df.dropna(subset=["precio"])
        assert (df_validos["precio"] > 0).all()

    def test_var_pct_calculable(self, tmp_path):
        _load_fixture("snapshot.json", tmp_path)
        df = fetch_snapshot(cache_dir=tmp_path, offline=True)
        df_validos = df.dropna(subset=["var_pct"])
        assert df_validos["var_pct"].between(-100, 100).all()

    def test_top_movers_identificables(self, tmp_path):
        _load_fixture("snapshot.json", tmp_path)
        df = fetch_snapshot(cache_dir=tmp_path, offline=True)
        df_m = df.dropna(subset=["var_pct"])
        top_up   = df_m.nlargest(1, "var_pct").iloc[0]
        top_down = df_m.nsmallest(1, "var_pct").iloc[0]
        assert top_up["var_pct"]   >  0
        assert top_down["var_pct"] <  0

    def test_sin_cache_retorna_dataframe_vacio(self, tmp_path):
        df = fetch_snapshot(cache_dir=tmp_path, offline=True)
        assert isinstance(df, pd.DataFrame)
        assert df.empty


# ── fetch_history ─────────────────────────────────────────────────────

class TestFetchHistory:
    def test_retorna_dataframe_con_indice_fecha(self, tmp_path):
        _load_fixture("history__MERV_3mo.json", tmp_path)
        df = fetch_history("^MERV", period="3mo", cache_dir=tmp_path, offline=True)
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert df.index.name == "Date"
        assert pd.api.types.is_datetime64_any_dtype(df.index)

    def test_columna_close_presente(self, tmp_path):
        _load_fixture("history__MERV_3mo.json", tmp_path)
        df = fetch_history("^MERV", period="3mo", cache_dir=tmp_path, offline=True)
        assert "Close" in df.columns

    def test_datos_ordenados_por_fecha(self, tmp_path):
        _load_fixture("history__MERV_3mo.json", tmp_path)
        df = fetch_history("^MERV", period="3mo", cache_dir=tmp_path, offline=True)
        assert df.index.is_monotonic_increasing

    def test_retorno_indexado_calculable(self, tmp_path):
        """Verifica que se puede normalizar a base 100 (lógica del dashboard)."""
        _load_fixture("history__MERV_3mo.json", tmp_path)
        df    = fetch_history("^MERV", period="3mo", cache_dir=tmp_path, offline=True)
        close = df["Close"]
        norm  = (close / close.iloc[0]) * 100
        assert norm.iloc[0] == pytest.approx(100.0)
        assert (norm > 0).all()

    def test_sin_cache_retorna_dataframe_vacio(self, tmp_path):
        df = fetch_history("INEXISTENTE", period="3mo",
                           cache_dir=tmp_path, offline=True)
        assert isinstance(df, pd.DataFrame)
        assert df.empty


# ── fetch_correlation ─────────────────────────────────────────────────

class TestFetchCorrelation:
    def test_sin_cache_retorna_dataframe_vacio(self, tmp_path):
        tickers = ["YPF", "MELI", "GGAL"]
        df = fetch_correlation(tickers, period="3mo",
                               cache_dir=tmp_path, offline=True)
        assert isinstance(df, pd.DataFrame)
        assert df.empty

    def test_con_cache_retorna_matriz(self, tmp_path):
        tickers = ["YPF", "MELI"]
        corr_data = {
            "YPF":  {"YPF": 1.0, "MELI": 0.45},
            "MELI": {"YPF": 0.45, "MELI": 1.0},
        }
        key = f"corr_{'_'.join(tickers)}_3mo"
        cache.write(key, corr_data, ttl=3600, cache_dir=tmp_path)
        df = fetch_correlation(tickers, period="3mo",
                               cache_dir=tmp_path, offline=True)
        assert not df.empty
        assert "YPF"  in df.columns
        assert "MELI" in df.columns


# ── _records_to_df (helper interno) ──────────────────────────────────

class TestRecordsToDf:
    def test_convierte_lista_de_dicts(self):
        records = [
            {"date": "2026-01-01T00:00:00", "Close": 100.0, "Volume": 1000},
            {"date": "2026-01-02T00:00:00", "Close": 102.0, "Volume": 1100},
        ]
        df = _records_to_df(records)
        assert not df.empty
        assert df.index.name == "Date"
        assert len(df) == 2
        assert df["Close"].iloc[0] == 100.0

    def test_lista_vacia_retorna_vacio(self):
        df = _records_to_df([])
        assert isinstance(df, pd.DataFrame)
        assert df.empty

    def test_timestamps_con_zona_horaria(self):
        records = [
            {"date": "2026-01-01T00:00:00+00:00", "Close": 50.0},
            {"date": "2026-01-02T00:00:00+00:00", "Close": 51.0},
        ]
        df = _records_to_df(records)
        assert not df.empty
        assert df.index.tz is None  # timezone removido
