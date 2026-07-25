from typing import Dict, List, Any

# Catálogo de empresas por sector (ejemplo muy básico)
SECTOR_CATALOG: Dict[str, List[str]] = {
    "construccion": [
        "constructora sa", "edificadora ltda", "inmobiliaria xyz", "grupo cementos"
    ],
    "servicios_financieros": [
        "banco abc", "financiera def"
    ],
    # ... otros sectores
}

# Catálogo para inferir países (más allá de la fuente)
COUNTRY_CATALOG: Dict[str, str] = {
    "comision nacional de valores": "argentina",
    "cnv": "argentina",
    # Añadir más mapeos de palabras clave a países si es necesario
}

# Catálogo de tamaños de empresa (ejemplo, podría ser por facturación o empleados)
COMPANY_SIZE_CATALOG: Dict[str, str] = {
    "grupo clarin": "grande",
    "mercado libre": "grande",
    # ...
}

def get_sector_for_company(company_name: str) -> Optional[str]:
    company_name_lower = company_name.lower()
    for sector, companies in SECTOR_CATALOG.items():
        if any(c in company_name_lower for c in companies):
            return sector
    return None

def get_country_from_text(text: str) -> Optional[str]:
    text_lower = text.lower()
    for keyword, country in COUNTRY_CATALOG.items():
        if keyword in text_lower:
            return country
    return None

def get_company_size(company_name: str) -> Optional[str]:
    return COMPANY_SIZE_CATALOG.get(company_name.lower())
