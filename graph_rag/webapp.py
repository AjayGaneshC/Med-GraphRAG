"""Modern Web UI for Medical Graph RAG System."""
from __future__ import annotations

import json
import logging
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any
import html

import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration - must be first Streamlit command
st.set_page_config(
    page_title="Medical Graph RAG",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for modern styling
CUSTOM_CSS = """
<style>
    /* Main container styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Card styling */
    .stCard {
        border-radius: 10px;
        padding: 1.5rem;
        background: linear-gradient(135deg, #2b3a4a 0%, #3f4c6b 100%);
        color: white;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #2b3a4a 0%, #202b38 100%);
        border: 1px solid #444;
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        transition: transform 0.2s;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(135deg, #81c784 0%, #a5d6a7 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #b0bec5;
        margin-top: 0.3rem;
    }
    
    /* Entity type badges */
    .entity-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 500;
        margin: 0.2rem;
    }
    
    .entity-DRUG { background-color: #4CAF50; color: white; }
    .entity-DISEASE { background-color: #f44336; color: white; }
    .entity-SYMPTOM { background-color: #FF9800; color: white; }
    .entity-GENE { background-color: #2196F3; color: white; }
    .entity-PROTEIN { background-color: #9C27B0; color: white; }
    .entity-ANATOMY { background-color: #795548; color: white; }
    .entity-PROCEDURE { background-color: #607D8B; color: white; }
    .entity-CHEMICAL { background-color: #00BCD4; color: white; }
    .entity-BIOMARKER { background-color: #E91E63; color: white; }
    .entity-ORGANISM { background-color: #8BC34A; color: white; }
    
    /* Answer box */
    .answer-box {
        background: #1e1e1e;
        border: 1px solid #333;
        border-left: 5px solid #2e7d32;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
        color: #e0e0e0 !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }
    
    .answer-box h4 {
        color: #81c784 !important;
        margin-top: 0;
        font-weight: 500;
    }
    
    .answer-box p {
        color: #e0e0e0 !important;
        font-size: 1.05rem;
        line-height: 1.6;
    }
    
    /* Source card */
    .source-card {
        background: #252526;
        border-radius: 8px;
        padding: 1.2rem;
        margin: 0.8rem 0;
        border-left: 3px solid #667eea;
        color: #e0e0e0 !important;
        border: 1px solid #333;
    }
    
    .source-card div, .source-card span, .source-card a, .source-card strong {
        color: #e0e0e0 !important;
    }
    
    /* Graph container */
    .graph-container {
        border: 1px solid #444;
        border-radius: 12px;
        padding: 1rem;
        background: #1e1e1e;
        color: #e0e0e0 !important;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Custom header */
    .custom-header {
        background: linear-gradient(135deg, #2b3a4a 0%, #3f4c6b 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 2rem;
    }
    
    /* Button overrides for less harsh styling */
    .stButton button[kind="primary"] {
        background-color: #4a5568 !important;
        color: #e2e8f0 !important;
        border-color: #2d3748 !important;
    }
    .stButton button[kind="primary"]:hover {
        background-color: #2d3748 !important;
        border-color: #1a202c !important;
    }
    
    .custom-header h1 {
        margin: 0;
        font-size: 2rem;
    }
    
    .custom-header p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
    }
</style>
"""

# Entity type colors for graph visualization
ENTITY_COLORS = {
    "DRUG": "#4CAF50",
    "DISEASE": "#f44336",
    "SYMPTOM": "#FF9800",
    "GENE": "#2196F3",
    "PROTEIN": "#9C27B0",
    "ANATOMY": "#795548",
    "PROCEDURE": "#607D8B",
    "CHEMICAL": "#00BCD4",
    "BIOMARKER": "#E91E63",
    "ORGANISM": "#8BC34A",
}

RELATION_COLORS = {
    "TREATS": "#4CAF50",
    "CAUSES": "#f44336",
    "ASSOCIATED_WITH": "#2196F3",
    "INTERACTS_WITH": "#FF9800",
    "TARGETS": "#9C27B0",
    "INHIBITS": "#E91E63",
    "ACTIVATES": "#00BCD4",
    "DIAGNOSES": "#795548",
    "PREVENTS": "#8BC34A",
    "LOCATED_IN": "#607D8B",
}


@st.cache_resource
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


def get_graph_stats() -> Dict[str, int]:
    """Get knowledge graph statistics."""
    db, _, _, _ = get_clients()
    
    try:
        query = """
        MATCH (d:Document) WITH count(d) as docs
        MATCH (c:Chunk) WITH docs, count(c) as chunks
        MATCH (o:Occurrence) WITH docs, chunks, count(o) as occurrences
        MATCH (e:CanonicalEntity) WITH docs, chunks, occurrences, count(e) as entities
        MATCH ()-[r:RELATES_TO]->() WITH docs, chunks, occurrences, entities, count(r) as relations
        RETURN docs, chunks, occurrences, entities, relations
        """
        results = db.execute_read(query)
        if results:
            return dict(results[0])
        return {"docs": 0, "chunks": 0, "occurrences": 0, "entities": 0, "relations": 0}
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        return {"docs": 0, "chunks": 0, "occurrences": 0, "entities": 0, "relations": 0}


def get_entity_type_counts() -> List[Dict]:
    """Get entity counts by type."""
    db, _, _, _ = get_clients()
    
    try:
        query = """
        MATCH (e:CanonicalEntity)
        RETURN e.entity_type as type, count(*) as count
        ORDER BY count DESC
        """
        return db.execute_read(query)
    except:
        return []


def get_entities(entity_type: Optional[str] = None, search: str = "", limit: int = 50) -> List[Dict]:
    """Get entities with optional filtering."""
    db, _, _, _ = get_clients()
    
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
            return db.execute_read(query, {"type": entity_type, "search": search, "limit": limit})
        else:
            query = """
            MATCH (e:CanonicalEntity)
            WHERE $search = '' OR toLower(e.name) CONTAINS toLower($search)
            RETURN e.id as id, e.name as name, e.entity_type as type,
                   e.occurrence_count as count, e.aliases as aliases
            ORDER BY e.occurrence_count DESC
            LIMIT $limit
            """
            return db.execute_read(query, {"search": search, "limit": limit})
    except:
        return []


def get_relations(limit: int = 100) -> List[Dict]:
    """Get relations from the graph."""
    db, _, _, _ = get_clients()
    
    try:
        query = """
        MATCH (e1:CanonicalEntity)-[r:RELATES_TO]->(e2:CanonicalEntity)
        RETURN e1.id as source_id, e1.name as source, e1.entity_type as source_type,
               e2.id as target_id, e2.name as target, e2.entity_type as target_type,
               r.type as relation_type, r.confidence as confidence
        ORDER BY r.confidence DESC
        LIMIT $limit
        """
        return db.execute_read(query, {"limit": limit})
    except:
        return []


def get_entity_neighborhood(entity_id: str, depth: int = 1) -> Dict:
    """Get entity and its neighborhood for visualization."""
    db, _, _, _ = get_clients()
    
    try:
        if depth == 1:
            query = """
            MATCH (e:CanonicalEntity {id: $id})
            OPTIONAL MATCH (e)-[r:RELATES_TO]-(e2:CanonicalEntity)
            RETURN e.id as center_id, e.name as center_name, e.entity_type as center_type,
                   collect(DISTINCT {
                       id: e2.id, name: e2.name, type: e2.entity_type,
                       relation: r.type, direction: CASE WHEN startNode(r) = e THEN 'out' ELSE 'in' END
                   }) as neighbors
            """
        else:
            query = """
            MATCH (e:CanonicalEntity {id: $id})
            OPTIONAL MATCH path = (e)-[:RELATES_TO*1..2]-(e2:CanonicalEntity)
            WITH e, e2, relationships(path) as rels
            UNWIND rels as r
            RETURN e.id as center_id, e.name as center_name, e.entity_type as center_type,
                   collect(DISTINCT {
                       id: e2.id, name: e2.name, type: e2.entity_type,
                       relation: r.type
                   }) as neighbors
            """
        
        results = db.execute_read(query, {"id": entity_id})
        if results:
            return dict(results[0])
        return {}
    except Exception as e:
        logger.error(f"Error getting neighborhood: {e}")
        return {}


def get_subgraph_for_query(entity_ids: List[str]) -> Dict:
    """Get subgraph around entities for visualization."""
    db, _, _, _ = get_clients()
    
    if not entity_ids:
        return {"nodes": [], "edges": []}
    
    try:
        query = """
        MATCH (e:CanonicalEntity)
        WHERE e.id IN $ids
        OPTIONAL MATCH (e)-[r:RELATES_TO]-(e2:CanonicalEntity)
        WHERE e2.id IN $ids OR e.id IN $ids
        WITH collect(DISTINCT e) + collect(DISTINCT e2) as all_nodes,
             collect(DISTINCT r) as all_rels
        UNWIND all_nodes as n
        WITH collect(DISTINCT {id: n.id, name: n.name, type: n.entity_type}) as nodes, all_rels
        UNWIND all_rels as r
        WITH nodes, collect(DISTINCT {
            source: startNode(r).id, 
            target: endNode(r).id, 
            type: r.type,
            confidence: r.confidence
        }) as edges
        RETURN nodes, edges
        """
        results = db.execute_read(query, {"ids": entity_ids})
        if results:
            return dict(results[0])
        return {"nodes": [], "edges": []}
    except Exception as e:
        logger.error(f"Error getting subgraph: {e}")
        return {"nodes": [], "edges": []}


def render_metric_card(value: int, label: str, icon: str = "📊"):
    """Render a styled metric card."""
    st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 1.5rem;">{icon}</div>
            <div class="metric-value">{value:,}</div>
            <div class="metric-label">{label}</div>
        </div>
    """, unsafe_allow_html=True)


def render_entity_badge(entity_type: str, name: str):
    """Render an entity type badge."""
    return f'<span class="entity-badge entity-{entity_type}">{name}</span>'


def render_graph_visualization(nodes: List[Dict], edges: List[Dict], height: int = 500):
    """Render interactive graph using streamlit-agraph."""
    if not nodes:
        st.info("No graph data to display")
        return
    
    # Create nodes
    graph_nodes = []
    for node in nodes:
        if node and node.get('id'):
            color = ENTITY_COLORS.get(node.get('type', ''), '#999999')
            graph_nodes.append(Node(
                id=node['id'],
                label=node.get('name', node['id'])[:30],
                size=25,
                color=color,
                title=f"{node.get('name', '')} ({node.get('type', 'Unknown')})",
            ))
    
    # Create edges
    graph_edges = []
    for edge in edges:
        if edge and edge.get('source') and edge.get('target'):
            color = RELATION_COLORS.get(edge.get('type', ''), '#999999')
            graph_edges.append(Edge(
                source=edge['source'],
                target=edge['target'],
                label=edge.get('type', ''),
                color=color,
                width=2,
            ))
    
    # Graph configuration
    config = Config(
        width="100%",
        height=height,
        directed=True,
        physics=True,
        hierarchical=False,
        nodeHighlightBehavior=True,
        highlightColor="#F7A7A6",
        collapsible=False,
        node={'labelProperty': 'label'},
        link={'labelProperty': 'label', 'renderLabel': True}
    )
    
    return agraph(nodes=graph_nodes, edges=graph_edges, config=config)


def render_sidebar():
    """Render sidebar navigation."""
    with st.sidebar:
        st.markdown("""
            <div style="text-align: center; padding: 1rem;">
                <h1 style="margin: 0;">🏥</h1>
                <h2 style="margin: 0.5rem 0;">Medical Graph RAG</h2>
                <p style="color: #666; font-size: 0.9rem;">Knowledge Graph System</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        # Navigation
        page = st.radio(
            "Navigation",
            options=["🏠 Dashboard", "🔍 Query", "📥 Ingest", "🕸️ Graph Explorer", "⚙️ Settings"],
            label_visibility="collapsed",
        )
        
        st.divider()
        
        # Quick stats
        stats = get_graph_stats()
        st.markdown("### 📊 Quick Stats")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Entities", stats.get('entities', 0))
            st.metric("Documents", stats.get('docs', 0))
        with col2:
            st.metric("Relations", stats.get('relations', 0))
            st.metric("Chunks", stats.get('chunks', 0))
        
        st.divider()
        
        # System status
        st.markdown("### 🔌 System Status")
        db, ollama, _, _ = get_clients()
        
        try:
            db.execute_read("RETURN 1")
            st.success("Neo4j Connected")
        except:
            st.error("Neo4j Disconnected")
        
        try:
            if ollama.check_health():
                st.success("Ollama Connected")
            else:
                st.warning("Ollama Not Running")
        except:
            st.warning("Ollama Not Running")
        
        return page


def render_dashboard():
    """Render the main dashboard."""
    st.markdown("""
        <div class="custom-header">
            <h1>🏠 Dashboard</h1>
            <p>Overview of your Medical Knowledge Graph</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Stats row
    stats = get_graph_stats()
    cols = st.columns(5)
    
    metrics = [
        (stats.get('docs', 0), "Documents", "📄"),
        (stats.get('chunks', 0), "Chunks", "📝"),
        (stats.get('occurrences', 0), "Mentions", "🏷️"),
        (stats.get('entities', 0), "Entities", "🔬"),
        (stats.get('relations', 0), "Relations", "🔗"),
    ]
    
    for col, (value, label, icon) in zip(cols, metrics):
        with col:
            render_metric_card(value, label, icon)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Entity type distribution
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 📊 Entities by Type")
        type_counts = get_entity_type_counts()
        if type_counts:
            import pandas as pd
            df = pd.DataFrame(type_counts)
            st.bar_chart(df.set_index('type')['count'])
        else:
            st.info("No entities in the graph yet")
    
    with col2:
        st.markdown("### 🔝 Top Entities")
        entities = get_entities(limit=10)
        if entities:
            for ent in entities:
                badge = render_entity_badge(ent['type'], ent['type'])
                st.markdown(f"{badge} **{ent['name']}** ({ent.get('count', 0)} mentions)", unsafe_allow_html=True)
        else:
            st.info("No entities in the graph yet")
    
    # Recent relations
    st.markdown("### 🔗 Sample Relations")
    relations = get_relations(limit=10)
    if relations:
        for rel in relations:
            src_badge = render_entity_badge(rel['source_type'], rel['source'])
            tgt_badge = render_entity_badge(rel['target_type'], rel['target'])
            st.markdown(
                f"{src_badge} → **{rel['relation_type']}** → {tgt_badge}",
                unsafe_allow_html=True
            )
    else:
        st.info("No relations in the graph yet")


def render_query_page():
    """Render the query interface."""
    st.markdown("""
        <div class="custom-header">
            <h1>🔍 Query Knowledge Graph</h1>
            <p>Ask questions about your medical knowledge base</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Query input
    query = st.text_area(
        "Enter your question:",
        placeholder="e.g., What are the treatments for type 2 diabetes? What drug interactions should I be aware of with statins?",
        height=100,
        key="query_input"
    )
    
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        search_btn = st.button("🔎 Search", type="primary", use_container_width=True)
    with col2:
        show_graph = st.checkbox("Show Graph", value=True)
    with col3:
        show_sources = st.checkbox("Show Sources", value=True)
    
    if search_btn and query:
        with st.spinner("🔍 Searching knowledge graph..."):
            try:
                from graph_rag.retriever import GraphRAG
                
                db, ollama, embeddings, _ = get_clients()
                rag = GraphRAG(db, ollama, embeddings)
                result = rag.query(query)
                
                # Display answer
                st.markdown(f"""
                    <div class="answer-box">
                        <h4>💡 Answer</h4>
                        <p>{html.escape(result.answer)}</p>
                    </div>
                """, unsafe_allow_html=True)
                
                # Display entities found
                if result.entities_found:
                    st.markdown("### 🏷️ Entities Found")
                    badges = " ".join([
                        f'<span class="entity-badge entity-DRUG">{html.escape(e)}</span>'
                        for e in result.entities_found[:15]
                    ])
                    st.markdown(badges, unsafe_allow_html=True)
                
                # Display graph visualization
                if show_graph and result.entities_found:
                    st.markdown("### 🕸️ Knowledge Graph Context")
                    
                    # Get entity IDs for visualization
                    entities = get_entities(search="", limit=100)
                    entity_name_to_id = {e['name'].lower(): e['id'] for e in entities}
                    
                    found_ids = []
                    for name in result.entities_found:
                        if name.lower() in entity_name_to_id:
                            found_ids.append(entity_name_to_id[name.lower()])
                    
                    if found_ids:
                        subgraph = get_subgraph_for_query(found_ids[:20])
                        if subgraph.get('nodes'):
                            render_graph_visualization(
                                subgraph.get('nodes', []),
                                subgraph.get('edges', []),
                                height=400
                            )
                
                # Display sources
                if show_sources and result.sources:
                    st.markdown("### 📚 Sources")
                    for i, src in enumerate(result.sources, 1):
                        with st.expander(f"📄 {src.get('document', 'Unknown')} (Source {i})"):
                            st.markdown(f"```\n{src.get('text', '')[:500]}...\n```")
                
            except Exception as e:
                st.error(f"Query failed: {e}")
                logger.exception("Query error")


def render_ingest_page():
    """Render the document ingestion interface."""
    st.markdown("""
        <div class="custom-header">
            <h1>📥 Ingest Documents</h1>
            <p>Add medical documents to your knowledge graph</p>
        </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📁 Upload Files", "✍️ Paste Text"])
    
    with tab1:
        st.markdown("### Upload Medical Documents")
        st.markdown("**Supported formats:** PDF, Word (docx/doc), Text (txt/md), HTML, CSV, JSON, XML, RTF")
        
        uploaded_files = st.file_uploader(
            "Choose files",
            type=["txt", "md", "pdf", "docx", "doc", "html", "htm", "csv", "json", "xml", "rtf"],
            accept_multiple_files=True,
            key="file_uploader"
        )
        
        if uploaded_files:
            st.info(f"📁 {len(uploaded_files)} file(s) selected")
            
            if st.button("📥 Start Ingestion", type="primary", key="ingest_files"):
                from graph_rag.kg_builder import KnowledgeGraphBuilder
                from graph_rag.document_loaders import DocumentLoader
                
                db, ollama, embeddings, settings = get_clients()
                builder = KnowledgeGraphBuilder(
                    db, ollama, embeddings,
                    settings.chunk_size, settings.chunk_overlap
                )
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                total_stats = {"chunks": 0, "new_entities": 0, "relations": 0, "occurrences": 0}
                errors = []
                
                for i, file in enumerate(uploaded_files):
                    status_text.text(f"Processing: {file.name}")
                    
                    try:
                        # Load file based on type
                        file_bytes = file.read()
                        content, format_type = DocumentLoader.load_from_bytes(file_bytes, file.name)
                        
                        if not content.strip():
                            errors.append(f"⚠️ {file.name}: No text content extracted")
                            continue
                        
                        stats = builder.ingest_text(
                            text=content,
                            title=file.name,
                            source=f"upload:{file.name}",
                        )
                        
                        for key in total_stats:
                            if key in stats:
                                total_stats[key] += stats[key]
                    except Exception as e:
                        errors.append(f"❌ {file.name}: {str(e)[:100]}")
                        logger.exception(f"Failed to process {file.name}")
                    
                    progress_bar.progress((i + 1) / len(uploaded_files))
                
                status_text.empty()
                
                # Show errors if any
                if errors:
                    with st.expander(f"⚠️ {len(errors)} file(s) had issues", expanded=False):
                        for error in errors:
                            st.warning(error)
                
                st.success(f"""
                    ✅ **Ingestion Complete!**
                    - Chunks created: {total_stats['chunks']}
                    - Entity mentions: {total_stats.get('occurrences', 0)}
                    - New entities: {total_stats['new_entities']}
                    - Relations: {total_stats['relations']}
                """)
                
                st.balloons()
    
    with tab2:
        st.markdown("### Paste Medical Text")
        
        title = st.text_input("Document Title", placeholder="Enter a title for this document")
        
        text = st.text_area(
            "Document Content",
            placeholder="Paste your medical text here...\n\nExample: Metformin is the first-line treatment for type 2 diabetes...",
            height=300,
            key="paste_text"
        )
        
        if st.button("📥 Ingest Text", type="primary", key="ingest_text"):
            if not text.strip():
                st.warning("Please enter some text to ingest")
            else:
                from graph_rag.kg_builder import KnowledgeGraphBuilder
                
                db, ollama, embeddings, settings = get_clients()
                builder = KnowledgeGraphBuilder(
                    db, ollama, embeddings,
                    settings.chunk_size, settings.chunk_overlap
                )
                
                with st.spinner("Processing document..."):
                    try:
                        stats = builder.ingest_text(
                            text=text,
                            title=title or "Pasted Document",
                            source="manual:paste",
                        )
                        
                        st.success(f"""
                            ✅ **Ingestion Complete!**
                            - Chunks created: {stats.get('chunks', 0)}
                            - Entity mentions: {stats.get('occurrences', 0)}
                            - New entities: {stats.get('new_entities', 0)}
                            - Relations: {stats.get('relations', 0)}
                        """)
                        st.balloons()
                    except Exception as e:
                        st.error(f"Ingestion failed: {e}")


def render_graph_explorer():
    """Render the graph exploration interface."""
    st.markdown("""
        <div class="custom-header">
            <h1>🕸️ Graph Explorer</h1>
            <p>Explore and visualize your knowledge graph</p>
        </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["🔬 Entity Explorer", "🔗 Relations", "🌐 Full Graph"])
    
    with tab1:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("### Filter Entities")
            
            entity_types = ["ALL", "DRUG", "DISEASE", "SYMPTOM", "GENE", "PROTEIN", 
                          "ANATOMY", "PROCEDURE", "CHEMICAL", "BIOMARKER", "ORGANISM"]
            selected_type = st.selectbox("Entity Type", entity_types)
            
            search_term = st.text_input("Search", placeholder="Search entities...")
            
            entities = get_entities(
                entity_type=selected_type if selected_type != "ALL" else None,
                search=search_term,
                limit=50
            )
            
            st.markdown(f"### Results ({len(entities)})")
            
            selected_entity = None
            for ent in entities:
                badge = render_entity_badge(ent['type'], ent['type'])
                if st.button(f"🔍 {ent['name']}", key=f"ent_{ent['id']}", use_container_width=True):
                    selected_entity = ent
                    st.session_state['selected_entity'] = ent
        
        with col2:
            st.markdown("### Entity Neighborhood")
            
            if 'selected_entity' in st.session_state:
                ent = st.session_state['selected_entity']
                
                st.markdown(f"""
                    **Name:** {ent['name']}  
                    **Type:** {ent['type']}  
                    **Mentions:** {ent.get('count', 0)}
                """)
                
                neighborhood = get_entity_neighborhood(ent['id'], depth=1)
                
                if neighborhood and neighborhood.get('neighbors'):
                    # Build nodes and edges for visualization
                    nodes = [{'id': ent['id'], 'name': ent['name'], 'type': ent['type']}]
                    edges = []
                    
                    for neighbor in neighborhood['neighbors']:
                        if neighbor and neighbor.get('id'):
                            nodes.append({
                                'id': neighbor['id'],
                                'name': neighbor['name'],
                                'type': neighbor['type']
                            })
                            
                            if neighbor.get('direction') == 'out':
                                edges.append({
                                    'source': ent['id'],
                                    'target': neighbor['id'],
                                    'type': neighbor.get('relation', '')
                                })
                            else:
                                edges.append({
                                    'source': neighbor['id'],
                                    'target': ent['id'],
                                    'type': neighbor.get('relation', '')
                                })
                    
                    render_graph_visualization(nodes, edges, height=400)
                else:
                    st.info("No connections found for this entity")
            else:
                st.info("👈 Select an entity from the list to view its connections")
    
    with tab2:
        st.markdown("### Browse Relations")
        
        relations = get_relations(limit=50)
        
        if relations:
            import pandas as pd
            df = pd.DataFrame(relations)
            df = df[['source', 'relation_type', 'target', 'source_type', 'target_type', 'confidence']]
            df.columns = ['Source', 'Relation', 'Target', 'Source Type', 'Target Type', 'Confidence']
            
            st.dataframe(df, use_container_width=True, height=400)
        else:
            st.info("No relations in the graph yet")
    
    with tab3:
        st.markdown("### Full Knowledge Graph")
        st.warning("⚠️ Large graphs may be slow to render")
        
        max_nodes = st.slider("Maximum nodes", 10, 200, 50)
        
        if st.button("🔄 Load Graph", type="primary"):
            db, _, _, _ = get_clients()
            
            try:
                # Get nodes
                node_query = """
                MATCH (e:CanonicalEntity)
                RETURN e.id as id, e.name as name, e.entity_type as type
                ORDER BY e.occurrence_count DESC
                LIMIT $limit
                """
                nodes = db.execute_read(node_query, {"limit": max_nodes})
                
                if nodes:
                    node_ids = [n['id'] for n in nodes]
                    
                    # Get edges
                    edge_query = """
                    MATCH (e1:CanonicalEntity)-[r:RELATES_TO]->(e2:CanonicalEntity)
                    WHERE e1.id IN $ids AND e2.id IN $ids
                    RETURN e1.id as source, e2.id as target, r.type as type
                    """
                    edges = db.execute_read(edge_query, {"ids": node_ids})
                    
                    render_graph_visualization(nodes, edges, height=600)
                else:
                    st.info("No entities in the graph yet")
            except Exception as e:
                st.error(f"Failed to load graph: {e}")


def render_settings_page():
    """Render the settings page."""
    st.markdown("""
        <div class="custom-header">
            <h1>⚙️ Settings</h1>
            <p>Configure your Graph RAG system</p>
        </div>
    """, unsafe_allow_html=True)
    
    db, ollama, embeddings, settings = get_clients()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🗄️ Database Configuration")
        st.text_input("Neo4j URI", settings.neo4j_uri, disabled=True)
        st.text_input("Neo4j User", settings.neo4j_user, disabled=True)
        st.text_input("Neo4j Password", "••••••••", disabled=True, type="password")
    
    with col2:
        st.markdown("### 🤖 LLM Configuration")
        st.text_input("Ollama URL", settings.ollama_base_url, disabled=True)
        st.text_input("Model", settings.ollama_model, disabled=True)
        st.text_input("Embedding Model", settings.embedding_model, disabled=True)
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📝 Processing Settings")
        st.number_input("Chunk Size", value=settings.chunk_size, disabled=True)
        st.number_input("Chunk Overlap", value=settings.chunk_overlap, disabled=True)
    
    with col2:
        st.markdown("### 🔧 Available Ollama Models")
        try:
            models = ollama.list_models()
            if models:
                for model in models[:10]:
                    st.text(f"• {model}")
            else:
                st.warning("No models found")
        except:
            st.warning("Could not fetch models")
    
    st.divider()
    
    st.markdown("### 🛠️ Database Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔧 Initialize Schema", use_container_width=True):
            with st.spinner("Initializing..."):
                try:
                    db.setup_schema()
                    st.success("Schema initialized!")
                except Exception as e:
                    st.error(f"Error: {e}")
    
    with col2:
        if st.button("📊 Refresh Stats", use_container_width=True):
            st.cache_resource.clear()
            st.rerun()
    
    with col3:
        if st.button("🗑️ Clear Database", type="secondary", use_container_width=True):
            st.warning("⚠️ This will delete ALL data!")
            if st.checkbox("I understand, delete everything"):
                if st.button("Confirm Delete", type="primary"):
                    try:
                        db.clear_database()
                        st.success("Database cleared!")
                        st.cache_resource.clear()
                    except Exception as e:
                        st.error(f"Error: {e}")
    
    st.divider()
    
    st.markdown("### ℹ️ About")
    st.markdown("""
        **Medical Graph RAG v0.2.0**
        
        A hierarchical knowledge graph system for medical domain using:
        - **Neo4j** for graph storage
        - **Ollama** for LLM-based extraction
        - **Sentence Transformers** for embeddings
        
        [View Documentation](https://github.com/your-repo/graph-rag)
    """)


def main():
    """Main application entry point."""
    # Inject custom CSS
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    
    # Render sidebar and get current page
    page = render_sidebar()
    
    # Render appropriate page
    if "Dashboard" in page:
        render_dashboard()
    elif "Query" in page:
        render_query_page()
    elif "Ingest" in page:
        render_ingest_page()
    elif "Graph" in page:
        render_graph_explorer()
    elif "Settings" in page:
        render_settings_page()


if __name__ == "__main__":
    main()
