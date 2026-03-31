"""
Domain models for the Medical Graph RAG system.

Graph Schema:
=============
(Document)-[:HAS_CHUNK]->(Chunk)
(Chunk)-[:NEXT]->(Chunk)
(Chunk)-[:HAS_OCCURRENCE]->(Occurrence)
(Occurrence)-[:REFERS_TO]->(CanonicalEntity)
(CanonicalEntity)-[:RELATES_TO {type}]->(CanonicalEntity)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class EntityType(str, Enum):
    """Medical entity types."""
    DISEASE = "DISEASE"
    DRUG = "DRUG"
    GENE = "GENE"
    PROTEIN = "PROTEIN"
    SYMPTOM = "SYMPTOM"
    PROCEDURE = "PROCEDURE"
    ANATOMY = "ANATOMY"
    ORGANISM = "ORGANISM"
    CHEMICAL = "CHEMICAL"
    BIOMARKER = "BIOMARKER"


class RelationType(str, Enum):
    """Relation types between entities."""
    TREATS = "TREATS"
    CAUSES = "CAUSES"
    ASSOCIATED_WITH = "ASSOCIATED_WITH"
    CONTRAINDICATED = "CONTRAINDICATED"
    INTERACTS_WITH = "INTERACTS_WITH"
    TARGETS = "TARGETS"
    INHIBITS = "INHIBITS"
    ACTIVATES = "ACTIVATES"
    DIAGNOSES = "DIAGNOSES"
    PREVENTS = "PREVENTS"
    LOCATED_IN = "LOCATED_IN"
    PRODUCES = "PRODUCES"


@dataclass
class Document:
    """A source document."""
    id: str
    title: str
    content: str
    source: str = ""
    metadata: dict = field(default_factory=dict)


@dataclass
class Chunk:
    """A text chunk from a document."""
    id: str
    doc_id: str
    text: str
    index: int
    start_char: int
    end_char: int
    embedding: Optional[List[float]] = None


@dataclass
class Occurrence:
    """An entity occurrence (mention) in a specific chunk."""
    id: str
    chunk_id: str
    text: str  # The exact text mention
    entity_type: EntityType
    start_char: int
    end_char: int
    confidence: float
    context: str  # Surrounding sentence/context
    canonical_id: Optional[str] = None  # Link to canonical entity


@dataclass
class CanonicalEntity:
    """A canonical (deduplicated) entity."""
    id: str
    name: str  # Normalized name
    entity_type: EntityType
    aliases: List[str] = field(default_factory=list)
    description: str = ""
    occurrence_count: int = 0
    embedding: Optional[List[float]] = None


@dataclass
class Relation:
    """A relation between two canonical entities."""
    id: str
    source_id: str
    target_id: str
    relation_type: RelationType
    confidence: float
    evidence_chunk_ids: List[str] = field(default_factory=list)


@dataclass
class ExtractionResult:
    """Result from LLM entity/relation extraction."""
    entities: List[dict]
    relations: List[dict]
    chunk_id: str
