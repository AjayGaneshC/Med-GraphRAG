"""Streamlit Web UI for Medical Graph RAG."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional
import tempfile

import streamlit as st

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Must be first Streamlit command
st.set_page_config(
    page_title="Medical Graph RAG",
    page_icon="🏥",
    layout="wide",
)


def get_clients():
    """Initialize clients (cached)."""
    from graph_rag.config import get_settings
    from graph_rag.database import Neo4jClient
    from graph_rag.llm import OllamaClient
    from graph_rag.embeddings import EmbeddingService
    
    settings = get_settings()
    
    db = Neo4jClient(
        uri=settings.neo4j_uri,
        user=settings.neo4j_user,
        password=settings.neo4j_password,
    )
    
    ollama = OllamaClient(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
    )
    
    embeddings = EmbeddingService(model_name=settings.embedding_model)
    
    return db, ollama, embeddings, settings


def check_connections():
    """Check service connections."""
    db, ollama, embeddings, settings = get_clients()
    
    status = {"neo4j": False, "ollama": False, "embeddings": False}
    
    try:
        db.execute_read("RETURN 1")
        status["neo4j"] = True
    except:
        pass
    
    try:
        status["ollama"] = ollama.check_health()
    except:
        pass
    
    try:
        embeddings.embed("test")
        status["embeddings"] = True
    except:
        pass
    
    return status


def render_sidebar():
    """Render sidebar with status and navigation."""
    with st.sidebar:
        st.title("🏥 Medical Graph RAG")
        st.markdown("---")
        
        # Navigation
        page = st.radio(
            "Navigate",
            ["🔍 Query", "📥 Ingest", "📊 Explore", "⚙️ Settings"],
            label_visibility="collapsed",
        )
        
        st.markdown("---")
        
        # Status indicators
        st.subheader("System Status")
        status = check_connections()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Neo4j", "✅" if status["neo4j"] else "❌")
        with col2:
            st.metric("Ollama", "✅" if status["ollama"] else "❌")
        
        if not all(status.values()):
            st.warning("Some services are not running!")
        
        return page


def render_query_page():
    """Render the query interface."""
    st.header("🔍 Query Knowledge Graph")
    
    # Query input
    query = st.text_area(
        "Enter your medical question:",
        placeholder="e.g., What are the treatments for diabetes?",
        height=100,
    )
    
    col1, col2 = st.columns([1, 4])
    with col1:
        search_btn = st.button("🔎 Search", type="primary", use_container_width=True)
    with col2:
        show_sources = st.checkbox("Show sources", value=True)
    
    if search_btn and query:
        with st.spinner("Searching knowledge graph..."):
            try:
                from graph_rag.retriever import GraphRAG
                
                db, ollama, embeddings, _ = get_clients()
                rag = GraphRAG(db, ollama, embeddings)
                result = rag.query(query)
                
                # Display answer
                st.markdown("### Answer")
                st.markdown(result.answer)
                
                # Display entities found
                if result.entities_found:
                    st.markdown("### Entities Found")
                    entity_cols = st.columns(min(len(result.entities_found), 5))
                    for i, entity in enumerate(result.entities_found[:10]):
                        with entity_cols[i % 5]:
                            st.info(entity)
                
                # Display sources
                if show_sources and result.sources:
                    st.markdown("### Sources")
                    for i, src in enumerate(result.sources):
                        with st.expander(f"📄 {src['document']}", expanded=False):
                            st.markdown(src['text'])
                
            except Exception as e:
                st.error(f"Error: {e}")
                logger.exception("Query failed")


def render_ingest_page():
    """Render the document ingestion interface."""
    st.header("📥 Ingest Documents")
    
    tab1, tab2 = st.tabs(["📁 Upload Files", "✍️ Paste Text"])
    
    with tab1:
        uploaded_files = st.file_uploader(
            "Upload medical documents",
            type=["txt", "md"],
            accept_multiple_files=True,
        )
        
        if uploaded_files and st.button("📥 Ingest Files", type="primary"):
            with st.spinner("Processing documents..."):
                try:
                    from graph_rag.kg_builder import KnowledgeGraphBuilder
                    
                    db, ollama, embeddings, settings = get_clients()
                    builder = KnowledgeGraphBuilder(
                        db, ollama, embeddings,
                        settings.chunk_size, settings.chunk_overlap
                    )
                    
                    total_stats = {"chunks": 0, "new_entities": 0, "relations": 0}
                    progress_bar = st.progress(0)
                    
                    for i, file in enumerate(uploaded_files):
                        st.text(f"Processing: {file.name}")
                        content = file.read().decode("utf-8")
                        
                        stats = builder.ingest_text(
                            text=content,
                            title=file.name,
                            source=f"upload:{file.name}",
                        )
                        
                        for key in total_stats:
                            if key in stats:
                                total_stats[key] += stats[key]
                        
                        progress_bar.progress((i + 1) / len(uploaded_files))
                    
                    st.success(f"""
                    ✅ Ingestion complete!
                    - Chunks: {total_stats['chunks']}
                    - New Entities: {total_stats['new_entities']}
                    - Relations: {total_stats['relations']}
                    """)
                    
                except Exception as e:
                    st.error(f"Error: {e}")
                    logger.exception("Ingestion failed")
    
    with tab2:
        title = st.text_input("Document Title", placeholder="My Medical Document")
        text = st.text_area(
            "Paste document text:",
            height=300,
            placeholder="Paste medical text here...",
        )
        
        if text and st.button("📥 Ingest Text", type="primary"):
            with st.spinner("Processing text..."):
                try:
                    from graph_rag.kg_builder import KnowledgeGraphBuilder
                    
                    db, ollama, embeddings, settings = get_clients()
                    builder = KnowledgeGraphBuilder(
                        db, ollama, embeddings,
                        settings.chunk_size, settings.chunk_overlap
                    )
                    
                    stats = builder.ingest_text(
                        text=text,
                        title=title or "Pasted Document",
                        source="manual:paste",
                    )
                    
                    st.success(f"""
                    ✅ Ingestion complete!
                    - Chunks: {stats.get('chunks', 0)}
                    - New Entities: {stats.get('new_entities', 0)}
                    - Relations: {stats.get('relations', 0)}
                    """)
                    
                except Exception as e:
                    st.error(f"Error: {e}")
                    logger.exception("Ingestion failed")


def render_explore_page():
    """Render the graph exploration interface."""
    st.header("📊 Explore Knowledge Graph")
    
    db, _, _, _ = get_clients()
    
    # Statistics
    col1, col2, col3, col4 = st.columns(4)
    
    try:
        stats_query = """
        MATCH (d:Document) WITH count(d) as docs
        MATCH (c:Chunk) WITH docs, count(c) as chunks
        MATCH (e:CanonicalEntity) WITH docs, chunks, count(e) as entities
        MATCH ()-[r:RELATES_TO]->() WITH docs, chunks, entities, count(r) as relations
        RETURN docs, chunks, entities, relations
        """
        results = db.execute_read(stats_query)
        
        if results:
            r = results[0]
            col1.metric("Documents", r["docs"])
            col2.metric("Chunks", r["chunks"])
            col3.metric("Entities", r["entities"])
            col4.metric("Relations", r["relations"])
    except Exception as e:
        st.warning(f"Could not fetch statistics: {e}")
    
    st.markdown("---")
    
    # Entity browser
    st.subheader("Browse Entities")
    
    entity_types = [
        "ALL", "DISEASE", "DRUG", "GENE", "PROTEIN", "SYMPTOM",
        "PROCEDURE", "ANATOMY", "ORGANISM", "CHEMICAL", "BIOMARKER"
    ]
    
    col1, col2 = st.columns([1, 3])
    with col1:
        selected_type = st.selectbox("Filter by type", entity_types)
    with col2:
        search_term = st.text_input("Search entities", placeholder="Type to search...")
    
    try:
        if selected_type == "ALL":
            query = """
            MATCH (e:CanonicalEntity)
            WHERE $search = '' OR toLower(e.name) CONTAINS toLower($search)
            RETURN e.id as id, e.name as name, e.entity_type as type, 
                   e.occurrence_count as count, e.aliases as aliases
            ORDER BY e.occurrence_count DESC
            LIMIT 50
            """
        else:
            query = """
            MATCH (e:CanonicalEntity {entity_type: $type})
            WHERE $search = '' OR toLower(e.name) CONTAINS toLower($search)
            RETURN e.id as id, e.name as name, e.entity_type as type,
                   e.occurrence_count as count, e.aliases as aliases
            ORDER BY e.occurrence_count DESC
            LIMIT 50
            """
        
        results = db.execute_read(query, {"type": selected_type, "search": search_term or ""})
        
        if results:
            import pandas as pd
            df = pd.DataFrame(results)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No entities found")
            
    except Exception as e:
        st.warning(f"Could not fetch entities: {e}")
    
    st.markdown("---")
    
    # Relations browser
    st.subheader("Browse Relations")
    
    try:
        rel_query = """
        MATCH (e1:CanonicalEntity)-[r:RELATES_TO]->(e2:CanonicalEntity)
        RETURN e1.name as source, r.type as relation, e2.name as target,
               r.confidence as confidence
        ORDER BY r.confidence DESC
        LIMIT 50
        """
        rel_results = db.execute_read(rel_query)
        
        if rel_results:
            import pandas as pd
            df = pd.DataFrame(rel_results)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No relations found")
            
    except Exception as e:
        st.warning(f"Could not fetch relations: {e}")


def render_settings_page():
    """Render the settings page."""
    st.header("⚙️ Settings")
    
    db, ollama, _, settings = get_clients()
    
    # Current configuration
    st.subheader("Current Configuration")
    
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Neo4j URI", settings.neo4j_uri, disabled=True)
        st.text_input("Ollama URL", settings.ollama_base_url, disabled=True)
        st.text_input("Ollama Model", settings.ollama_model, disabled=True)
    
    with col2:
        st.text_input("Embedding Model", settings.embedding_model, disabled=True)
        st.number_input("Chunk Size", settings.chunk_size, disabled=True)
        st.number_input("Chunk Overlap", settings.chunk_overlap, disabled=True)
    
    st.info("Edit the .env file to change configuration")
    
    st.markdown("---")
    
    # Database actions
    st.subheader("Database Actions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔧 Initialize Schema", type="secondary"):
            with st.spinner("Initializing..."):
                try:
                    db.setup_schema()
                    st.success("Schema initialized!")
                except Exception as e:
                    st.error(f"Error: {e}")
    
    with col2:
        if st.button("🗑️ Clear Database", type="secondary"):
            if st.checkbox("I confirm I want to delete all data"):
                with st.spinner("Clearing..."):
                    try:
                        db.clear_database()
                        st.success("Database cleared!")
                    except Exception as e:
                        st.error(f"Error: {e}")
    
    st.markdown("---")
    
    # Available Ollama models
    st.subheader("Available Ollama Models")
    
    try:
        models = ollama.list_models()
        if models:
            for model in models:
                st.text(f"• {model}")
        else:
            st.warning("No models found. Pull a model with: ollama pull llama3.2")
    except Exception as e:
        st.warning(f"Could not fetch models: {e}")


def main():
    """Main application."""
    page = render_sidebar()
    
    if "🔍 Query" in page:
        render_query_page()
    elif "📥 Ingest" in page:
        render_ingest_page()
    elif "📊 Explore" in page:
        render_explore_page()
    elif "⚙️ Settings" in page:
        render_settings_page()


if __name__ == "__main__":
    main()
