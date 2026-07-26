"""Extracción estructurada de entidades desde títulos y descripciones."""

from __future__ import annotations

import re
from typing import Any, Dict, Optional

from ceo_radar.catalogs import (
    SECTOR_MARKERS,
    TARGET_ROLES,
    find_known_company,
    normalize,
)

# Patrones para extraer persona desde titulares comunes
_NAME = r"[A-ZÁÉÍÓÚÑÃÕÇ][a-záéíóúñãõç]+(?:\s+[A-ZÁÉÍÓÚÑÃÕÇ][a-záéíóúñãõç]+){0,3}"

PERSON_PATTERNS: list[re.Pattern[str]] = [
    re.compile(rf"designa\s+a\s+({_NAME})\s+como", re.IGNORECASE),
    re.compile(rf"nombr[oó]\s+(?:como\s+)?(?:a\s+)?({_NAME})\s+como", re.IGNORECASE),
    re.compile(rf"anuncia\s+({_NAME})\s+como", re.IGNORECASE),
    re.compile(rf"escolhe\s+({_NAME})\s+como", re.IGNORECASE),
    re.compile(rf"({_NAME})\s+(?:é|e)\s+o\s+novo", re.IGNORECASE),
    re.compile(rf"({_NAME})\s+assume\s+como", re.IGNORECASE),
    re.compile(rf"nomeia\s+({_NAME})", re.IGNORECASE),
]

CHANGE_KEYWORDS: tuple[str, ...] = (
    "nombramiento",
    "nombra",
    "nombró",
    "nomeia",
    "nomeou",
    "anuncia",
    "designa",
    "escolhe",
    "troca",
    "renuncia",
    "renúncia",
    "adquisición",
    "fusión",
)

CHANGE_VERBS = (
    r"anuncia|designa|nomeia|nomeou|escolhe|troca|nombr[oó]|elege|contrata|muda|passa"
)

SECTOR_PREFIX_PATTERN = re.compile(
    rf"^(?:Construtora|Constructora|Incorporadora|Inmobiliaria)\s+({_NAME})\s+(?:{CHANGE_VERBS})",
    re.IGNORECASE,
)

GRUPO_PREFIX_PATTERN = re.compile(
    rf"^Grupo\s+({_NAME})\s+(?:{CHANGE_VERBS})",
    re.IGNORECASE,
)

COMPANY_START_PATTERN = re.compile(
    rf"^({_NAME})(?:\s*\([A-Z0-9]+\))?\s+(?:{CHANGE_VERBS})",
    re.IGNORECASE,
)


def _extract_role(text: str) -> tuple[Optional[str], str]:
    normalized = normalize(text)
    for role in sorted(TARGET_ROLES, key=len, reverse=True):
        if role in normalized:
            return role, "alta"
    for keyword in ("ceo", "director", "gerente", "presidente", "cfo", "cto"):
        if re.search(r"\b" + re.escape(keyword) + r"\b", normalized):
            return keyword, "baja"
    return None, "baja"


def _extract_change_type(text: str) -> tuple[Optional[str], str]:
    normalized = normalize(text)
    for keyword in CHANGE_KEYWORDS:
        if keyword in normalized:
            return keyword, "media"
    return None, "baja"


def _extract_person(text: str) -> tuple[Optional[str], str]:
    for pattern in PERSON_PATTERNS:
        match = pattern.search(text)
        if match:
            person = match.group(1).strip()
            if len(person.split()) >= 2 or (len(person) > 4 and person[0].isupper()):
                return person, "media"
    return None, "baja"


def _extract_company_by_pattern(text: str) -> Optional[tuple[str, Optional[str]]]:
    """
    Extrae empresa por patrón posicional al inicio del titular.
    Retorna (nombre_empresa, sector_inferido) o None.
    """
    text = text.strip()

    match = SECTOR_PREFIX_PATTERN.match(text)
    if match:
        return match.group(1).strip(), "construccion"

    match = GRUPO_PREFIX_PATTERN.match(text)
    if match:
        return f"Grupo {match.group(1).strip()}", "construccion"

    match = COMPANY_START_PATTERN.match(text)
    if match:
        return match.group(1).strip(), None

    return None


def _extract_company(
    text: str,
) -> tuple[Optional[str], str, Optional[str], Optional[str]]:
    """Retorna (company, confidence, country_from_catalog, sector_inferido)."""
    known = find_known_company(text)
    if known:
        company, country = known
        return company, "alta", country, None

    pattern_result = _extract_company_by_pattern(text)
    if pattern_result:
        company, sector = pattern_result
        return company, "media", None, sector

    normalized = normalize(text)
    if any(marker in normalized for marker in SECTOR_MARKERS):
        return "Desconocida", "baja", None, None

    return None, "baja", None, None


def extract_entities_from_text(text: str) -> Dict[str, Any]:
    entities: Dict[str, Any] = {}
    confidence: Dict[str, str] = {}

    company, company_conf, catalog_country, inferred_sector = _extract_company(text)
    if company:
        entities["company"] = company
        confidence["company"] = company_conf
        if catalog_country:
            entities["country"] = catalog_country
            confidence["country"] = "alta"
        if inferred_sector:
            entities["sector"] = inferred_sector
            confidence["sector"] = "media"

    role, role_conf = _extract_role(text)
    if role:
        entities["role"] = role
        confidence["role"] = role_conf

    change_type, change_conf = _extract_change_type(text)
    if change_type:
        entities["change_type"] = change_type
        confidence["change_type"] = change_conf

    person, person_conf = _extract_person(text)
    if person:
        entities["person"] = person
        confidence["person"] = person_conf

    if confidence:
        entities["confidence"] = confidence

    return entities


def infer_country(
    *,
    source: str,
    company: Optional[str] = None,
    url: Optional[str] = None,
    catalog_country: Optional[str] = None,
) -> Optional[str]:
    """Inferir país real sin usar market como proxy."""
    if catalog_country:
        return catalog_country

    if company:
        from ceo_radar.catalogs import get_country_for_company

        country = get_country_for_company(company)
        if country:
            return country

    if url:
        from ceo_radar.catalogs import get_country_from_url

        country = get_country_from_url(url)
        if country:
            return country

    if source == "cnv":
        return "argentina"

    return None
