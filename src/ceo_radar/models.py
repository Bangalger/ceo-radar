from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class Article(BaseModel):
    id: str
    source: str
    url: str
    title: str
    description: Optional[str] = None
    published_at: datetime
    content: Optional[str] = None
    extracted_data: Dict[str, Any] = {} # {empresa, persona, rol, tipo_cambio}

class Event(BaseModel):
    id: str
    articles: List[Article]
    first_seen: datetime
    last_seen: datetime
    entities: Dict[str, Any] = {} # Consolidado de {empresa, persona, rol, tipo_cambio}
    score: float = 0.0

class Feedback(BaseModel):
    event_id: str
    user_id: str
    status: str # buen_candidato, revisar, no_relevante
    reason: Optional[str] = None
    comment: Optional[str] = None
    suggested_rule: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class Rule(BaseModel):
    id: str
    pattern: str
    action: Dict[str, Any]
    priority: int = 0
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class Run(BaseModel):
    id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    status: str # success, failed, partial
    metrics: Dict[str, Any] = {}
    snapshot_path: Optional[str] = None
