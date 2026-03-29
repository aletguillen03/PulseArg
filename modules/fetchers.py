import httpx
import json
from datetime import datetime
from pathlib import Path
from core.config import RAW_DIR

# ── Dólar (todos los tipos de cambio) ──────────────────────────────
def fetch_dolar() -> dict:
    """dolarito.ar — API pública, sin clave."""
    url = "https://dolarito.ar/api/informal"
    r = httpx.get(url, timeout=10)
    data = r.json()
    return {
        "timestamp": datetime.now().isoformat(),
        "blue":      data.get("blue", {}).get("value_sell"),
        "oficial":   data.get("oficial", {}).get("value_sell"),
        "mep":       data.get("bolsa", {}).get("value_sell"),
        "ccl":       data.get("contadoconliqui", {}).get("value_sell"),
        "cripto":    data.get("cripto", {}).get("value_sell"),
    }

# ── BCRA — reservas y variables monetarias ─────────────────────────
def fetch_bcra(variable_id: int) -> dict:
    """
    IDs útiles:
      1  = Reservas internacionales (millones USD)
      4  = Tipo de cambio oficial (BNA)
      27 = Inflación mensual
      28 = Inflación interanual
    """
    url = f"https://api.bcra.gob.ar/estadisticas/v2.0/datosvariable/{variable_id}/1/10"
    r = httpx.get(url, timeout=10, verify=False)  # BCRA tiene cert issues
    results = r.json().get("results", [])
    return {
        "variable_id": variable_id,
        "data": [{"fecha": x["fecha"], "valor": x["valor"]} for x in results]
    }

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
