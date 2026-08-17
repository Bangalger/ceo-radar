from ceo_radar.catalogs import get_sector_for_company, get_sector_for_text


def test_construction_from_title():
    assert get_sector_for_text("Constructora Tenda nomeia novo CEO") == "construccion"


def test_finance_from_title():
    assert get_sector_for_text("Banco Galicia designa nuevo gerente comercial") == "finanzas"


def test_marketing_from_title():
    assert get_sector_for_text("Agencia creativa anuncia nuevo director de marketing") == "marketing_publicidad"


def test_tech_from_title():
    assert get_sector_for_text("La fintech anuncia un nuevo CEO") == "tecnologia"


def test_unknown_text():
    assert get_sector_for_text("Nombramiento sin señales de industria") is None


def test_sector_from_known_company_name():
    assert get_sector_for_company("Trisul") == "construccion"
    assert get_sector_for_company("Empresa Desconocida SA") is None
