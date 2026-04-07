"""
core/cache.py — Capa de caché JSON con TTL y fallback a datos expirados.

Estructura de cada archivo:
  {
    "cached_at":   "2026-04-07T10:00:00.123456",
    "ttl_seconds": 300,
    "data":        { ... }
  }
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def _path(key: str, cache_dir: Path) -> Path:
    """Convierte una clave arbitraria en un nombre de archivo seguro."""
    safe = (
        key.replace("/", "_")
           .replace(":", "_")
           .replace("^", "_")
           .replace("=", "_")
           .replace(" ", "_")
    )
    return cache_dir / f"{safe}.json"


def write(key: str, data: Any, ttl: int, cache_dir: Path) -> None:
    """Persiste data en disco con metadatos de TTL."""
    _path(key, cache_dir).write_text(
        json.dumps(
            {
                "cached_at":   datetime.now().isoformat(),
                "ttl_seconds": ttl,
                "data":        data,
            },
            ensure_ascii=False,
            default=str,
        ),
        encoding="utf-8",
    )


def read(
    key: str,
    cache_dir: Path,
    *,
    allow_stale: bool = False,
) -> tuple[Any | None, bool]:
    """
    Retorna (data, is_fresh).
      - is_fresh=True  → dentro del TTL
      - is_fresh=False → expirado o inexistente
    Si allow_stale=True, devuelve data aunque haya expirado.
    Ante cualquier error de lectura/parseo retorna (None, False).
    """
    p = _path(key, cache_dir)
    if not p.exists():
        return None, False
    try:
        payload = json.loads(p.read_text(encoding="utf-8"))
        age     = (datetime.now() - datetime.fromisoformat(payload["cached_at"])).total_seconds()
        fresh   = age < payload["ttl_seconds"]
        if fresh or allow_stale:
            return payload["data"], fresh
        return None, False
    except Exception:
        return None, False
