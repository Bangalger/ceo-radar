from datetime import datetime

SPANISH_MONTHS = {
    "ene": 1,
    "feb": 2,
    "mar": 3,
    "abr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "ago": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dic": 12,
}

def parse_google_date(value: str) -> datetime:
    return datetime.strptime(value[:10], "%m/%d/%Y")

def parse_cnv_date(value: str) -> datetime:
    day, month, year, *_ = value.replace(".", "").split()
    return datetime(
        int(year),
        SPANISH_MONTHS[month.lower()],
        int(day),
    )


def parse_bo_date(value: str) -> datetime:
    """Parsea fechas dd/mm/aaaa del Boletín Oficial."""
    return datetime.strptime(value[:10], "%d/%m/%Y")
