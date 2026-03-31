"""FastAPI backend for Medical Graph RAG web application."""
from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from graph_rag.config import get_settings
from graph_rag.database import Neo4jClient
from graph_rag.llm import OllamaClient
from graph_rag.embeddings import EmbeddingService
from graph_rag.kg_builder import KnowledgeGraphBuilder
from graph_rag.retriever import GraphRAG
from graph_rag.document_loaders import DocumentLoader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Medical Graph RAG API", version="0.2.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:3003", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global clients (initialized on startup)
db_client: Optional[Neo4jClient] = None
ollama_client: Optional[OllamaClient] = None
embedding_service: Optional[EmbeddingService] = None
settings = None


@app.on_event("startup")
async def startup():
    """Initialize clients on startup."""
    global db_client, ollama_client, embedding_service, settings
    
    settings = get_settings()
    
    db_client = Neo4jClient(
        uri=settings.neo4j_uri,
        user=settings.neo4j_user,
        password=settings.neo4j_password,
    )
    
    ollama_client = OllamaClient(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
    )
    
    embedding_service = EmbeddingService(model_name=settings.embedding_model)
    
    logger.info("Application started successfully")


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown."""
    if db_client:
        db_client.close()
    if ollama_client:
        ollama_client.close()


# Pydantic models
class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    query: str
    answer: str
    entities_found: List[str]
    sources: List[dict]


class StatsResponse(BaseModel):
    documents: int
    chunks: int
    occurrences: int
    entities: int
    relations: int
    entity_types: List[dict]


class EntityResponse(BaseModel):
    id: str
    name: str
    type: str
    count: int
    aliases: List[str]


class GraphData(BaseModel):
    nodes: List[dict]
    edges: List[dict]


# API Endpoints
@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main HTML page."""
    html_file = Path(__file__).parent / "static" / "index.html"
    if html_file.exists():
        return FileResponse(html_file)
    return HTMLResponse("<h1>Medical Graph RAG</h1><p>API is running. Frontend not found.</p>")


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    neo4j_ok = False
    ollama_ok = False
    
    try:
        db_client.execute_read("RETURN 1")
        neo4j_ok = True
    except:
        pass
    
    try:
        ollama_ok = ollama_client.check_health()
    except:
        pass
    
    return {
        "status": "healthy" if (neo4j_ok and ollama_ok) else "degraded",
        "neo4j": "connected" if neo4j_ok else "disconnected",
        "ollama": "connected" if ollama_ok else "disconnected",
    }


@app.get("/api/stats", response_model=StatsResponse)
async def get_stats():
    """Get knowledge graph statistics."""
    try:
        query = """
        MATCH (d:Document) WITH count(d) as docs
        MATCH (c:Chunk) WITH docs, count(c) as chunks
        MATCH (o:Occurrence) WITH docs, chunks, count(o) as occurrences
        MATCH (e:CanonicalEntity) WITH docs, chunks, occurrences, count(e) as entities
        MATCH ()-[r:RELATES_TO]->() WITH docs, chunks, occurrences, entities, count(r) as relations
        RETURN docs, chunks, occurrences, entities, relations
        """
        results = db_client.execute_read(query)
        stats = dict(results[0]) if results else {}
        
        # Get entity type counts
        type_query = """
        MATCH (e:CanonicalEntity)
        RETURN e.entity_type as type, count(*) as count
        ORDER BY count DESC
        """
        entity_types = db_client.execute_read(type_query)
        
        return StatsResponse(
            documents=stats.get('docs', 0),
            chunks=stats.get('chunks', 0),
            occurrences=stats.get('occurrences', 0),
            entities=stats.get('entities', 0),
            relations=stats.get('relations', 0),
            entity_types=entity_types or []
        )
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/query", response_model=QueryResponse)
async def query_graph(request: QueryRequest):
    """Query the knowledge graph."""
    try:
        rag = GraphRAG(db_client, ollama_client, embedding_service)
        result = rag.query(request.query)
        
        return QueryResponse(
            query=result.query,
            answer=result.answer,
            entities_found=result.entities_found,
            sources=result.sources
        )
    except Exception as e:
        logger.error(f"Query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ingest/files")
async def ingest_files(files: List[UploadFile] = File(...)):
    """Ingest uploaded files."""
    try:
        builder = KnowledgeGraphBuilder(
            db_client, ollama_client, embedding_service,
            settings.chunk_size, settings.chunk_overlap
        )
        
        total_stats = {"chunks": 0, "new_entities": 0, "relations": 0, "occurrences": 0}
        errors = []
        
        for file in files:
            try:
                content_bytes = await file.read()
                content, format_type = DocumentLoader.load_from_bytes(
                    content_bytes, file.filename
                )
                
                if not content.strip():
                    errors.append(f"{file.filename}: No text content extracted")
                    continue
                
                stats = builder.ingest_text(
                    text=content,
                    title=file.filename,
                    source=f"upload:{file.filename}",
                )
                
                for key in total_stats:
                    if key in stats:
                        total_stats[key] += stats[key]
            except Exception as e:
                errors.append(f"{file.filename}: {str(e)[:100]}")
                logger.exception(f"Failed to process {file.filename}")
        
        return {
            "success": True,
            "files_processed": len(files) - len(errors),
            "stats": total_stats,
            "errors": errors
        }
    except Exception as e:
        logger.error(f"Ingestion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ingest/text")
async def ingest_text(title: str = Form(...), content: str = Form(...)):
    """Ingest text content."""
    try:
        builder = KnowledgeGraphBuilder(
            db_client, ollama_client, embedding_service,
            settings.chunk_size, settings.chunk_overlap
        )
        
        stats = builder.ingest_text(
            text=content,
            title=title,
            source="manual:paste",
        )
        
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Text ingestion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/entities")
async def get_entities(
    entity_type: Optional[str] = None,
    search: str = "",
    limit: int = 50
):
    """Get entities with optional filtering."""
    try:
        if entity_type and entity_type != "ALL":
            query = """
            MATCH (e:CanonicalEntity {entity_type: $type})
            WHERE $search = '' OR toLower(e.name) CONTAINS toLower($search)
            RETURN e.id as id, e.name as name, e.entity_type as type,
                   e.occurrence_count as count, e.aliases as aliases
            ORDER BY e.occurrence_count DESC
            LIMIT $limit
            """
            results = db_client.execute_read(query, {"type": entity_type, "search": search, "limit": limit})
        else:
            query = """
            MATCH (e:CanonicalEntity)
            WHERE $search = '' OR toLower(e.name) CONTAINS toLower($search)
            RETURN e.id as id, e.name as name, e.entity_type as type,
                   e.occurrence_count as count, e.aliases as aliases
            ORDER BY e.occurrence_count DESC
            LIMIT $limit
            """
            results = db_client.execute_read(query, {"search": search, "limit": limit})
        
        return {"entities": results}
    except Exception as e:
        logger.error(f"Error getting entities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/graph/subgraph")
async def get_subgraph(max_nodes: int = 50, entity_ids: str = None):
    """Get subgraph around entities or random subgraph."""
    try:
        if entity_ids:
            # Get subgraph for specific entities
            ids = entity_ids.split(",")
            
            query = """
            MATCH (e:CanonicalEntity)
            WHERE e.id IN $ids
            OPTIONAL MATCH (e)-[r:RELATES_TO]-(e2:CanonicalEntity)
            WHERE e2.id IN $ids OR e.id IN $ids
            WITH collect(DISTINCT e) + collect(DISTINCT e2) as all_nodes,
                 collect(DISTINCT r) as all_rels
            UNWIND all_nodes as n
            WITH collect(DISTINCT {id: n.id, labels: labels(n), properties: properties(n)}) as nodes, all_rels
            UNWIND all_rels as r
            WITH nodes, collect(DISTINCT {
                start: startNode(r).id, 
                end: endNode(r).id, 
                type: type(r),
                properties: properties(r)
            }) as edges
            RETURN nodes, edges
            """
            results = db_client.execute_read(query, {"ids": ids})
        else:
            # Get random subgraph with max_nodes
            query = """
            MATCH (e:CanonicalEntity)
            WITH e LIMIT $max_nodes
            MATCH (e)-[r:RELATES_TO]-(e2:CanonicalEntity)
            WITH collect(DISTINCT e) + collect(DISTINCT e2) as all_nodes,
                 collect(DISTINCT r) as all_rels
            UNWIND all_nodes as n
            WITH collect(DISTINCT {id: n.id, labels: labels(n), properties: properties(n)}) as nodes, all_rels
            UNWIND all_rels as r
            WITH nodes, collect(DISTINCT {
                start: startNode(r).id, 
                end: endNode(r).id, 
                type: type(r),
                properties: properties(r)
            }) as edges
            RETURN nodes, edges
            """
            results = db_client.execute_read(query, {"max_nodes": max_nodes})
        
        if results:
            return dict(results[0])
        return {"nodes": [], "edges": []}
    except Exception as e:
        logger.error(f"Error getting subgraph: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/graph/entity/{entity_id}")
async def get_entity_neighborhood(entity_id: str):
    """Get entity neighborhood."""
    try:
        query = """
        MATCH (e:CanonicalEntity {id: $id})
        OPTIONAL MATCH (e)-[r:RELATES_TO]-(e2:CanonicalEntity)
        WITH e, collect(DISTINCT {
            id: e2.id, 
            name: e2.name, 
            type: e2.entity_type,
            relation: r.type,
            direction: CASE WHEN startNode(r) = e THEN 'out' ELSE 'in' END
        }) as neighbors
        RETURN e.id as id, e.name as name, e.entity_type as type, neighbors
        """
        results = db_client.execute_read(query, {"id": entity_id})
        
        if results:
            data = dict(results[0])
            # Build graph data
            nodes = [{"id": data["id"], "name": data["name"], "type": data["type"]}]
            edges = []
            
            for neighbor in data.get("neighbors", []):
                if neighbor and neighbor.get("id"):
                    nodes.append({
                        "id": neighbor["id"],
                        "name": neighbor["name"],
                        "type": neighbor["type"]
                    })
                    
                    if neighbor.get("direction") == "out":
                        edges.append({
                            "source": data["id"],
                            "target": neighbor["id"],
                            "type": neighbor.get("relation", ""),
                            "label": neighbor.get("relation", "")
                        })
                    else:
                        edges.append({
                            "source": neighbor["id"],
                            "target": data["id"],
                            "type": neighbor.get("relation", ""),
                            "label": neighbor.get("relation", "")
                        })
            
            return GraphData(nodes=nodes, edges=edges)
        
        raise HTTPException(status_code=404, detail="Entity not found")
    except Exception as e:
        logger.error(f"Error getting entity neighborhood: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/database/init")
async def init_database():
    """Initialize database schema."""
    try:
        db_client.setup_schema()
        return {"success": True, "message": "Schema initialized"}
    except Exception as e:
        logger.error(f"Schema init error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/database/clear")
async def clear_database():
    """Clear all data from database."""
    try:
        db_client.clear_database()
        return {"success": True, "message": "Database cleared"}
    except Exception as e:
        logger.error(f"Clear database error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Mount static files
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
