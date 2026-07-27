import json
from datetime import datetime, UTC, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from hashlib import sha256

from ceo_radar.models import Article, Event, Run
from ceo_radar.utils import parse_bo_date, parse_cnv_date, parse_google_date
from ceo_radar.extraction import extract_entities_from_text, extract_entities_from_title_and_snippet, infer_country
from ceo_radar.catalogs import get_sector_for_company, get_company_size, normalize

ROOT = Path(__file__).resolve().parents[2]
CNV_INPUT = (
    ROOT
    / ".planning"
    / "spikes"
    / "005-cnv-hechos-relevantes"
    / "results"
    / "cnv_cambios_ejecutivos.json"
)
GOOGLE_INPUT = (
    ROOT
    / ".planning"
    / "spikes"
    / "002b-serpapi-news"
    / "results"
    / "constructoras_curadas.json"
)
BO_INPUT = (
    ROOT
    / ".planning"
    / "spikes"
    / "006-boletin-oficial"
    / "results"
    / "latest.json"
)
NICHO_INPUT = (
    ROOT
    / ".planning"
    / "spikes"
    / "007-revistas-nicho"
    / "results"
    / "curadas.json"
)
OUTPUT = ROOT / ".planning" / "results" / "oportunidades_unificadas.json"

GROUPING_WINDOW_DAYS = 45

ENTITY_KEYS = [
    "company",
    "person",
    "role",
    "change_type",
    "country",
    "search_scope",
    "sector",
    "company_size",
]


def generate_article_id(source: str, url: str) -> str:
    return sha256(f"{source}-{url}".encode()).hexdigest()


def generate_event_id(entities: Dict[str, Any], window_start: datetime) -> str:
    relevant = {
        k: v
        for k, v in entities.items()
        if k in ENTITY_KEYS and v and k != "confidence"
    }
    entity_str = "-".join(f"{k}:{v}" for k, v in sorted(relevant.items()))
    key = f"{entity_str}-{window_start.isoformat()}"
    return sha256(key.encode()).hexdigest()


def _has_reliable_company(extracted_data: Dict[str, Any]) -> bool:
    confidence = extracted_data.get("confidence", {})
    company = extracted_data.get("company")
    return bool(
        company
        and company != "Desconocida"
        and confidence.get("company") in ("alta", "media")
    )


def _grouping_key(extracted_data: Dict[str, Any]) -> Optional[Tuple[str, str]]:
    if not _has_reliable_company(extracted_data):
        return None
    company = normalize(str(extracted_data.get("company", "")))
    role = normalize(str(extracted_data.get("role", "")))
    return company, role


def _consolidate_entities(event: Event, article: Article) -> None:
    for key in ENTITY_KEYS:
        value = article.extracted_data.get(key)
        if value and not event.entities.get(key):
            event.entities[key] = value


def group_articles_into_events(articles: List[Article]) -> List[Event]:
    """Agrupa artículos por (empresa, rol) dentro de una ventana temporal."""
    events: List[Event] = []
    open_events: Dict[Tuple[str, str], Event] = {}

    sorted_articles = sorted(articles, key=lambda a: a.published_at)

    for article in sorted_articles:
        key = _grouping_key(article.extracted_data)

        if key is None:
            # Sin empresa confiable: evento individual
            entities = {
                k: v
                for k, v in article.extracted_data.items()
                if k in ENTITY_KEYS and v
            }
            event = Event(
                id=generate_event_id(entities, article.published_at),
                articles=[article],
                first_seen=article.published_at,
                last_seen=article.published_at,
                entities=entities,
            )
            events.append(event)
            continue

        existing = open_events.get(key)
        if existing and (article.published_at - existing.last_seen) <= timedelta(
            days=GROUPING_WINDOW_DAYS
        ):
            existing.articles.append(article)
            existing.first_seen = min(existing.first_seen, article.published_at)
            existing.last_seen = max(existing.last_seen, article.published_at)
            _consolidate_entities(existing, article)
            continue

        entities = {
            k: v
            for k, v in article.extracted_data.items()
            if k in ENTITY_KEYS and v
        }
        event = Event(
            id=generate_event_id(entities, article.published_at),
            articles=[article],
            first_seen=article.published_at,
            last_seen=article.published_at,
            entities=entities,
        )
        open_events[key] = event
        events.append(event)

    return sorted(events, key=lambda e: e.last_seen, reverse=True)


def run_pipeline() -> Run:
    cnv_raw = json.loads(CNV_INPUT.read_text(encoding="utf-8"))
    google_raw = json.loads(GOOGLE_INPUT.read_text(encoding="utf-8"))
    bo_raw = json.loads(BO_INPUT.read_text(encoding="utf-8"))
    nicho_raw = json.loads(NICHO_INPUT.read_text(encoding="utf-8"))

    articles: List[Article] = []

    for item in cnv_raw["results"]:
        published_at = parse_cnv_date(item["date"])
        article_id = generate_article_id("cnv", item["presentation_url"])
        full_text = f"{item['description']} {item['document']}"
        extracted_data = extract_entities_from_text(full_text)

        company_name = item["entity"]
        extracted_data["company"] = company_name
        extracted_data.setdefault("confidence", {})["company"] = "alta"

        country = infer_country(
            source="cnv",
            company=company_name,
            url=item["presentation_url"],
        )
        if country:
            extracted_data["country"] = country
            extracted_data.setdefault("confidence", {})["country"] = "alta"

        sector = get_sector_for_company(company_name)
        if sector:
            extracted_data["sector"] = sector
        size = get_company_size(company_name)
        if size:
            extracted_data["company_size"] = size

        articles.append(
            Article(
                id=article_id,
                source="cnv",
                url=item["presentation_url"],
                title=item["description"],
                published_at=published_at,
                content=item["document"],
                extracted_data=extracted_data,
            )
        )

    for item in google_raw["results"]:
        published_at = parse_google_date(item["date"])
        article_id = generate_article_id("google_news", item["link"])
        full_text = f"{item['title']} {item['snippet']}"
        extracted_data = extract_entities_from_text(full_text)

        extracted_data["search_scope"] = item.get("market")

        catalog_country = extracted_data.get("country")
        country = infer_country(
            source="google_news",
            company=extracted_data.get("company"),
            url=item["link"],
            catalog_country=catalog_country,
        )
        if country:
            extracted_data["country"] = country
            extracted_data.setdefault("confidence", {})["country"] = (
                "alta" if catalog_country else "media"
            )

        company_name = extracted_data.get("company")
        if company_name and company_name != "Desconocida":
            sector = get_sector_for_company(company_name)
            if sector:
                extracted_data["sector"] = sector
            size = get_company_size(company_name)
            if size:
                extracted_data["company_size"] = size

        articles.append(
            Article(
                id=article_id,
                source="google_news",
                url=item["link"],
                title=item["title"],
                description=item["snippet"],
                published_at=published_at,
                extracted_data=extracted_data,
            )
        )

    bo_results = [item for item in bo_raw["results"] if item.get("relevant")]
    for item in bo_results:
        published_at = parse_bo_date(item["date"])
        article_id = generate_article_id("boletin_oficial", item["detail_url"])
        full_text = f"{item['entity']} {item['rubro']} {item['description']}"
        extracted_data = extract_entities_from_text(full_text)

        company_name = item["entity"]
        extracted_data["company"] = company_name
        extracted_data.setdefault("confidence", {})["company"] = "alta"
        extracted_data["country"] = "argentina"
        extracted_data.setdefault("confidence", {})["country"] = "alta"

        sector = get_sector_for_company(company_name)
        if sector:
            extracted_data["sector"] = sector
        size = get_company_size(company_name)
        if size:
            extracted_data["company_size"] = size

        articles.append(
            Article(
                id=article_id,
                source="boletin_oficial",
                url=item["detail_url"],
                title=f"{item['entity']} — {item['rubro']}",
                published_at=published_at,
                content=item["description"],
                extracted_data=extracted_data,
            )
        )

    for item in nicho_raw["results"]:
        published_at = parse_google_date(item["date"])
        article_id = generate_article_id(item["source_file"], item["link"])
        extracted_data = extract_entities_from_title_and_snippet(
            item["title"],
            item.get("snippet", ""),
        )
        stored = dict(item.get("extracted_data", {}))

        for key, value in stored.items():
            if key == "confidence":
                stored_confidence = value if isinstance(value, dict) else {}
                extracted_data.setdefault("confidence", {}).update(
                    {
                        conf_key: conf_value
                        for conf_key, conf_value in stored_confidence.items()
                        if conf_key not in extracted_data.get("confidence", {})
                    }
                )
            elif not extracted_data.get(key):
                extracted_data[key] = value

        catalog_country = extracted_data.get("country")
        country = infer_country(
            source=item["source_file"],
            company=extracted_data.get("company"),
            url=item["link"],
            catalog_country=catalog_country,
        )
        if country:
            extracted_data["country"] = country
            extracted_data.setdefault("confidence", {})["country"] = (
                "alta" if catalog_country else "media"
            )
        elif not extracted_data.get("country"):
            extracted_data["country"] = "argentina"
            extracted_data.setdefault("confidence", {})["country"] = "media"

        company_name = extracted_data.get("company")
        if company_name and company_name != "Desconocida":
            sector = get_sector_for_company(company_name)
            if sector:
                extracted_data["sector"] = sector
            size = get_company_size(company_name)
            if size:
                extracted_data["company_size"] = size

        articles.append(
            Article(
                id=article_id,
                source=item["source_file"],
                url=item["link"],
                title=item["title"],
                description=item["snippet"],
                published_at=published_at,
                extracted_data=extracted_data,
            )
        )

    event_list = group_articles_into_events(articles)

    companies_by_pattern = sorted(
        {
            article.extracted_data["company"]
            for article in articles
            if article.extracted_data.get("confidence", {}).get("company") == "media"
            and article.extracted_data.get("company")
            and article.extracted_data.get("company") != "Desconocida"
        }
    )

    run_metrics = {
        "cnv_articles": len(cnv_raw["results"]),
        "google_articles": len(google_raw["results"]),
        "boletin_oficial_articles": len(bo_results),
        "revistas_nicho_articles": len(nicho_raw["results"]),
        "total_articles": len(articles),
        "total_events": len(event_list),
        "grouping_window_days": GROUPING_WINDOW_DAYS,
        "companies_by_pattern": companies_by_pattern,
    }

    current_run = Run(
        id=sha256(datetime.now(UTC).isoformat().encode()).hexdigest(),
        status="success",
        metrics=run_metrics,
        snapshot_path=OUTPUT.relative_to(ROOT).as_posix(),
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(
            {
                "generated_at": datetime.now(UTC).isoformat(),
                "year": datetime.now(UTC).year,
                "source_counts": {
                    "cnv": len(cnv_raw["results"]),
                    "google_news": len(google_raw["results"]),
                    "boletin_oficial": len(bo_results),
                    "revistas_nicho": len(nicho_raw["results"]),
                },
                "result_count": len(event_list),
                "results": [event.model_dump(mode="json") for event in event_list],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"Resultado unificado: {len(event_list)} eventos")
    print(f"Guardado en {OUTPUT.relative_to(ROOT)}")

    return current_run


if __name__ == "__main__":
    run_pipeline()
