from typing import Dict, Any, Optional
import re
from ceo_radar.catalogs import get_country_from_text

def extract_entities_from_text(text: str) -> Dict[str, Any]:
    # Esta es una implementación básica. En el futuro, se podría usar NLP más avanzado.
    entities = {}

    # Ejemplo: Extracción de empresas (muy simplificado)
    company_keywords = ["constructora", "inmobiliaria", "grupo", "s.a.", "s.r.l."]
    for keyword in company_keywords:
        if re.search(r'\b' + re.escape(keyword) + r'\b', text, re.IGNORECASE):
            # Esto es solo un placeholder, la extracción real de la empresa sería más compleja
            entities["company"] = entities.get("company", "Desconocida") # Mejorar esto
            break

    # Ejemplo: Extracción de roles (muy simplificado)
    role_keywords = ["ceo", "director", "gerente", "presidente", "cfo", "cto"]
    for keyword in role_keywords:
        if re.search(r'\b' + re.escape(keyword) + r'\b', text, re.IGNORECASE):
            entities["role"] = keyword # Mejorar esto para extraer el rol específico
            break
    
    # Ejemplo: Extracción de tipo de cambio (muy simplificado)
    change_keywords = ["nombramiento", "renuncia", "adquisición", "fusión"]
    for keyword in change_keywords:
        if re.search(r'\b' + re.escape(keyword) + r'\b', text, re.IGNORECASE):
            entities["change_type"] = keyword
            break

    # Añadir lógica para extraer 'persona' si es posible

    # Intentar inferir el país del texto también
    country_from_text = get_country_from_text(text)
    if country_from_text:
        entities["country"] = country_from_text
    
    return entities

def infer_country_from_source(source: str, text: str = "") -> Optional[str]:
    # Primero intenta inferir del texto, luego de la fuente si no se encuentra
    country = get_country_from_text(text)
    if country:
        return country
    
    if source == "cnv":
        return "argentina"
    # Añadir más reglas para otras fuentes si es necesario
    return None
