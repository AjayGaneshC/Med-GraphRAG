"""Graph traversal and retrieval for RAG queries."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple

from .database import Neo4jClient
from .embeddings import EmbeddingService
from .llm import OllamaClient
from .models import CanonicalEntity, EntityType

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """Result from graph retrieval."""
    query: str
    entities: List[Dict[str, Any]]
    chunks: List[Dict[str, Any]]
    subgraph: List[Dict[str, Any]]  # Edges with source, target, type
    context: str  # Aggregated context for LLM


@dataclass
class QueryResult:
    """Final answer with sources."""
    query: str
    answer: str
    sources: List[Dict[str, Any]]
    entities_found: List[str]


class GraphRetriever:
    """Retrieve relevant context from knowledge graph."""
    
    def __init__(
        self,
        db_client: Neo4jClient,
        embedding_service: EmbeddingService,
        top_k_chunks: int = 5,
        top_k_entities: int = 10,
        traversal_depth: int = 2,
    ):
        self.db = db_client
        self.embeddings = embedding_service
        self.top_k_chunks = top_k_chunks
        self.top_k_entities = top_k_entities
        self.traversal_depth = traversal_depth
    
    def _vector_search_chunks(self, query_embedding: List[float], top_k: int) -> List[Dict]:
        """Search chunks by vector similarity."""
        # Try both possible index names
        for index_name in ['chunk_embedding_index', 'chunk_embedding']:
            query = f"""
            CALL db.index.vector.queryNodes('{index_name}', $top_k, $embedding)
            YIELD node, score
            MATCH (d:Document)-[:HAS_CHUNK]->(node)
            RETURN node.id as id, node.text as text, node.index as chunk_index,
                   d.id as doc_id, d.title as doc_title, score
            ORDER BY score DESC
            """
            try:
                results = self.db.execute_read(query, {
                    "top_k": top_k,
                    "embedding": query_embedding,
                })
                return [dict(r) for r in results]
            except Exception as e:
                continue
        logger.warning("Vector search failed for chunks (no index found)")
        return []
    
    def _vector_search_entities(self, query_embedding: List[float], top_k: int) -> List[Dict]:
        """Search canonical entities by vector similarity."""
        # Try both possible index names
        for index_name in ['entity_embedding_index', 'entity_embedding']:
            query = f"""
            CALL db.index.vector.queryNodes('{index_name}', $top_k, $embedding)
            YIELD node, score
            RETURN node.id as id, node.name as name, node.entity_type as entity_type,
                   node.aliases as aliases, score
            ORDER BY score DESC
            """
            try:
                results = self.db.execute_read(query, {
                    "top_k": top_k,
                    "embedding": query_embedding,
                })
                return [dict(r) for r in results]
            except Exception as e:
                continue
        logger.warning("Entity vector search failed (no index found)")
        return []
    
    def _text_search_entities(self, keywords: List[str]) -> List[Dict]:
        """Fallback text-based entity search."""
        query = """
        MATCH (e:CanonicalEntity)
        WHERE any(kw IN $keywords WHERE 
            toLower(e.name) CONTAINS toLower(kw) OR
            any(alias IN e.aliases WHERE toLower(alias) CONTAINS toLower(kw)))
        RETURN e.id as id, e.name as name, e.entity_type as entity_type,
               e.aliases as aliases, e.occurrence_count as count
        ORDER BY e.occurrence_count DESC
        LIMIT $limit
        """
        results = self.db.execute_read(query, {
            "keywords": keywords,
            "limit": self.top_k_entities,
        })
        return [dict(r) for r in results]
    
    def _get_entity_neighborhood(self, entity_ids: List[str], depth: int = 2) -> List[Dict]:
        """Get subgraph around entities up to depth hops."""
        query = """
        MATCH (e:CanonicalEntity)
        WHERE e.id IN $entity_ids
        CALL apoc.path.subgraphAll(e, {
            relationshipFilter: 'RELATES_TO',
            maxLevel: $depth
        })
        YIELD nodes, relationships
        UNWIND relationships as r
        RETURN DISTINCT 
            startNode(r).name as source,
            startNode(r).entity_type as source_type,
            endNode(r).name as target,
            endNode(r).entity_type as target_type,
            r.type as relation_type,
            r.confidence as confidence
        """
        try:
            results = self.db.execute_read(query, {
                "entity_ids": entity_ids,
                "depth": depth,
            })
            return [dict(r) for r in results]
        except Exception as e:
            # Fallback without APOC
            logger.warning(f"APOC not available, using simple traversal: {e}")
            return self._simple_traversal(entity_ids, depth)
    
    def _simple_traversal(self, entity_ids: List[str], depth: int) -> List[Dict]:
        """Simple graph traversal without APOC."""
        if depth == 1:
            query = """
            MATCH (e1:CanonicalEntity)-[r:RELATES_TO]-(e2:CanonicalEntity)
            WHERE e1.id IN $entity_ids
            RETURN DISTINCT 
                e1.name as source, e1.entity_type as source_type,
                e2.name as target, e2.entity_type as target_type,
                r.type as relation_type, r.confidence as confidence
            """
        else:
            query = """
            MATCH path = (e1:CanonicalEntity)-[:RELATES_TO*1..2]-(e2:CanonicalEntity)
            WHERE e1.id IN $entity_ids
            UNWIND relationships(path) as r
            RETURN DISTINCT 
                startNode(r).name as source, startNode(r).entity_type as source_type,
                endNode(r).name as target, endNode(r).entity_type as target_type,
                r.type as relation_type, r.confidence as confidence
            """
        results = self.db.execute_read(query, {"entity_ids": entity_ids})
        return [dict(r) for r in results]
    
    def _get_chunks_for_entities(self, entity_ids: List[str], limit: int = 10) -> List[Dict]:
        """Get chunks that contain occurrences of given entities."""
        query = """
        MATCH (e:CanonicalEntity)<-[:REFERS_TO]-(o:Occurrence)<-[:HAS_OCCURRENCE]-(c:Chunk)<-[:HAS_CHUNK]-(d:Document)
        WHERE e.id IN $entity_ids
        RETURN DISTINCT c.id as id, c.text as text, c.index as chunk_index,
               d.id as doc_id, d.title as doc_title, e.name as entity_name
        LIMIT $limit
        """
        results = self.db.execute_read(query, {
            "entity_ids": entity_ids,
            "limit": limit,
        })
        return [dict(r) for r in results]
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract keywords from query for fallback search."""
        # Simple keyword extraction - remove common words
        stopwords = {'what', 'is', 'are', 'the', 'a', 'an', 'of', 'in', 'for', 
                     'to', 'and', 'or', 'how', 'does', 'do', 'can', 'which', 'who'}
        words = query.lower().split()
        keywords = [w for w in words if w not in stopwords and len(w) > 2]
        return keywords
    
    def _build_context(
        self, 
        chunks: List[Dict], 
        entities: List[Dict], 
        subgraph: List[Dict]
    ) -> str:
        """Build context string for LLM."""
        parts = []
        
        # Add entity information
        if entities:
            parts.append("## Relevant Medical Entities:")
            for ent in entities[:10]:
                etype = ent.get('entity_type', 'UNKNOWN')
                name = ent.get('name', '')
                parts.append(f"- {name} ({etype})")
        
        # Add relationship information
        if subgraph:
            parts.append("\n## Known Relationships:")
            for edge in subgraph[:20]:
                src = edge.get('source', '')
                tgt = edge.get('target', '')
                rel = edge.get('relation_type', 'RELATED_TO')
                parts.append(f"- {src} --[{rel}]--> {tgt}")
        
        # Add chunk text
        if chunks:
            parts.append("\n## Relevant Text Passages:")
            seen_texts = set()
            for chunk in chunks[:self.top_k_chunks]:
                text = chunk.get('text', '')[:500]
                if text not in seen_texts:
                    doc_title = chunk.get('doc_title', 'Unknown')
                    parts.append(f"\n[From: {doc_title}]\n{text}")
                    seen_texts.add(text)
        
        return "\n".join(parts)
    
    def retrieve(self, query: str) -> RetrievalResult:
        """Retrieve relevant context for a query."""
        logger.info(f"Retrieving context for: {query}")
        
        # Get query embedding
        query_embedding = self.embeddings.embed(query)
        
        # Vector search for chunks
        chunks = self._vector_search_chunks(query_embedding, self.top_k_chunks)
        
        # Vector search for entities
        entities = self._vector_search_entities(query_embedding, self.top_k_entities)
        
        # Fallback to text search if vector search returns nothing
        if not entities:
            keywords = self._extract_keywords(query)
            if keywords:
                entities = self._text_search_entities(keywords)
        
        # Get entity neighborhood
        entity_ids = [e['id'] for e in entities]
        subgraph = []
        if entity_ids:
            subgraph = self._get_entity_neighborhood(entity_ids, self.traversal_depth)
            
            # Get additional chunks from entity occurrences
            entity_chunks = self._get_chunks_for_entities(entity_ids, self.top_k_chunks)
            # Merge with vector search results (deduplicate)
            seen_ids = {c['id'] for c in chunks}
            for ec in entity_chunks:
                if ec['id'] not in seen_ids:
                    chunks.append(ec)
                    seen_ids.add(ec['id'])
        
        # Build context
        context = self._build_context(chunks, entities, subgraph)
        
        logger.info(f"Retrieved {len(entities)} entities, {len(chunks)} chunks, {len(subgraph)} relations")
        
        return RetrievalResult(
            query=query,
            entities=entities,
            chunks=chunks,
            subgraph=subgraph,
            context=context,
        )


class GraphRAG:
    """Full Graph RAG system with retrieval and generation."""
    
    ANSWER_PROMPT = """You are a medical knowledge assistant. Answer the question based ONLY on the provided context. 
If the context doesn't contain enough information, say so clearly.

CONTEXT:
{context}

QUESTION: {query}

Provide a clear, accurate answer based on the context above. Cite specific entities and relationships when relevant."""
    
    def __init__(
        self,
        db_client: Neo4jClient,
        ollama_client: OllamaClient,
        embedding_service: EmbeddingService,
        top_k_chunks: int = 5,
        top_k_entities: int = 10,
    ):
        self.retriever = GraphRetriever(
            db_client, embedding_service, top_k_chunks, top_k_entities
        )
        self.llm = ollama_client
    
    def query(self, question: str) -> QueryResult:
        """Answer a question using graph-based retrieval."""
        # Retrieve context
        retrieval = self.retriever.retrieve(question)
        
        if not retrieval.context.strip():
            return QueryResult(
                query=question,
                answer="I don't have enough information in the knowledge graph to answer this question.",
                sources=[],
                entities_found=[],
            )
        
        # Generate answer
        prompt = self.ANSWER_PROMPT.format(
            context=retrieval.context,
            query=question,
        )
        
        answer = self.llm.generate(prompt, temperature=0.3)
        
        # Collect sources
        sources = []
        for chunk in retrieval.chunks[:5]:
            sources.append({
                "text": chunk.get("text", "")[:300],
                "document": chunk.get("doc_title", "Unknown"),
                "chunk_id": chunk.get("id", ""),
            })
        
        entities_found = [e.get("name", "") for e in retrieval.entities]
        
        return QueryResult(
            query=question,
            answer=answer,
            sources=sources,
            entities_found=entities_found,
        )
