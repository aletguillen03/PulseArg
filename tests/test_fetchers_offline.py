"""
tests/test_fetchers_offline.py — Tests en frío de los fetchers.

Todos los tests corren en OFFLINE_MODE=True con datos de fixtures.
Ninguno hace requests HTTP; si hay un import de httpx o feedparser
se usa solo para typing, nunca se invoca la red.
"""
import json
import pytest
from pathlib import Path
from core import cache
from modules.pulse.fetchers import fetch_dolar, fetch_bcra, fetch_news

FIXTURES = Path(__file__).parent / "fixtures"


# ── Helpers ───────────────────────────────────────────────────────────

def _load_fixture(name: str, tmp_path: Path) -> None:
    """Copia un fixture al directorio de caché temporal."""
    src = FIXTURES / name
    (tmp_path / name).write_bytes(src.read_bytes())


# ── fetch_dolar ───────────────────────────────────────────────────────

class TestFetchDolar:
    def test_retorna_datos_del_cache(self, tmp_path):
        _load_fixture("dolar.json", tmp_path)
        result = fetch_dolar(cache_dir=tmp_path, offline=True)
        assert result["blue"]    == 1230.0
        assert result["oficial"] == 1065.0
        assert result["mep"]     == 1195.0
        assert result["ccl"]     == 1205.0
        assert result["cripto"]  == 1215.0

    def test_sin_cache_retorna_valores_none(self, tmp_path):
        """Sin caché y offline → devuelve dict vacío sin None explosion."""
        result = fetch_dolar(cache_dir=tmp_path, offline=True)
        assert result["blue"]    is None
        assert result["oficial"] is None
        assert "timestamp" in result

    def test_cache_fresco_tiene_prioridad(self, tmp_path):
        """Cache dentro del TTL → se sirve sin intentar fetch."""
        datos = {"timestamp": "2099-01-01T00:00:00",
                 "blue": 9999.0, "oficial": 8888.0,
                 "mep": None, "ccl": None, "cripto": None}
        cache.write("dolar", datos, ttl=3600, cache_dir=tmp_path)
        result = fetch_dolar(cache_dir=tmp_path, offline=True)
        assert result["blue"] == 9999.0

    def test_cache_expirado_se_usa_en_offline(self, tmp_path):
        """Cache expirado pero offline → sirve stale."""
        datos = {"timestamp": "2020-01-01T00:00:00",
                 "blue": 555.0, "oficial": 444.0,
                 "mep": None, "ccl": None, "cripto": None}
        cache.write("dolar", datos, ttl=0, cache_dir=tmp_path)
        result = fetch_dolar(cache_dir=tmp_path, offline=True)
        assert result["blue"] == 555.0

    def test_brecha_calculable(self, tmp_path):
        """Verifica que blue/oficial permiten calcular la brecha."""
        _load_fixture("dolar.json", tmp_path)
        r = fetch_dolar(cache_dir=tmp_path, offline=True)
        brecha = ((r["blue"] / r["oficial"]) - 1) * 100
        assert brecha == pytest.approx(15.49, rel=1e-2)


# ── fetch_bcra ────────────────────────────────────────────────────────

class TestFetchBcra:
    def test_reservas_desde_fixture(self, tmp_path):
        _load_fixture("bcra_1.json", tmp_path)
        result = fetch_bcra(1, cache_dir=tmp_path, offline=True)
        assert result["variable_id"] == 1
        assert len(result["data"]) == 22
        assert result["data"][-1]["fecha"] == "2026-01-01"
        assert result["data"][-1]["valor"] == 26750

    def test_inflacion_desde_fixture(self, tmp_path):
        _load_fixture("bcra_27.json", tmp_path)
        result = fetch_bcra(27, cache_dir=tmp_path, offline=True)
        assert result["variable_id"] == 27
        assert len(result["data"]) == 8
        assert result["data"][-1]["valor"] == 2.5

    def test_sin_cache_retorna_lista_vacia(self, tmp_path):
        result = fetch_bcra(99, cache_dir=tmp_path, offline=True)
        assert result["variable_id"] == 99
        assert result["data"] == []

    def test_datos_tienen_fecha_y_valor(self, tmp_path):
        _load_fixture("bcra_1.json", tmp_path)
        result = fetch_bcra(1, cache_dir=tmp_path, offline=True)
        for punto in result["data"]:
            assert "fecha" in punto
            assert "valor" in punto
            assert isinstance(punto["valor"], (int, float))

    def test_variable_ids_independientes(self, tmp_path):
        """Cada variable_id usa su propio archivo de caché."""
        _load_fixture("bcra_1.json",  tmp_path)
        _load_fixture("bcra_27.json", tmp_path)
        r1  = fetch_bcra(1,  cache_dir=tmp_path, offline=True)
        r27 = fetch_bcra(27, cache_dir=tmp_path, offline=True)
        assert r1["variable_id"]  == 1
        assert r27["variable_id"] == 27
        assert r1["data"] != r27["data"]


# ── fetch_news ────────────────────────────────────────────────────────

class TestFetchNews:
    def test_retorna_lista_de_articulos(self, tmp_path):
        _load_fixture("news.json", tmp_path)
        result = fetch_news(cache_dir=tmp_path, offline=True)
        assert isinstance(result, list)
        assert len(result) == 6

    def test_estructura_de_articulo(self, tmp_path):
        _load_fixture("news.json", tmp_path)
        result = fetch_news(cache_dir=tmp_path, offline=True)
        campos = {"medio", "titulo", "resumen", "link", "publicado"}
        for art in result:
            assert campos.issubset(art.keys()), f"Faltan campos en: {art}"

    def test_medios_presentes(self, tmp_path):
        _load_fixture("news.json", tmp_path)
        result = fetch_news(cache_dir=tmp_path, offline=True)
        medios = {a["medio"] for a in result}
        assert "infobae"  in medios
        assert "lanacion" in medios
        assert "ambito"   in medios
        assert "cronista" in medios

    def test_sin_cache_retorna_lista_vacia(self, tmp_path):
        result = fetch_news(cache_dir=tmp_path, offline=True)
        assert result == []

    def test_resumen_no_excede_300_chars(self, tmp_path):
        _load_fixture("news.json", tmp_path)
        result = fetch_news(cache_dir=tmp_path, offline=True)
        for art in result:
            assert len(art["resumen"]) <= 300
