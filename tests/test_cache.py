"""
tests/test_cache.py — Tests unitarios de la capa de caché.
Corre 100% offline: no hace ningún request HTTP.
"""
import time
import pytest
from core import cache


# ── write / read básico ───────────────────────────────────────────────

def test_write_y_read_fresco(tmp_path):
    cache.write("clave", {"valor": 42}, ttl=60, cache_dir=tmp_path)
    data, fresh = cache.read("clave", tmp_path)
    assert fresh is True
    assert data == {"valor": 42}


def test_read_expirado_sin_allow_stale(tmp_path):
    cache.write("clave", {"valor": 42}, ttl=0, cache_dir=tmp_path)
    time.sleep(0.01)  # asegura que ttl=0 expire
    data, fresh = cache.read("clave", tmp_path)
    assert fresh is False
    assert data is None


def test_read_expirado_con_allow_stale(tmp_path):
    cache.write("clave", {"valor": 99}, ttl=0, cache_dir=tmp_path)
    time.sleep(0.01)
    data, fresh = cache.read("clave", tmp_path, allow_stale=True)
    assert fresh is False
    assert data == {"valor": 99}


def test_read_inexistente(tmp_path):
    data, fresh = cache.read("no_existe", tmp_path)
    assert data is None
    assert fresh is False


def test_read_inexistente_allow_stale(tmp_path):
    data, fresh = cache.read("no_existe", tmp_path, allow_stale=True)
    assert data is None
    assert fresh is False


# ── sobreescritura ────────────────────────────────────────────────────

def test_write_sobreescribe(tmp_path):
    cache.write("k", "v1", ttl=60, cache_dir=tmp_path)
    cache.write("k", "v2", ttl=60, cache_dir=tmp_path)
    data, _ = cache.read("k", tmp_path)
    assert data == "v2"


# ── sanitización de claves ────────────────────────────────────────────

def test_clave_con_caracteres_especiales(tmp_path):
    """Claves con ^, :, =, / y espacios deben guardarse y leerse correctamente."""
    clave = "history_^MERV_3mo"
    cache.write(clave, [1, 2, 3], ttl=60, cache_dir=tmp_path)
    data, fresh = cache.read(clave, tmp_path)
    assert fresh is True
    assert data == [1, 2, 3]


def test_clave_con_slash_y_igual(tmp_path):
    clave = "corr_ZS=F/ZC=F_3mo"
    cache.write(clave, {"r": 0.85}, ttl=60, cache_dir=tmp_path)
    data, _ = cache.read(clave, tmp_path)
    assert data == {"r": 0.85}


# ── tipos de datos ────────────────────────────────────────────────────

def test_lista(tmp_path):
    cache.write("lista", [{"a": 1}, {"b": 2}], ttl=60, cache_dir=tmp_path)
    data, fresh = cache.read("lista", tmp_path)
    assert fresh is True
    assert len(data) == 2
    assert data[0]["a"] == 1


def test_string(tmp_path):
    cache.write("str", "hola mundo", ttl=60, cache_dir=tmp_path)
    data, _ = cache.read("str", tmp_path)
    assert data == "hola mundo"


def test_numero(tmp_path):
    cache.write("num", 3.14, ttl=60, cache_dir=tmp_path)
    data, _ = cache.read("num", tmp_path)
    assert data == pytest.approx(3.14)


# ── archivo corrupto ──────────────────────────────────────────────────

def test_archivo_corrupto_retorna_none(tmp_path):
    p = tmp_path / "malo.json"
    p.write_text("esto no es json válido", encoding="utf-8")
    # El cache usa la clave "malo" → archivo "malo.json"
    data, fresh = cache.read("malo", tmp_path)
    assert data is None
    assert fresh is False
