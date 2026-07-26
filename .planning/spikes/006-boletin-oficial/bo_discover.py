"""Descubre el endpoint del buscador avanzado del Boletín Oficial (Sección 2).

Hallazgo principal (2026-07-25):
- No hay API pública documentada.
- El buscador avanzado usa POST interno:
  /busquedaAvanzada/realizarBusqueda/segunda
- Payload: params=<JSON>, array_volver=[]
- Respuesta JSON con content.html (HTML embebido) y cantidad_result_seccion.
- Detalle de aviso: GET /detalleAviso/segunda/{id}/{fecha}?busqueda=1
- requests + BeautifulSoup alcanzan; no se requiere headless browser.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta

import requests

BASE = "https://www.boletinoficial.gob.ar"
SEARCH_URL = f"{BASE}/busquedaAvanzada/realizarBusqueda/segunda"
HEADERS = {
    "User-Agent": "CEO-Radar/0.1 (+public BO data monitor)",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": f"{BASE}/busquedaAvanzada/index",
    "Accept": "application/json, text/javascript, */*; q=0.01",
}


def build_params(texto: str = "", denominacion: str = "", days: int = 90) -> dict:
    date_from = (datetime.now() - timedelta(days=days)).strftime("%d/%m/%Y")
    date_to = datetime.now().strftime("%d/%m/%Y")
    return {
        "texto": texto,
        "seccion": [2],
        "seccionesOriginales": [2],
        "rubros": [],
        "nroNorma": "",
        "anioNorma": "",
        "ordenamiento": "",
        "denominacion": denominacion,
        "tipoContratacion": "",
        "anioContratacion": "",
        "nroContratacion": "",
        "fechaDesde": date_from,
        "fechaHasta": date_to,
        "fecha": "",
        "tipoBusqueda": "Avanzada",
        "numeroPagina": 1,
        "ultimoRubro": "",
        "busquedaRubro": False,
        "hayMasResultadosBusqueda": "",
        "ejecutandoLlamadaAsincronicaBusqueda": "",
        "ultimaSeccion": "",
        "todasLasPalabras": True,
        "filtroPorRubrosSeccion": False,
        "filtroPorRubroBusqueda": False,
        "filtroPorSeccionBusqueda": False,
        "busquedaOriginal": True,
        "comienzaDenominacion": False,
        "ordenamientoSegunda": True,
        "ultimoItemExterno": None,
        "ultimoItemInterno": None,
    }


def probe_endpoint(texto: str = "DESIGNACION DE AUTORIDADES") -> dict:
    response = requests.post(
        SEARCH_URL,
        data={"params": json.dumps(build_params(texto=texto)), "array_volver": "[]"},
        headers=HEADERS,
        timeout=60,
    )
    response.raise_for_status()
    payload = response.json()
    content = payload.get("content", {})
    return {
        "endpoint": SEARCH_URL,
        "method": "POST",
        "transport": "requests + BeautifulSoup (sin headless browser)",
        "query": texto,
        "error": payload.get("error"),
        "result_count": content.get("cantidad_result_seccion"),
        "html_bytes": len(content.get("html", "")),
    }


def main() -> int:
    result = probe_endpoint()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("error") == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
