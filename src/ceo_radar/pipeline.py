import json
from datetime import datetime, UTC, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from hashlib import sha256

from ceo_radar.models import Article, Event, Run
from ceo_radar.utils import parse_cnv_date, parse_google_date
from ceo_radar.extraction import extract_entities_from_text, infer_country_from_source
from ceo_radar.catalogs import get_sector_for_company, get_company_size

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
OUTPUT = ROOT / ".planning" / "results" / "oportunidades_unificadas.json"

def generate_article_id(source: str, url: str) -> str:
    return sha256(f"{source}-{url}".encode()).hexdigest()

def generate_event_id(
    entities: Dict[str, Any],
    window_start: datetime,
) -> str:
    # Using a sorted string representation of entities for deterministic ID
    # Ensure 'market' is used, and include 'sector' and 'company_size' if available
    relevant_entities = {k: v for k, v in entities.items() if k in ["company", "person", "role", "change_type", "market", "sector", "company_size"] and v}
    entity_str = "-".join(f"{k}:{v}" for k, v in sorted(relevant_entities.items()) if v)
    key = f"{entity_str}-{window_start.isoformat()}"
    return sha256(key.encode()).hexdigest()

def run_pipeline() -> Run:
    cnv_raw = json.loads(CNV_INPUT.read_text(encoding="utf-8"))
    google_raw = json.loads(GOOGLE_INPUT.read_text(encoding="utf-8"))

    articles: List[Article] = []

    # Process CNV data
    for item in cnv_raw["results"]:
        published_at = parse_cnv_date(item["date"])
        article_id = generate_article_id("cnv", item["presentation_url"])
        
        # Use both description and document for entity extraction
        full_text = f"{item["description"]} {item["document"]}"
        extracted_data = extract_entities_from_text(full_text)
        
        # CNV provides company directly
        company_name = item["entity"]
        extracted_data["company"] = company_name
        
        # Infer country using full text content
        extracted_data["market"] = infer_country_from_source("cnv", full_text)

        # Enrich with sector and company size from catalogs
        if company_name:
            sector = get_sector_for_company(company_name)
            if sector: extracted_data["sector"] = sector
            size = get_company_size(company_name)
            if size: extracted_data["company_size"] = size

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

    # Process Google News data
    for item in google_raw["results"]:
        published_at = parse_google_date(item["date"])
        article_id = generate_article_id("google_news", item["link"])
        
        # Use title and snippet for entity extraction
        full_text = f"{item["title"]} {item["snippet"]}"
        extracted_data = extract_entities_from_text(full_text)
        
        # Infer country using full text content
        extracted_data["market"] = infer_country_from_source("google_news", full_text)

        # Enrich with sector and company size from catalogs if company is extracted
        company_name = extracted_data.get("company")
        if company_name and company_name != "Desconocida": # Check if a company was actually extracted
            sector = get_sector_for_company(company_name)
            if sector: extracted_data["sector"] = sector
            size = get_company_size(company_name)
            if size: extracted_data["company_size"] = size

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

    # Group articles into events
    events: Dict[str, Event] = {}
    for article in articles:
        # Determine a temporal window for event grouping (e.g., same day)
        window_start = article.published_at.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Use extracted entities for a more robust event key
        event_entities = {
            k: v for k, v in article.extracted_data.items()
            if k in ["company", "person", "role", "change_type", "market", "sector", "company_size"]
        }
        
        event_id = generate_event_id(event_entities, window_start)

        if event_id not in events:
            events[event_id] = Event(
                id=event_id,
                articles=[],
                first_seen=article.published_at,
                last_seen=article.published_at,
                entities={}
            )
        
        events[event_id].articles.append(article)
        events[event_id].first_seen = min(events[event_id].first_seen, article.published_at)
        events[event_id].last_seen = max(events[event_id].last_seen, article.published_at)
        
        # Consolidate entities from all articles in the event
        for k, v in article.extracted_data.items():
            if k in ["company", "person", "role", "change_type", "market", "sector", "company_size"] and v:
                # Simple consolidation: if the entity doesn't exist or is empty, assign it
                # For more complex cases, could implement a merge strategy (e.g., list of values)
                if not events[event_id].entities.get(k):
                    events[event_id].entities[k] = v


    # Convert events dict to list and sort
    event_list = sorted(events.values(), key=lambda e: e.last_seen, reverse=True)

    # Prepare run metrics
    run_metrics = {
        "cnv_articles": len(cnv_raw["results"]),
        "google_articles": len(google_raw["results"]),
        "total_articles": len(articles),
        "total_events": len(event_list),
    }

    # Create Run object
    current_run = Run(
        id=sha256(datetime.now(UTC).isoformat().encode()).hexdigest(),
        status="success",
        metrics=run_metrics,
        snapshot_path=OUTPUT.relative_to(ROOT).as_posix() # Store relative path
    )

    # Save unified output (for now, same as original consolidar_resultados.py)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(
            {
                "generated_at": datetime.now(UTC).isoformat(),
                "year": datetime.now(UTC).year,
                "source_counts": {
                    "cnv": len(cnv_raw["results"]),
                    "google_news": len(google_raw["results"]),
                },
                "result_count": len(event_list),
                "results": [event.model_dump(mode='json') for event in event_list], # Use model_dump for Pydantic v2
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