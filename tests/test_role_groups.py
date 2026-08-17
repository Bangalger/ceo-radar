from ceo_radar.catalogs import get_role_group


def test_ceo_aliases():
    assert get_role_group("ceo") == "ceo"
    assert get_role_group("CEO") == "ceo"
    assert get_role_group("director ejecutivo") == "ceo"
    assert get_role_group("diretor executivo") == "ceo"


def test_comercial_and_gerencia():
    assert get_role_group("gerente comercial") == "comercial"
    assert get_role_group("director comercial") == "comercial"
    assert get_role_group("gerente general") == "gerencia_general"


def test_directorio_group():
    assert get_role_group("directorio") == "directorio"
    assert get_role_group("presidente") == "directorio"
    assert get_role_group("vicepresidente") == "directorio"
    assert get_role_group("director titular") == "directorio"
    assert get_role_group("directora suplente") == "directorio"


def test_otros_fallback():
    assert get_role_group("director") == "otros"
    assert get_role_group("gerente") == "otros"
    assert get_role_group("cfo") == "otros"
    assert get_role_group("cto") == "otros"
    assert get_role_group("director de marketing") == "otros"


def test_sin_clasificar():
    assert get_role_group(None) == "sin_clasificar"
    assert get_role_group("") == "sin_clasificar"
    assert get_role_group("analista") == "sin_clasificar"


def test_longest_match_prefers_specific_role():
    assert get_role_group("director comercial internacional") == "comercial"
    assert get_role_group("directorio de la empresa") == "directorio"
