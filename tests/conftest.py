"""
conftest.py — Configuración global de pytest para PulseArg.

Agrega el directorio raíz al sys.path para que los imports de
core.* y modules.* funcionen independientemente de dónde se
ejecute pytest.
"""
import sys
from pathlib import Path

# Raíz del proyecto
ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
