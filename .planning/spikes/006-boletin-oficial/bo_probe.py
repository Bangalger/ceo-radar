"""Spike 006: detecta cambios ejecutivos en el Boletín Oficial (Sección 2, Argentina).

Uso:
    py .planning/spikes/006-boletin-oficial/bo_probe.py

Valida la hipótesis: ¿podemos identificar cambios de CEO/autoridades vía Boletín Oficial?
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from datetime import UTC, datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from ceo_radar.catalogs import LATAM_COMPANIES  # noqa: E402
from ceo_radar.timeframe import is_year_allowed, window_start_date  # noqa: E402

BASE = "https://www.boletinoficial.gob.ar"
SEARCH_URL = f"{BASE}/busquedaAvanzada/realizarBusqueda/segunda"
OUTPUT = Path(__file__).resolve().parent / "results" / "latest.json"
MAX_DETAILS = 120

HEADERS = {
    "User-Agent": "CEO-Radar/0.1 (+public BO data monitor)",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": f"{BASE}/busquedaAvanzada/index",
    "Accept": "application/json, text/javascript, */*; q=0.01",
}

FREE_TEXT_QUERIES = (
    "DESIGNACION DE AUTORIDADES",
    "GERENTE GENERAL",
    "PRESIDENTE",
    "DIRECTORIO",
)

TARGET_ROLES = (
    "CEO",
    "PRESIDENTE",
    "VICEPRESIDENTE",
    "DIRECTOR TITULAR",
    "DIRECTOR EJECUTIVO",
    "DIRECTORA EJECUTIVA",
    "GERENTE GENERAL",
    "GERENTE COMERCIAL",
    "DIRECTOR COMERCIAL",
    "DIRECTORA COMERCIAL",
    "DIRECTORIO",
)

CHANGE_MARKERS = (
    "DESIGN",
    "NOMBR",
    "ELECT",
    "ASUME",
    "REEMPLAZ",
    "RENUNC",
    "CESE",
    "CAMBIO",
    "VENCIMIENTO DEL MANDATO",
)

NOISE_MARKERS = (
    "CONVOCATORIA",
    "BALANCE",
    "MEMORIA",
    "DISOLUCION",
    "FUSION",
    "ABSORCION",
    "AUMENTO DE CAPITAL",
    "REDUCCION DE CAPITAL",
    "TRANSFERENCIA DE FONDO",
    "SUCESION",
    "QUIEBRA",
    "CONCURSO",
)


def normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(
        char for char in decomposed if not unicodedata.combining(char)
    ).upper()


def build_params(*, texto: str = "", denominacion: str = "") -> dict:
    start = window_start_date()
    date_from = start.strftime("%d/%m/%Y")
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


def search_section2(*, texto: str = "", denominacion: str = "") -> dict:
    response = requests.post(
        SEARCH_URL,
        data={
            "params": json.dumps(build_params(texto=texto, denominacion=denominacion)),
            "array_volver": "[]",
        },
        headers=HEADERS,
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def parse_search_html(html: str, strategy: str, query: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    results: list[dict] = []
    seen: set[str] = set()

    for link in soup.select("a[href*='/detalleAviso/segunda/']"):
        href = link.get("href", "")
        if not href or href in seen:
            continue
        seen.add(href)
        detail_url = href if href.startswith("http") else f"{BASE}{href}"
        date_match = re.search(r"(\d{2}/\d{2}/\d{4})", link.get_text(" ", strip=True))
        aviso_id_match = re.search(r"/detalleAviso/segunda/([^/]+)/", href)
        results.append(
            {
                "strategy": strategy,
                "query": query,
                "date": date_match.group(1) if date_match else "",
                "aviso_id": aviso_id_match.group(1) if aviso_id_match else "",
                "detail_url": detail_url,
            }
        )
    return results


def fetch_detail(detail_url: str) -> dict:
    response = requests.get(
        detail_url,
        headers={"User-Agent": "CEO-Radar/0.1 (+public BO data monitor)"},
        timeout=30,
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    title = soup.title.get_text(strip=True) if soup.title else ""
    entity = title.split(" - ", 1)[1].strip() if " - " in title else ""

    paragraphs = [
        p.get_text(" ", strip=True)
        for p in soup.select("p")
        if len(p.get_text(strip=True)) > 80
    ]
    document = paragraphs[0] if paragraphs else ""

    breadcrumb = soup.select_one(".breadcrumb")
    rubro = ""
    if breadcrumb:
        parts = [part.strip() for part in breadcrumb.get_text(" ", strip=True).split("Detalle")]
        rubro = parts[0].strip() if parts else ""

    pub_date = ""
    pub_match = re.search(
        r"Fecha de publicaci[oó]n\s*(\d{2}/\d{2}/\d{4})",
        soup.get_text(" ", strip=True),
        re.IGNORECASE,
    )
    if pub_match:
        pub_date = pub_match.group(1)

    return {
        "entity": entity,
        "rubro": rubro,
        "date": pub_date,
        "document": document,
        "title": title,
    }


def is_date_in_window(date: str) -> bool:
    match = re.search(r"\b(20\d{2})\b", date)
    return bool(match and is_year_allowed(int(match.group(1))))


def classify_relevance(text: str) -> tuple[bool, str]:
    normalized = normalize(text)
    has_role = any(role in normalized for role in TARGET_ROLES)
    has_change = any(marker in normalized for marker in CHANGE_MARKERS)
    has_noise = any(marker in normalized for marker in NOISE_MARKERS)

    if has_role and has_change and not has_noise:
        return True, "alta"
    if has_role and has_change:
        return True, "media"
    if has_change and ("DIRECTOR" in normalized or "GERENTE" in normalized):
        return True, "baja"
    return False, "ruido"


def argentina_companies() -> list[str]:
    return sorted(
        {
            company.title()
            for company, country in LATAM_COMPANIES.items()
            if country == "argentina"
        }
    )


def _lookback_days() -> int:
    return (datetime.now().date() - window_start_date()).days


def build_verdict(
    *,
    raw_count: int,
    detailed_count: int,
    relevant_count: int,
    noise_count: int,
) -> dict:
    precision = round(relevant_count / detailed_count, 3) if detailed_count else 0.0
    validated = relevant_count >= 3 and precision >= 0.2
    return {
        "hypothesis": (
            "Podemos identificar cambios de CEO/autoridades a través del Boletín Oficial"
        ),
        "validated": validated,
        "confidence": "alta" if validated and precision >= 0.4 else "media" if validated else "baja",
        "summary": (
            f"Se encontraron {relevant_count} avisos relevantes de {detailed_count} "
            f"analizados ({raw_count} candidatos en búsqueda). "
            + (
                "La hipótesis se valida: el buscador de Sección 2 permite detectar "
                "designaciones de autoridades con empresa y texto identificables."
                if validated
                else "La hipótesis no se valida con confianza suficiente en esta corrida."
            )
        ),
        "metrics": {
            "raw_candidates": raw_count,
            "details_fetched": detailed_count,
            "relevant": relevant_count,
            "noise": noise_count,
            "precision_on_sample": precision,
            "lookback_days": _lookback_days(),
        },
        "limitations": [
            "Alto volumen de avisos comerciales no ejecutivos (convocatorias, balances, etc.).",
            "El lenguaje societario usa Presidente/Directorio/Gerente General, no CEO.",
            "Endpoint interno no documentado; puede cambiar sin aviso.",
            "La búsqueda por empresa requiere coincidencia parcial en denominación social.",
        ],
    }


def main() -> int:
    searches: list[dict] = []
    candidates: list[dict] = []
    seen_urls: set[str] = set()

    for query in FREE_TEXT_QUERIES:
        payload = search_section2(texto=query)
        html = payload.get("content", {}).get("html", "")
        count = payload.get("content", {}).get("cantidad_result_seccion", 0)
        parsed = parse_search_html(html, "texto_libre", query)
        searches.append({"strategy": "texto_libre", "query": query, "result_count": count})
        for item in parsed:
            if item["detail_url"] not in seen_urls:
                seen_urls.add(item["detail_url"])
                candidates.append(item)
        print(f"texto_libre '{query}': {count} resultados, {len(parsed)} parseados")

    for company in argentina_companies():
        payload = search_section2(denominacion=company)
        html = payload.get("content", {}).get("html", "")
        count = payload.get("content", {}).get("cantidad_result_seccion", 0)
        if count <= 0:
            continue
        parsed = parse_search_html(html, "empresa_conocida", company)
        searches.append(
            {
                "strategy": "empresa_conocida",
                "query": company,
                "result_count": count,
            }
        )
        for item in parsed:
            if item["detail_url"] not in seen_urls:
                seen_urls.add(item["detail_url"])
                candidates.append(item)
        print(f"empresa '{company}': {count} resultados, {len(parsed)} parseados")

    current_window_candidates = [
        item for item in candidates if not item["date"] or is_date_in_window(item["date"])
    ]
    to_fetch = current_window_candidates[:MAX_DETAILS]

    results: list[dict] = []
    relevant_count = 0
    noise_count = 0

    for item in to_fetch:
        try:
            detail = fetch_detail(item["detail_url"])
        except requests.RequestException as error:
            print(f"Error detalle {item['detail_url']}: {error}")
            continue

        full_text = f"{detail['entity']} {detail['rubro']} {detail['document']}"
        relevant, relevance = classify_relevance(full_text)
        if relevant:
            relevant_count += 1
        else:
            noise_count += 1

        results.append(
            {
                **item,
                "entity": detail["entity"],
                "rubro": detail["rubro"],
                "date": detail["date"] or item["date"],
                "description": detail["document"][:500],
                "relevant": relevant,
                "relevance": relevance,
            }
        )

    output = {
        "fetched_at": datetime.now(UTC).isoformat(),
        "source": "Boletín Oficial de la República Argentina — Sección 2",
        "source_url": f"{BASE}/busquedaAvanzada/index",
        "year": datetime.now(UTC).year,
        "country_focus": "argentina",
        "criteria": {
            "section": 2,
            "free_text_queries": FREE_TEXT_QUERIES,
            "company_seeds": argentina_companies(),
            "target_roles": TARGET_ROLES,
            "change_markers": CHANGE_MARKERS,
            "lookback_days": _lookback_days(),
        },
        "searches": searches,
        "raw_candidate_count": len(candidates),
        "result_count": len(results),
        "relevant_count": relevant_count,
        "noise_count": noise_count,
        "verdict": build_verdict(
            raw_count=len(candidates),
            detailed_count=len(results),
            relevant_count=relevant_count,
            noise_count=noise_count,
        ),
        "results": results,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"\nCandidatos: {len(candidates)} | Detalle analizado: {len(results)}")
    print(f"Relevantes: {relevant_count} | Ruido: {noise_count}")
    print(f"Veredicto: {'VALIDADA' if output['verdict']['validated'] else 'NO VALIDADA'}")
    print(f"Guardado en {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
