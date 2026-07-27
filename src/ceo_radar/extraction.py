"""Extracción estructurada de entidades desde títulos y descripciones."""

from __future__ import annotations

import re
from typing import Any, Dict, Optional

from ceo_radar.catalogs import (
    SECTOR_MARKERS,
    TARGET_ROLES,
    find_known_company,
    get_country_from_company_suffix,
    normalize,
)

# Patrones para extraer persona desde titulares comunes
_NAME_PART = r"[A-ZÁÉÍÓÚÑÃÕÇÜ][\wáéíóúñãõç]*"
_NAME = (
    rf"{_NAME_PART}(?:\s+(?:del|de la|de|y)\s+{_NAME_PART}|\s+{_NAME_PART}){{0,3}}"
)

# Patrón permisivo para nombres de organización (siglas, CamelCase, símbolos)
_ORG_TOKEN = r"[A-Z0-9ÁÉÍÓÚÑÃÕÇÜ][\w&.'’+\-]*"
_ORG = rf"{_ORG_TOKEN}(?:[ \-](?:de|del|la|y|&|do|da)?[ ]?{_ORG_TOKEN}){{0,4}}"

PERSON_LEADING_PATTERN = re.compile(
    rf"^({_NAME_PART}\s+{_NAME_PART}(?:\s+{_NAME_PART}){{0,2}})\s+"
    rf"(?:fue ascendid|empez|empieza|asume|asumi|lleg|se incorpora|ahora trabaja|"
    rf"tiene un nuevo puesto|cambi[óo] de|vuelve|deja|dejar[áa]|se va|anuncia|"
    rf"es (?:el|la|un|una))",
    re.IGNORECASE,
)

PERSON_PATTERNS: list[re.Pattern[str]] = [
    PERSON_LEADING_PATTERN,
    re.compile(rf"designa\s+a\s+({_NAME})\s+como", re.IGNORECASE),
    re.compile(rf"nombr[oó]\s+(?:como\s+)?(?:a\s+)?({_NAME})\s+como", re.IGNORECASE),
    re.compile(rf"nomeia\s+({_NAME})\s+como", re.IGNORECASE),
    re.compile(rf"anuncia\s+({_NAME})\s+como", re.IGNORECASE),
    re.compile(rf"escolhe\s+({_NAME})\s+como", re.IGNORECASE),
    re.compile(rf"({_NAME})\s+(?:é|e)\s+o\s+novo", re.IGNORECASE),
    re.compile(rf"({_NAME})\s+assume\s+como", re.IGNORECASE),
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

PERSONAL_ACTION_PATTERN = re.compile(
    r"^(?:"
    r"anuncia\s+su\s+salida"
    r"|deja\b"
    r"|dejar[áa]\b"
    r"|se\s+va\b"
    r"|renuncia\b"
    r")",
    re.IGNORECASE,
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

# Patrones persona-primero: empresa al final tras preposición
COMPANY_TRAILING_PATTERNS: list[re.Pattern[str]] = [
    re.compile(rf"fue ascendid[oa]\s+en\s+(?:el\s+)?({_ORG})", re.IGNORECASE),
    re.compile(rf"empez[óo]\s+a\s+trabajar\s+(?:en|para)\s+(?:el\s+)?({_ORG})", re.IGNORECASE),
    re.compile(rf"empez[óo]\s+en\s+un\s+nuevo\s+puesto\s+en\s+(?:el\s+)?({_ORG})", re.IGNORECASE),
    re.compile(rf"empieza\s+en\s+un\s+nuevo\s+puesto\s+en\s+(?:el\s+)?({_ORG})", re.IGNORECASE),
    re.compile(rf"asume\s+un\s+nuevo\s+cargo\s+en\s+(?:el\s+)?({_ORG})", re.IGNORECASE),
    re.compile(rf"asumi[óo]\s+la\s+direcci[óo]n\s+de\s+marketing\s+de\s+(?:el\s+)?({_ORG})", re.IGNORECASE),
    re.compile(rf"lleg[óo]\s+a\s+(?:el\s+)?({_ORG})(?:\s+como|\s*$)", re.IGNORECASE),
    re.compile(rf"se\s+incorpora\s+a\s+(?:el\s+)?({_ORG})", re.IGNORECASE),
    re.compile(rf"se\s+despide\s+de\s+(?:el\s+)?({_ORG})", re.IGNORECASE),
    re.compile(rf"ahora\s+trabaja\s+en\s+(?:el\s+)?({_ORG})\s*$", re.IGNORECASE),
    re.compile(rf"tiene\s+un\s+nuevo\s+puesto\s+en\s+(?:el\s+)?({_ORG})", re.IGNORECASE),
    re.compile(rf"cambi[óo]\s+de\s+(?:sector\s+y\s+cargo|categor[íi]a)\s+en\s+(?:el\s+)?({_ORG})", re.IGNORECASE),
    re.compile(rf"vuelve\s+al\s+pa[íi]s\s+de\s+la\s+mano\s+de\s+(?:el\s+)?({_ORG})", re.IGNORECASE),
    re.compile(
        rf"es\s+(?:el|la)\s+(?:nuev[oa]\s+)?(?:[\w&]+\s+){{1,6}}(?:de|en)\s+(?:el\s+)?({_ORG})\s*$",
        re.IGNORECASE,
    ),
    re.compile(rf"es\s+(?:el|la)\s+(?:nuev[oa]\s+)?CMO\s+de\s+(?:el\s+)?({_ORG})\s*$", re.IGNORECASE),
    re.compile(rf"dejar[áa]\s+(?:el\s+)?({_ORG})\s*$", re.IGNORECASE),
    re.compile(
        rf"como\s+(?:director|directora|gerente|head|chief|CMO|CMMO)[\w\s&]*\s+en\s+(?:el\s+)?({_ORG})",
        re.IGNORECASE,
    ),
    re.compile(rf"empieza\s+una\s+nueva\s+etapa\s+en\s+(?:el\s+)?({_ORG})\s*$", re.IGNORECASE),
    re.compile(rf"llega\s+a\s+(?:el\s+)?({_ORG})\s+como", re.IGNORECASE),
    re.compile(
        rf"es\s+nuev[oa]\s+[\w\s&]+\s+(?:de|en)\s+(?:el\s+)?({_ORG})\s*$",
        re.IGNORECASE,
    ),
    re.compile(
        rf"en\s+(?:el\s+)?({_ORG})(?:,\s+en\s+[A-ZÁÉÍÓÚÑ][\wáéíóú]+)?\s*$",
        re.IGNORECASE,
    ),
    re.compile(rf"empieza\s+en\s+(?:el\s+)?({_ORG})\s*$", re.IGNORECASE),
    re.compile(rf"empez[óo]\s+en\s+(?:el\s+)?({_ORG})\s*$", re.IGNORECASE),
]


def _strip_trailing_noise(text: str) -> str:
    """Recorta colas ruidosas del titular antes de matchear empresa."""
    cleaned = text.strip()
    cleaned = re.sub(
        r",\s*(?:después de|después de un|tras|luego de)\s+.*$",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"\s+a un puesto regional\s*$", "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


SNIPPET_STARTERS: tuple[str, ...] = (
    r"\s+Tras\s+(?:cinco|cuatro|tres|dos|diez|\d+)\s+años",
    r"\s+Luego\s+de\s+",
    r"\s+La\s+novedad",
    r"\s+Ahora\s+es\s+",
    r"\s+En\s+total\b",
    r"\s+Despu[eé]s\s+de\s+",
)

def _headline_portion(text: str) -> str:
    """Aísla la porción tipo titular antes del cuerpo/snippet."""
    stripped = text.strip()
    for starter in SNIPPET_STARTERS:
        match = re.search(starter, stripped, re.IGNORECASE)
        if match and match.start() > 20:
            return stripped[: match.start()].strip()
    for separator in (". ", " — ", " - "):
        if separator in stripped:
            candidate = stripped.split(separator, 1)[0].strip()
            if len(candidate.split()) >= 4:
                return candidate
    return stripped[:200].strip()


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
    headline = _headline_portion(text)
    for pattern in PERSON_PATTERNS:
        match = pattern.search(headline)
        if match:
            person = match.group(1).strip()
            if len(person.split()) >= 2 or (len(person) > 4 and person[0].isupper()):
                return person, "media"
    return None, "baja"


def _is_personal_company_start(text: str, company: str) -> bool:
    """True si el match inicial parece ser una persona, no una empresa."""
    match = COMPANY_START_PATTERN.match(text.strip())
    if not match or normalize(match.group(1)) != normalize(company):
        return False
    remainder = text.strip()[match.end() :].lstrip()
    if PERSONAL_ACTION_PATTERN.match(remainder):
        return True
    # Nombres de persona suelen ser dos o más tokens capitalizados
    return len(company.split()) >= 2 and not find_known_company(company)


def _extract_company_by_trailing_pattern(
    text: str,
    *,
    person: Optional[str] = None,
) -> Optional[tuple[str, Optional[str]]]:
    """
    Extrae empresa desde titulares persona-primero.
    Retorna (nombre_empresa, previous_company) o None.
    """
    headline = _strip_trailing_noise(_headline_portion(text))
    matches: list[tuple[str, int]] = []

    for pattern in COMPANY_TRAILING_PATTERNS:
        for match in pattern.finditer(headline):
            company = match.group(1).strip().rstrip(".,;")
            if person and normalize(company) == normalize(person):
                continue
            if len(company) < 2:
                continue
            if normalize(company) in {"salida", "pais", "país"}:
                continue
            matches.append((company, match.start()))

    if not matches:
        return None

    # Preferir el match más específico (más largo) y, en empate, el último del titular
    matches.sort(key=lambda item: (item[1], len(item[0])))
    best = matches[-1][0]
    previous_company = matches[-2][0] if len(matches) >= 2 else None
    return best, previous_company


def _extract_company_by_pattern(
    text: str,
    *,
    person: Optional[str] = None,
) -> Optional[tuple[str, Optional[str]]]:
    """
    Extrae empresa por patrón posicional al inicio del titular.
    Retorna (nombre_empresa, sector_inferido) o None.
    """
    text = _headline_portion(text).strip()

    match = SECTOR_PREFIX_PATTERN.match(text)
    if match:
        company = match.group(1).strip()
        if not person or normalize(company) != normalize(person):
            return company, "construccion"

    match = GRUPO_PREFIX_PATTERN.match(text)
    if match:
        company = f"Grupo {match.group(1).strip()}"
        if not person or normalize(company) != normalize(person):
            return company, "construccion"

    match = COMPANY_START_PATTERN.match(text)
    if match:
        company = match.group(1).strip()
        if person and normalize(company) == normalize(person):
            return None
        if _is_personal_company_start(text, company):
            return None
        return company, None

    return None


def _extract_company(
    text: str,
    *,
    person: Optional[str] = None,
) -> tuple[Optional[str], str, Optional[str], Optional[str], Optional[str]]:
    """Retorna (company, confidence, country, sector, previous_company)."""
    known = find_known_company(text)
    if known:
        company, country = known
        return company, "alta", country, None, None

    trailing = _extract_company_by_trailing_pattern(text, person=person)
    if trailing:
        company, previous_company = trailing
        suffix_country = get_country_from_company_suffix(company)
        return company, "media", suffix_country, None, previous_company

    pattern_result = _extract_company_by_pattern(text, person=person)
    if pattern_result:
        company, sector = pattern_result
        suffix_country = get_country_from_company_suffix(company)
        return company, "media", suffix_country, sector, None

    normalized = normalize(text)
    if any(marker in normalized for marker in SECTOR_MARKERS):
        return "Desconocida", "baja", None, None, None

    return None, "baja", None, None, None


def _merge_extraction(primary: Dict[str, Any], secondary: Dict[str, Any]) -> Dict[str, Any]:
    """Combina extracciones priorizando primary y completando huecos desde secondary."""
    merged = dict(secondary)
    merged.update(primary)
    primary_conf = primary.get("confidence", {})
    secondary_conf = secondary.get("confidence", {})
    if primary_conf or secondary_conf:
        merged["confidence"] = {**secondary_conf, **primary_conf}
    return merged


def extract_entities_from_title_and_snippet(title: str, snippet: str = "") -> Dict[str, Any]:
    """Extrae entidades priorizando el titular; el snippet sólo completa señales faltantes."""
    from_title = extract_entities_from_text(title)
    if not snippet.strip():
        return from_title
    from_snippet = extract_entities_from_text(snippet)
    supplemental = {
        key: value
        for key, value in from_snippet.items()
        if key != "confidence" and value and not from_title.get(key)
    }
    return _merge_extraction(from_title, supplemental)


def extract_entities_from_text(text: str) -> Dict[str, Any]:
    entities: Dict[str, Any] = {}
    confidence: Dict[str, str] = {}

    person, person_conf = _extract_person(text)

    company, company_conf, catalog_country, inferred_sector, previous_company = _extract_company(
        text,
        person=person,
    )
    if company:
        entities["company"] = company
        confidence["company"] = company_conf
        if catalog_country:
            entities["country"] = catalog_country
            confidence["country"] = "media"
        if inferred_sector:
            entities["sector"] = inferred_sector
            confidence["sector"] = "media"
        if previous_company:
            entities["previous_company"] = previous_company

    role, role_conf = _extract_role(text)
    if role:
        entities["role"] = role
        confidence["role"] = role_conf

    change_type, change_conf = _extract_change_type(text)
    if change_type:
        entities["change_type"] = change_type
        confidence["change_type"] = change_conf

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

        suffix_country = get_country_from_company_suffix(company)
        if suffix_country:
            return suffix_country

    if url:
        from ceo_radar.catalogs import get_country_from_url

        country = get_country_from_url(url)
        if country:
            return country

    if source == "cnv":
        return "argentina"

    return None
