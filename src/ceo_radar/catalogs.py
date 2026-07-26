"""Catálogos compartidos para curación, extracción y enriquecimiento."""

from __future__ import annotations

import unicodedata
from typing import Dict, List, Optional
from urllib.parse import urlparse

SECTOR_MARKERS: tuple[str, ...] = (
    "constructora",
    "construtora",
    "incorporadora",
    "inmobiliaria",
    "desarrolladora inmobiliaria",
    "empreendimentos",
    "realty",
)

# Empresas Latam conocidas con país asociado (clave normalizada -> país)
LATAM_COMPANIES: Dict[str, str] = {
    "gcdi": "argentina",
    "cgdi": "argentina",
    "tglt": "argentina",
    "urbanova": "argentina",
    "milicic": "argentina",
    "tenda": "brasil",
    "trisul": "brasil",
    "dasart": "brasil",
    "pdg": "brasil",
    "pdg realty": "brasil",
    "tarraf": "brasil",
    "allterra": "brasil",
    "grupo marquise": "brasil",
    "gafisa": "brasil",
    "vci": "brasil",
    "novonor": "brasil",
    "odebrecht": "brasil",
    "caparao": "brasil",
    "rossi": "brasil",
    "grupo diagonal": "brasil",
    "consciente": "brasil",
    "mota machado": "brasil",
    "rni": "brasil",
    "bonatti": "chile",
    "contract workplaces": "argentina",
}

NON_LATAM_COMPANIES: tuple[str, ...] = (
    "tektia",
    "ulma",
    "seyses",
    "rubau",
    "fcc",
    "mota-engil",
    "mota engil",
    "fortera",
    "grupo afa",
    "teixeira duarte",
    "algeco",
    "berkshire hathaway",
)

TARGET_ROLES: tuple[str, ...] = (
    "director ejecutivo",
    "diretor executivo",
    "director titular",
    "directora titular",
    "director suplente",
    "directora suplente",
    "gerente general",
    "gerente comercial",
    "director comercial",
    "diretor comercial",
    "vicepresidente",
    "presidente",
    "directorio",
    "ceo",
)

# Mapeo de dominio TLD -> país
DOMAIN_COUNTRY: Dict[str, str] = {
    ".com.br": "brasil",
    ".cl": "chile",
    ".com.ar": "argentina",
    ".ar": "argentina",
}

# Catálogo de empresas por sector (enriquecimiento opcional)
SECTOR_CATALOG: Dict[str, List[str]] = {
    "construccion": [
        "constructora",
        "construtora",
        "incorporadora",
        "inmobiliaria",
        "realty",
        "tenda",
        "trisul",
        "gafisa",
        "pdg",
        "grupo diagonal",
        "grupo marquise",
    ],
}

COMPANY_SIZE_CATALOG: Dict[str, str] = {
    "trisul": "grande",
    "tenda": "grande",
    "gafisa": "grande",
    "pdg": "grande",
    "grupo marquise": "grande",
}


def normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(char for char in decomposed if not unicodedata.combining(char)).lower()


def find_known_company(text: str) -> Optional[tuple[str, str]]:
    """Retorna (nombre_canonico, pais) si encuentra empresa conocida en el texto."""
    normalized = normalize(text)
    # Buscar coincidencias más largas primero para evitar falsos positivos
    for company_key in sorted(LATAM_COMPANIES.keys(), key=len, reverse=True):
        if company_key in normalized:
            return company_key.title(), LATAM_COMPANIES[company_key]
    return None


def get_country_for_company(company_name: str) -> Optional[str]:
    return LATAM_COMPANIES.get(normalize(company_name))


def get_country_from_url(url: str) -> Optional[str]:
    host = urlparse(url).netloc.lower()
    for suffix, country in sorted(DOMAIN_COUNTRY.items(), key=lambda x: len(x[0]), reverse=True):
        if host.endswith(suffix):
            return country
    return None


def get_sector_for_company(company_name: str) -> Optional[str]:
    company_name_lower = normalize(company_name)
    for sector, companies in SECTOR_CATALOG.items():
        if any(c in company_name_lower for c in companies):
            return sector
    return None


def get_company_size(company_name: str) -> Optional[str]:
    return COMPANY_SIZE_CATALOG.get(normalize(company_name))
