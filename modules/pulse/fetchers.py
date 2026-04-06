import httpx
import json
from datetime import datetime, timedelta
from pathlib import Path
from core.config import RAW_DIR

# ── Dólar (todos los tipos de cambio) ──────────────────────────────
def fetch_dolar() -> dict:
    """
    Obtiene tipos de cambio desde dos fuentes públicas con fallback:
      1. bluelytics.com.ar  → blue + oficial (muy estable)
      2. dolarapi.com        → MEP, CCL, cripto (y fallback para blue/oficial)
    Nunca lanza excepción: devuelve None en los campos que no pudo obtener.
    """
    result = {
        "timestamp": datetime.now().isoformat(),
        "blue":    None,
        "oficial": None,
        "mep":     None,
        "ccl":     None,
        "cripto":  None,
    }

    # Fuente 1: bluelytics — blue y oficial
    try:
        r = httpx.get("https://api.bluelytics.com.ar/v2/latest", timeout=10)
        r.raise_for_status()
        if r.text.strip():
            data = r.json()
            result["blue"]    = data.get("blue",    {}).get("value_sell")
            result["oficial"] = data.get("oficial", {}).get("value_sell")
    except Exception:
        pass  # continúa con la fuente 2

    # Fuente 2: dolarapi.com — MEP, CCL, cripto + fallback de blue/oficial
    try:
        r = httpx.get("https://dolarapi.com/v1/dolares", timeout=10)
        r.raise_for_status()
        if r.text.strip():
            by_casa = {d["casa"]: d for d in r.json()}
            if result["blue"] is None:
                result["blue"]    = by_casa.get("blue",            {}).get("venta")
            if result["oficial"] is None:
                result["oficial"] = by_casa.get("oficial",         {}).get("venta")
            result["mep"]    = by_casa.get("bolsa",            {}).get("venta")
            result["ccl"]    = by_casa.get("contadoconliqui",  {}).get("venta")
            result["cripto"] = by_casa.get("cripto",           {}).get("venta")
    except Exception:
        pass

    return result

# ── BCRA — reservas y variables monetarias ─────────────────────────
def fetch_bcra(variable_id: int, days: int = 30) -> dict:
    """
    Descarga los últimos `days` días de una variable del BCRA.
    IDs útiles:
      1  = Reservas internacionales (millones USD)
      4  = Tipo de cambio oficial (BNA)
      27 = Inflación mensual
      28 = Inflación interanual

    Usa API v4.0 (la v2.0 fue deprecada en junio 2025).
    Endpoint: /estadisticas/v4.0/monetarias/{id_variable}
    Query params: desde, hasta (YYYY-MM-DD), limit, offset
    """
    desde = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    hasta = datetime.now().strftime("%Y-%m-%d")
    url = f"https://api.bcra.gob.ar/estadisticas/v4.0/monetarias/{variable_id}"
    params = {"desde": desde, "hasta": hasta, "limit": 1000}

    try:
        r = httpx.get(url, params=params, timeout=15, verify=False)
        r.raise_for_status()
        if not r.text.strip():
            return {"variable_id": variable_id, "data": []}
        body = r.json()
        # v4.0: { "results": [{ "idVariable": N, "detalle": [{fecha, valor}, ...] }] }
        raw_results = body.get("results", []) if isinstance(body, dict) else []
        first = raw_results[0] if raw_results else {}
        data_points = (
            first.get("detalle", []) if isinstance(first, dict) and "detalle" in first
            else (raw_results if isinstance(raw_results, list) else [])
        )
        return {
            "variable_id": variable_id,
            "data": [
                {"fecha": x["fecha"], "valor": x["valor"]}
                for x in data_points
                if x.get("fecha") and x.get("valor") is not None
            ],
        }
    except Exception:
        # Fallback: v2.0 por si v4.0 no responde
        try:
            url_v2 = f"https://api.bcra.gob.ar/estadisticas/v2.0/datosvariable/{variable_id}/{desde}/{hasta}"
            r = httpx.get(url_v2, timeout=10, verify=False)
            r.raise_for_status()
            if not r.text.strip():
                return {"variable_id": variable_id, "data": []}
            results = r.json().get("results", [])
            return {
                "variable_id": variable_id,
                "data": [{"fecha": x["fecha"], "valor": x["valor"]} for x in results],
            }
        except Exception:
            return {"variable_id": variable_id, "data": []}

# ── RSS — noticias en tiempo real ──────────────────────────────────
import feedparser

FEEDS = {
    "infobae":    "https://www.infobae.com/feeds/rss/",
    "lanacion":   "https://www.lanacion.com.ar/arc/outboundfeeds/rss/",
    "ambito":     "https://www.ambito.com/rss/home.xml",
    "cronista":   "https://www.cronista.com/rss/ultimas-noticias/",
}

def fetch_news(max_per_feed: int = 10) -> list[dict]:
    articles = []
    for medio, url in FEEDS.items():
        feed = feedparser.parse(url)
        for entry in feed.entries[:max_per_feed]:
            articles.append({
                "medio":     medio,
                "titulo":    entry.get("title", ""),
                "resumen":   entry.get("summary", "")[:300],
                "link":      entry.get("link", ""),
                "publicado": entry.get("published", ""),
            })
    return articles
