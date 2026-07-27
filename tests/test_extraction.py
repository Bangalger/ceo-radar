import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ceo_radar.extraction import (
    extract_entities_from_text,
    extract_entities_from_title_and_snippet,
)


def test_beyond_one_person_first_headline():
    text = (
        "Diego Salazar empezó a trabajar en Beyond One "
        "Tras cinco años construyendo su propia marca"
    )
    result = extract_entities_from_text(text)
    assert result["company"] == "Beyond One"
    assert result["person"] == "Diego Salazar"


def test_xp_director_de_marketing():
    text = (
        "Marcelo Bronze es el nuevo director de marketing de XP "
        "Luego de seis años en Danone, Bronze asume la dirección del departamento creativo."
    )
    result = extract_entities_from_text(text)
    assert result["company"] == "XP"
    assert result["person"] == "Marcelo Bronze"


def test_lucas_fernandez_not_company_false_positive():
    text = (
        "Lucas Fernández anuncia su salida de Arcos Dorados y "
        "María Esther Rivera Rodríguez empieza en Grupo Lala"
    )
    result = extract_entities_from_text(text)
    assert result.get("company") == "Grupo Lala"
    assert result.get("person") == "Lucas Fernández"
    assert result.get("company") != "Lucas Fernández"


def test_pepsico_mexico_country_suffix():
    text = "Mauricio Bernal fue ascendido en PepsiCo México"
    result = extract_entities_from_text(text)
    assert result["company"] == "PepsiCo México"
    assert result["country"] == "mexico"


def test_trisul_company_start_pattern():
    text = "Trisul anuncia nuevo director ejecutivo"
    result = extract_entities_from_text(text)
    assert result["company"] == "Trisul"
    assert result.get("person") is None


def test_constructora_tenda_nomeia():
    text = "Constructora Tenda nomeia João Silva como CEO"
    result = extract_entities_from_text(text)
    assert result["company"] == "Tenda"
    assert result["person"] == "João Silva"


def test_cnv_style_known_company_in_body():
    text = "Hecho relevante: Trisul SA informa nombramiento de nuevo director ejecutivo"
    result = extract_entities_from_text(text)
    assert result["company"] == "Trisul"


def test_title_priority_over_snippet_noise():
    title = (
        "Lucas Fernández anuncia su salida de Arcos Dorados y "
        "María Esther Rivera Rodríguez empieza en Grupo Lala"
    )
    snippet = (
        "Fernández trabajó durante más de una década en Arcos Dorados "
        "y ahora inicia una nueva etapa en el mercado lácteo."
    )
    result = extract_entities_from_title_and_snippet(title, snippet)
    assert result["company"] == "Grupo Lala"
    assert result["person"] == "Lucas Fernández"


def test_freddo_llego_a_company():
    title = "Lucas Fernández llegó a Freddo como chief commercial & marketing officer"
    snippet = "Hasta febrero había sido director de marketing en Arcos Dorados."
    result = extract_entities_from_title_and_snippet(title, snippet)
    assert result["company"] == "Freddo"


def test_headline_without_company_destination():
    text = "Lina Hoyos y Claudia Contreras abandonan su puestos como CMOs"
    result = extract_entities_from_text(text)
    assert result.get("company") is None
