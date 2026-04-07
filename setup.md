# PulseArg — Setup Guide

Dashboard de inteligencia económica modular para Argentina. Ejecuta 100% local, sin servicios externos de pago.

## Requisitos

- macOS con Apple Silicon (M1/M2/M3/M4) o Linux
- Python 3.13+
- Conexión a internet (para las APIs públicas)

## Instalación

### 1. Clonar el repositorio

```bash
git clone <repo-url>
cd PulseArg
```

### 2. Crear y activar el entorno virtual

```bash
python3.13 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

## Ejecutar el dashboard

Siempre correr desde la raíz del proyecto:

```bash
cd ~/Proyectos/PulseArg
streamlit run dashboard.py
```

Abre automáticamente en `http://localhost:8501`.

## Estructura del proyecto

```
PulseArg/
├── dashboard.py              # Punto de entrada principal (Streamlit)
├── requirements.txt          # Dependencias pinneadas
├── setup.md                  # Este archivo
├── core/
│   ├── __init__.py
│   └── config.py             # Configuración global (rutas BASE_DIR, DATA_DIR, RAW_DIR)
├── modules/
│   └── pulse/
│       ├── __init__.py
│       ├── fetchers.py       # Fetchers HTTP: dólar, BCRA, RSS
│       ├── markets.py        # Datos de mercado vía yfinance
│       ├── dashboard.py      # Componentes UI del dashboard
│       └── anomaly.py        # Detección de anomalías (z-score)
├── data/
│   └── raw/                  # Cache local de datos (auto-creado)
└── venv/                     # Entorno virtual (no versionar)
```

## Fuentes de datos

| Fuente | Datos | Endpoint |
|--------|-------|----------|
| bluelytics.com.ar | Dólar blue y oficial | `api.bluelytics.com.ar/v2/latest` |
| dolarapi.com | MEP, CCL, cripto | `dolarapi.com/v1/dolares` |
| BCRA v4.0 | Reservas (var 1), Inflación (var 27) | `api.bcra.gob.ar/estadisticas/v4.0/monetarias/{id}` |
| Yahoo Finance | Acciones, índices, commodities | vía `yfinance` |
| RSS feeds | Noticias económicas | Infobae, La Nación, Ámbito, Cronista |

## Stack técnico

| Capa | Tecnología |
|------|-----------|
| UI / Frontend | Streamlit + CSS custom (tema dark blue) |
| Visualización | Plotly (go.Figure, px.imshow) |
| HTTP | httpx |
| Datos de mercado | yfinance |
| RSS / Noticias | feedparser |
| Procesamiento | pandas, numpy |
| Detección anomalías | módulo propio con z-score (`modules/pulse/anomaly.py`) |

## Módulos

### `core/config.py`
Configuración centralizada de rutas. Define `BASE_DIR`, `DATA_DIR` y `RAW_DIR`. Crea el directorio `data/raw/` automáticamente si no existe.

### `modules/pulse/fetchers.py`
Fetchers HTTP para:
- `fetch_dolar()` — tipos de cambio (blue, oficial, MEP, CCL, cripto) con fallback entre dos fuentes
- `fetch_bcra(variable_id, days)` — series históricas del BCRA (v4.0 con fallback a v2.0)
- `fetch_news(max_per_feed)` — noticias vía RSS de cuatro medios

### `modules/pulse/markets.py`
Datos de mercado vía Yahoo Finance:
- `fetch_snapshot()` — precio y variación diaria de todos los activos
- `fetch_history(ticker, period)` — serie histórica de cierre
- `fetch_correlation(tickers, period)` — matriz de correlación de retornos

### `modules/pulse/anomaly.py`
- `detect_anomalies(history, current, threshold)` — z-score sobre historial; alerta si |z| > umbral (default 2.0σ)

### `modules/pulse/dashboard.py`
Componentes de UI reutilizables (`render_tile`, `render_market_card`) y lógica de layout de las pestañas Panorama, Finanzas y Noticias.

## Convenciones de desarrollo

- Correr siempre Streamlit desde la raíz del proyecto
- Todos los paquetes necesitan `__init__.py` para que los imports funcionen
- `dashboard.py` corrige `sys.path` al inicio
- Cada sesión debe terminar con algo funcional
- Código completo listo para pegar, sin fragmentos aislados
- Comentarios en español

## Actualización de dependencias

Para regenerar `requirements.txt` con versiones actuales del venv:

```bash
source venv/bin/activate
pip freeze > requirements.txt
```
