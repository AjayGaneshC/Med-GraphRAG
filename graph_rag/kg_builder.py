"""Knowledge Graph builder - orchestrates entity extraction and graph construction."""
from __future__ import annotations

import logging
from typing import List, Optional, Dict, Set, Tuple
from uuid import uuid4

from .models import (
    Document, Chunk, Occurrence, CanonicalEntity, Relation,
    EntityType, RelationType, ExtractionResult
)
from .database import Neo4jClient
from .llm import OllamaClient, EntityExtractor
from .chunker import TextChunker
from .embeddings import EmbeddingService

logger = logging.getLogger(__name__)


class CanonicalResolver:
    """Resolve entity mentions to canonical entities with deduplication."""
    
    def __init__(self, embedding_service: EmbeddingService, similarity_threshold: float = 0.85):
        self.embeddings = embedding_service
        self.threshold = similarity_threshold
        self._cache: Dict[str, CanonicalEntity] = {}  # name -> canonical entity
    
    def _normalize_name(self, name: str) -> str:
        """Normalize entity name for matching."""
        return name.lower().strip()
    
    def resolve(
        self, 
        mention: str, 
        entity_type: EntityType,
        existing_entities: List[CanonicalEntity]
    ) -> Tuple[CanonicalEntity, bool]:
        """
        Resolve a mention to a canonical entity.
        Returns (entity, is_new) tuple.
        """
        normalized = self._normalize_name(mention)
        
        # Check cache first
        cache_key = f"{normalized}:{entity_type.value}"
        if cache_key in self._cache:
            return self._cache[cache_key], False
        
        # Try exact match
        for entity in existing_entities:
            if entity.entity_type != entity_type:
                continue
            if self._normalize_name(entity.name) == normalized:
                self._cache[cache_key] = entity
                return entity, False
            for alias in entity.aliases:
                if self._normalize_name(alias) == normalized:
                    self._cache[cache_key] = entity
                    return entity, False
        
        # Try semantic similarity
        if existing_entities:
            mention_embedding = self.embeddings.embed(mention)
            best_match = None
            best_score = 0.0
            
            for entity in existing_entities:
                if entity.entity_type != entity_type:
                    continue
                if entity.embedding:
                    score = self.embeddings.similarity(mention_embedding, entity.embedding)
                    if score > best_score:
                        best_score = score
                        best_match = entity
            
            if best_match and best_score >= self.threshold:
                # Add as alias
                if mention not in best_match.aliases:
                    best_match.aliases.append(mention)
                self._cache[cache_key] = best_match
                return best_match, False
        
        # Create new canonical entity
        new_entity = CanonicalEntity(
            id=f"entity_{uuid4().hex[:12]}",
            name=mention,
            entity_type=entity_type,
            aliases=[],
            description="",
            occurrence_count=1,
            embedding=self.embeddings.embed(mention),
        )
        self._cache[cache_key] = new_entity
        return new_entity, True
    
    def clear_cache(self):
        """Clear the resolution cache."""
        self._cache.clear()


class KnowledgeGraphBuilder:
    """Build and populate the knowledge graph."""
    
    def __init__(
        self,
        db_client: Neo4jClient,
        ollama_client: OllamaClient,
        embedding_service: EmbeddingService,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
    ):
        self.db = db_client
        self.extractor = EntityExtractor(ollama_client)
        self.embeddings = embedding_service
        self.chunker = TextChunker(chunk_size, chunk_overlap)
        self.resolver = CanonicalResolver(embedding_service)
    
    def _store_document(self, doc: Document) -> None:
        """Store document node."""
        query = """
        MERGE (d:Document {id: $id})
        SET d.title = $title,
            d.source = $source,
            d.metadata = $metadata
        """
        self.db.execute_write(query, {
            "id": doc.id,
            "title": doc.title,
            "source": doc.source,
            "metadata": str(doc.metadata),
        })
    
    def _store_chunk(self, chunk: Chunk) -> None:
        """Store chunk node and link to document."""
        query = """
        MATCH (d:Document {id: $doc_id})
        MERGE (c:Chunk {id: $id})
        SET c.text = $text,
            c.index = $index,
            c.start_char = $start_char,
            c.end_char = $end_char,
            c.embedding = $embedding
        MERGE (d)-[:HAS_CHUNK]->(c)
        """
        self.db.execute_write(query, {
            "id": chunk.id,
            "doc_id": chunk.doc_id,
            "text": chunk.text,
            "index": chunk.index,
            "start_char": chunk.start_char,
            "end_char": chunk.end_char,
            "embedding": chunk.embedding,
        })
    
    def _link_chunks_sequential(self, chunks: List[Chunk]) -> None:
        """Create NEXT relationships between sequential chunks."""
        for i in range(len(chunks) - 1):
            query = """
            MATCH (c1:Chunk {id: $id1}), (c2:Chunk {id: $id2})
            MERGE (c1)-[:NEXT]->(c2)
            """
            self.db.execute_write(query, {
                "id1": chunks[i].id,
                "id2": chunks[i + 1].id,
            })
    
    def _store_occurrence(self, occ: Occurrence) -> None:
        """Store occurrence node and link to chunk."""
        query = """
        MATCH (c:Chunk {id: $chunk_id})
        MERGE (o:Occurrence {id: $id})
        SET o.text = $text,
            o.entity_type = $entity_type,
            o.start_char = $start_char,
            o.end_char = $end_char,
            o.confidence = $confidence,
            o.context = $context
        MERGE (c)-[:HAS_OCCURRENCE]->(o)
        """
        self.db.execute_write(query, {
            "id": occ.id,
            "chunk_id": occ.chunk_id,
            "text": occ.text,
            "entity_type": occ.entity_type.value,
            "start_char": occ.start_char,
            "end_char": occ.end_char,
            "confidence": occ.confidence,
            "context": occ.context,
        })
    
    def _store_canonical_entity(self, entity: CanonicalEntity) -> None:
        """Store or update canonical entity."""
        query = """
        MERGE (e:CanonicalEntity {id: $id})
        SET e.name = $name,
            e.entity_type = $entity_type,
            e.aliases = $aliases,
            e.description = $description,
            e.occurrence_count = $occurrence_count,
            e.embedding = $embedding
        """
        self.db.execute_write(query, {
            "id": entity.id,
            "name": entity.name,
            "entity_type": entity.entity_type.value,
            "aliases": entity.aliases,
            "description": entity.description,
            "occurrence_count": entity.occurrence_count,
            "embedding": entity.embedding,
        })
    
    def _link_occurrence_to_canonical(self, occ_id: str, canonical_id: str) -> None:
        """Link occurrence to canonical entity."""
        query = """
        MATCH (o:Occurrence {id: $occ_id}), (e:CanonicalEntity {id: $canonical_id})
        MERGE (o)-[:REFERS_TO]->(e)
        """
        self.db.execute_write(query, {
            "occ_id": occ_id,
            "canonical_id": canonical_id,
        })
    
    def _store_relation(self, relation: Relation) -> None:
        """Store relation between canonical entities."""
        query = """
        MATCH (e1:CanonicalEntity {id: $source_id}), (e2:CanonicalEntity {id: $target_id})
        MERGE (e1)-[r:RELATES_TO {id: $id}]->(e2)
        SET r.type = $relation_type,
            r.confidence = $confidence,
            r.evidence_chunk_ids = $evidence_chunk_ids
        """
        self.db.execute_write(query, {
            "id": relation.id,
            "source_id": relation.source_id,
            "target_id": relation.target_id,
            "relation_type": relation.relation_type.value,
            "confidence": relation.confidence,
            "evidence_chunk_ids": relation.evidence_chunk_ids,
        })
    
    def _get_existing_entities(self, entity_type: Optional[EntityType] = None) -> List[CanonicalEntity]:
        """Fetch existing canonical entities from database."""
        if entity_type:
            query = """
            MATCH (e:CanonicalEntity {entity_type: $type})
            RETURN e.id as id, e.name as name, e.entity_type as entity_type,
                   e.aliases as aliases, e.embedding as embedding
            """
            results = self.db.execute_read(query, {"type": entity_type.value})
        else:
            query = """
            MATCH (e:CanonicalEntity)
            RETURN e.id as id, e.name as name, e.entity_type as entity_type,
                   e.aliases as aliases, e.embedding as embedding
            """
            results = self.db.execute_read(query)
        
        entities = []
        for r in results:
            entities.append(CanonicalEntity(
                id=r["id"],
                name=r["name"],
                entity_type=EntityType(r["entity_type"]),
                aliases=r["aliases"] or [],
                embedding=r["embedding"],
            ))
        return entities
    
    def ingest_document(self, doc: Document) -> Dict:
        """Ingest a document into the knowledge graph."""
        logger.info(f"Ingesting document: {doc.title} ({doc.id})")
        
        stats = {
            "document_id": doc.id,
            "chunks": 0,
            "occurrences": 0,
            "new_entities": 0,
            "relations": 0,
        }
        
        # Store document
        self._store_document(doc)
        
        # Chunk document
        chunks = self.chunker.chunk(doc.content, doc.id)
        logger.info(f"Created {len(chunks)} chunks")
        
        # Generate embeddings for chunks
        chunk_texts = [c.text for c in chunks]
        chunk_embeddings = self.embeddings.embed_batch(chunk_texts)
        for chunk, embedding in zip(chunks, chunk_embeddings):
            chunk.embedding = embedding
        
        # Store chunks
        for chunk in chunks:
            self._store_chunk(chunk)
            stats["chunks"] += 1
        
        # Link sequential chunks
        self._link_chunks_sequential(chunks)
        
        # Extract entities and relations from each chunk
        name_to_canonical: Dict[str, CanonicalEntity] = {}
        all_relations: List[Tuple[str, str, RelationType, float, str]] = []
        
        for chunk in chunks:
            logger.info(f"Processing chunk {chunk.index + 1}/{len(chunks)}")
            
            # Extract using LLM
            extraction = self.extractor.extract(chunk.text, chunk.id)
            
            # Get existing entities for resolution
            existing_entities = self._get_existing_entities()
            
            # Process extracted entities
            for ent_data in extraction.entities:
                entity_type = EntityType(ent_data["type"])
                mention = ent_data["name"]
                
                # Resolve to canonical entity
                canonical, is_new = self.resolver.resolve(
                    mention, entity_type, existing_entities
                )
                
                if is_new:
                    self._store_canonical_entity(canonical)
                    existing_entities.append(canonical)
                    stats["new_entities"] += 1
                else:
                    # Update occurrence count
                    canonical.occurrence_count += 1
                    self._store_canonical_entity(canonical)
                
                name_to_canonical[mention.lower()] = canonical
                
                # Create occurrence
                occurrence = Occurrence(
                    id=f"occ_{uuid4().hex[:12]}",
                    chunk_id=chunk.id,
                    text=mention,
                    entity_type=entity_type,
                    start_char=ent_data.get("start", 0),
                    end_char=ent_data.get("end", len(mention)),
                    confidence=0.9,
                    context=chunk.text[:200],
                    canonical_id=canonical.id,
                )
                self._store_occurrence(occurrence)
                self._link_occurrence_to_canonical(occurrence.id, canonical.id)
                stats["occurrences"] += 1
            
            # Collect relations
            for rel_data in extraction.relations:
                source_name = rel_data["source"].lower()
                target_name = rel_data["target"].lower()
                rel_type = RelationType(rel_data["type"])
                confidence = rel_data.get("confidence", 0.8)
                all_relations.append((source_name, target_name, rel_type, confidence, chunk.id))
        
        # Process relations
        for source_name, target_name, rel_type, confidence, chunk_id in all_relations:
            source_entity = name_to_canonical.get(source_name)
            target_entity = name_to_canonical.get(target_name)
            
            if source_entity and target_entity:
                relation = Relation(
                    id=f"rel_{uuid4().hex[:12]}",
                    source_id=source_entity.id,
                    target_id=target_entity.id,
                    relation_type=rel_type,
                    confidence=confidence,
                    evidence_chunk_ids=[chunk_id],
                )
                self._store_relation(relation)
                stats["relations"] += 1
        
        logger.info(f"Ingestion complete: {stats}")
        return stats
    
    def ingest_text(self, text: str, title: str = "Untitled", source: str = "") -> Dict:
        """Convenience method to ingest raw text."""
        doc = Document(
            id=f"doc_{uuid4().hex[:12]}",
            title=title,
            content=text,
            source=source,
        )
        return self.ingest_document(doc)
