import httpx
import feedparser
from datetime import datetime, timedelta

from core import cache
from core.config import (
    RAW_DIR, OFFLINE_MODE, BCRA_VERIFY_SSL,
    BLUELYTICS_URL, DOLARAPI_URL, BCRA_URL_V4, BCRA_URL_V2,
    CACHE_TTL_DOLAR, CACHE_TTL_BCRA, CACHE_TTL_NEWS,
)

# ── Dólar ─────────────────────────────────────────────────────────────

def fetch_dolar(*, cache_dir=None, offline=None) -> dict:
    """
    Tipos de cambio: blue, oficial, MEP, CCL, cripto.
    Estrategia: caché fresco → fetch en vivo → caché expirado.
    En modo offline omite el fetch y sirve caché (aunque esté expirado).
    """
    _dir     = cache_dir if cache_dir is not None else RAW_DIR
    _offline = offline   if offline   is not None else OFFLINE_MODE

    data, fresh = cache.read("dolar", _dir)
    if fresh:
        return data

    if _offline:
        stale, _ = cache.read("dolar", _dir, allow_stale=True)
        return stale or _empty_dolar()

    result = _empty_dolar()

    # Fuente 1: bluelytics — blue + oficial
    try:
        r = httpx.get(BLUELYTICS_URL, timeout=10)
        r.raise_for_status()
        if r.text.strip():
            raw = r.json()
            result["blue"]    = raw.get("blue",    {}).get("value_sell")
            result["oficial"] = raw.get("oficial", {}).get("value_sell")
    except Exception:
        pass

    # Fuente 2: dolarapi — MEP, CCL, cripto + fallback blue/oficial
    try:
        r = httpx.get(DOLARAPI_URL, timeout=10)
        r.raise_for_status()
        if r.text.strip():
            by_casa = {d["casa"]: d for d in r.json()}
            if result["blue"]    is None:
                result["blue"]    = by_casa.get("blue",           {}).get("venta")
            if result["oficial"] is None:
                result["oficial"] = by_casa.get("oficial",        {}).get("venta")
            result["mep"]    = by_casa.get("bolsa",           {}).get("venta")
            result["ccl"]    = by_casa.get("contadoconliqui", {}).get("venta")
            result["cripto"] = by_casa.get("cripto",          {}).get("venta")
    except Exception:
        pass

    if any(result[k] for k in ("blue", "oficial", "mep", "ccl", "cripto")):
        cache.write("dolar", result, CACHE_TTL_DOLAR, _dir)
    else:
        stale, _ = cache.read("dolar", _dir, allow_stale=True)
        if stale:
            return stale

    return result


def _empty_dolar() -> dict:
    return {
        "timestamp": datetime.now().isoformat(),
        "blue": None, "oficial": None,
        "mep":  None, "ccl":     None, "cripto": None,
    }


# ── BCRA ──────────────────────────────────────────────────────────────

def fetch_bcra(variable_id: int, days: int = 30,
               *, cache_dir=None, offline=None) -> dict:
    """
    Serie histórica de una variable del BCRA (v4.0 con fallback a v2.0).
    IDs: 1=Reservas USD, 4=TC oficial BNA, 27=Inflación mensual, 28=Inflación interanual.
    """
    _dir     = cache_dir if cache_dir is not None else RAW_DIR
    _offline = offline   if offline   is not None else OFFLINE_MODE
    key      = f"bcra_{variable_id}"

    data, fresh = cache.read(key, _dir)
    if fresh:
        return data

    if _offline:
        stale, _ = cache.read(key, _dir, allow_stale=True)
        return stale or {"variable_id": variable_id, "data": []}

    desde = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    hasta = datetime.now().strftime("%Y-%m-%d")

    result = (
        _bcra_v4(variable_id, desde, hasta)
        or _bcra_v2(variable_id, desde, hasta)
        or {"variable_id": variable_id, "data": []}
    )

    if result["data"]:
        cache.write(key, result, CACHE_TTL_BCRA, _dir)
    else:
        stale, _ = cache.read(key, _dir, allow_stale=True)
        if stale:
            return stale

    return result


def _bcra_v4(variable_id: int, desde: str, hasta: str) -> dict | None:
    url    = f"{BCRA_URL_V4}/{variable_id}"
    params = {"desde": desde, "hasta": hasta, "limit": 1000}
    try:
        r = httpx.get(url, params=params, timeout=15, verify=BCRA_VERIFY_SSL)
        r.raise_for_status()
        if not r.text.strip():
            return None
        body    = r.json()
        results = body.get("results", []) if isinstance(body, dict) else []
        first   = results[0] if results else {}
        points  = (
            first.get("detalle", [])
            if isinstance(first, dict) and "detalle" in first
            else (results if isinstance(results, list) else [])
        )
        return {
            "variable_id": variable_id,
            "data": [
                {"fecha": x["fecha"], "valor": x["valor"]}
                for x in points
                if x.get("fecha") and x.get("valor") is not None
            ],
        }
    except Exception:
        return None


def _bcra_v2(variable_id: int, desde: str, hasta: str) -> dict | None:
    url = f"{BCRA_URL_V2}/{variable_id}/{desde}/{hasta}"
    try:
        r = httpx.get(url, timeout=10, verify=BCRA_VERIFY_SSL)
        r.raise_for_status()
        if not r.text.strip():
            return None
        results = r.json().get("results", [])
        return {
            "variable_id": variable_id,
            "data": [{"fecha": x["fecha"], "valor": x["valor"]} for x in results],
        }
    except Exception:
        return None


# ── RSS — noticias ────────────────────────────────────────────────────

FEEDS = {
    "infobae":  "https://www.infobae.com/feeds/rss/",
    "lanacion":  "https://www.lanacion.com.ar/arc/outboundfeeds/rss/",
    "ambito":    "https://www.ambito.com/rss/home.xml",
    "cronista":  "https://www.cronista.com/rss/ultimas-noticias/",
}


def fetch_news(max_per_feed: int = 10, *, cache_dir=None, offline=None) -> list[dict]:
    """Noticias económicas vía RSS de cuatro medios argentinos."""
    _dir     = cache_dir if cache_dir is not None else RAW_DIR
    _offline = offline   if offline   is not None else OFFLINE_MODE

    data, fresh = cache.read("news", _dir)
    if fresh:
        return data

    if _offline:
        stale, _ = cache.read("news", _dir, allow_stale=True)
        return stale or []

    articles = []
    for medio, url in FEEDS.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:max_per_feed]:
                articles.append({
                    "medio":     medio,
                    "titulo":    entry.get("title",    ""),
                    "resumen":   entry.get("summary",  "")[:300],
                    "link":      entry.get("link",     ""),
                    "publicado": entry.get("published",""),
                })
        except Exception:
            continue

    if articles:
        cache.write("news", articles, CACHE_TTL_NEWS, _dir)
    else:
        stale, _ = cache.read("news", _dir, allow_stale=True)
        if stale:
            return stale

    return articles
