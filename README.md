# Medical Graph RAG

A hierarchical knowledge graph system for medical domain using Graph-based Retrieval Augmented Generation (RAG).

## 🫀 NEW: CardioGraph React Frontend

**A modern, cardiovascular-themed React application is now available!**

### Quick Start
```bash
# Automated startup (recommended)
./start-cardiograph.sh

# Or manual startup:
# Terminal 1 - Backend
python -m uvicorn graph_rag.api:app --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend
cd frontend && npm run dev
```

### Access
- **CardioGraph UI**: http://localhost:3000 (React + Vite + TailwindCSS)
- **API Backend**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### Features
- 🫀 **Cardiovascular Theme**: Custom red gradient design with heartbeat animations
- 📊 **Interactive Dashboard**: Real-time metrics and entity distribution
- 🔍 **Smart Query**: Natural language queries with graph visualization
- 📁 **Multi-Format Ingestion**: Drag & drop for PDF, DOCX, TXT, HTML, JSON, CSV, XML, MD, RTF
- 🕸️ **Graph Explorer**: Interactive force-directed graph with entity filtering
- ⚙️ **Settings Panel**: Database management and system configuration

See [CARDIOGRAPH_README.md](CARDIOGRAPH_README.md) for detailed frontend documentation.

---

## Quick Links
- 📚 [Supported File Formats](docs/SUPPORTED_FORMATS.md) - PDF, Word, HTML, CSV, JSON, XML, RTF, and more
- 🖥️ [Web UI Guide](#web-ui) - Modern interface with graph visualization
- 💻 [CLI Reference](#cli) - Command-line tools

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Medical Graph RAG System                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Documents → Chunks → Occurrences → Canonical Entities           │
│                                                                   │
│  Graph Schema:                                                    │
│  ┌──────────┐    ┌───────┐    ┌────────────┐    ┌─────────────┐ │
│  │ Document │--->│ Chunk │--->│ Occurrence │--->│ Canonical   │ │
│  │          │    │       │    │ (mention)  │    │ Entity      │ │
│  └──────────┘    └───────┘    └────────────┘    └─────────────┘ │
│       │              │                               │    │     │
│       │         ┌────┴────┐                    ┌─────┴────┐    │
│       └─────────│ :NEXT   │                    │:RELATES_TO│    │
│                 │ (chain) │                    │ (semantic)│    │
│                 └─────────┘                    └──────────┘    │
│                                                                   │
├─────────────────────────────────────────────────────────────────┤
│  Entity Types: DISEASE, DRUG, GENE, PROTEIN, SYMPTOM,           │
│                PROCEDURE, ANATOMY, ORGANISM, CHEMICAL, BIOMARKER │
│                                                                   │
│  Relation Types: TREATS, CAUSES, ASSOCIATED_WITH, TARGETS,       │
│                  INHIBITS, ACTIVATES, DIAGNOSES, PREVENTS        │
└─────────────────────────────────────────────────────────────────┘
```

## Features

- **Hierarchical Knowledge Graph**: Separates entity mentions (occurrences) from canonical entities for proper deduplication
- **LLM-Powered Extraction**: Uses Ollama for entity and relation extraction from medical text
- **Vector + Graph Search**: Combines semantic similarity with graph traversal for rich retrieval
- **Multi-Format Support**: Ingest PDF, Word, HTML, CSV, JSON, XML, RTF, Markdown, and text files
- **Web UI**: Modern Streamlit interface with graph visualization for ingestion and querying
- **CLI**: Command-line tools for automation

## Prerequisites

1. **Neo4j** (v5.x+)
   ```bash
   docker run -d --name neo4j \
     -p 7474:7474 -p 7687:7687 \
     -e NEO4J_AUTH=neo4j/graphrag123 \
     neo4j:5
   ```

2. **Ollama**
   ```bash
   # Install Ollama: https://ollama.ai
   ollama serve
   ollama pull llama3.2
   ```

## Installation

```bash
# Clone and install
cd Graph-RAG
pip install -e .

# Or with dev dependencies
pip install -e ".[dev]"
```

## Configuration

Create a `.env` file:

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=graphrag123

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
CHUNK_SIZE=512
CHUNK_OVERLAP=50
```

## Usage

### Supported File Formats

The system supports ingestion from multiple document formats:
- **Text**: `.txt`, `.md` (Markdown)
- **PDF**: `.pdf`
- **Word**: `.docx`, `.doc`
- **Web**: `.html`, `.htm`
- **Data**: `.csv`, `.json`, `.xml`
- **Rich Text**: `.rtf`

### CLI

```bash
# Initialize database schema
graph-rag init

# Ingest documents (auto-detects format)
graph-rag ingest data/medical_docs/
graph-rag ingest data/research_paper.pdf
graph-rag ingest data/clinical_trial.docx

# Query the knowledge graph
graph-rag query "What are the treatments for diabetes?"

# Show statistics
graph-rag stats

# Clear database
graph-rag clear --yes
```

### Web UI

```bash
# Run modern web interface with graph visualization
streamlit run graph_rag/webapp.py
```

Then open http://localhost:8501

**Web UI Features:**
- 📊 Dashboard with real-time statistics
- 🔍 Interactive query interface with graph visualization
- 📥 Multi-format document upload (drag & drop)
- 🕸️ Graph explorer with entity neighborhoods
- ⚙️ Settings and database management

### Python API

```python
from graph_rag.config import get_settings
from graph_rag.database import Neo4jClient
from graph_rag.llm import OllamaClient
from graph_rag.embeddings import EmbeddingService
from graph_rag.kg_builder import KnowledgeGraphBuilder
from graph_rag.retriever import GraphRAG

settings = get_settings()

# Initialize clients
db = Neo4jClient(settings.neo4j_uri, settings.neo4j_user, settings.neo4j_password)
llm = OllamaClient(settings.ollama_base_url, settings.ollama_model)
embeddings = EmbeddingService(settings.embedding_model)

# Build knowledge graph
builder = KnowledgeGraphBuilder(db, llm, embeddings)
builder.ingest_text(
    text="Metformin is a first-line treatment for type 2 diabetes...",
    title="Diabetes Treatment Guidelines"
)

# Query
rag = GraphRAG(db, llm, embeddings)
result = rag.query("What drug treats type 2 diabetes?")
print(result.answer)
```

## Graph Schema

### Nodes

| Label | Description | Properties |
|-------|-------------|------------|
| Document | Source document | id, title, source, metadata |
| Chunk | Text segment | id, text, index, embedding |
| Occurrence | Entity mention | id, text, entity_type, context, confidence |
| CanonicalEntity | Deduplicated entity | id, name, entity_type, aliases, embedding |

### Relationships

| Type | From | To | Description |
|------|------|-----|-------------|
| HAS_CHUNK | Document | Chunk | Document contains chunk |
| NEXT | Chunk | Chunk | Sequential order |
| HAS_OCCURRENCE | Chunk | Occurrence | Chunk contains mention |
| REFERS_TO | Occurrence | CanonicalEntity | Mention refers to entity |
| RELATES_TO | CanonicalEntity | CanonicalEntity | Semantic relation |

## Retrieval Flow

1. **Query Embedding**: Convert question to vector
2. **Vector Search**: Find similar chunks and entities
3. **Graph Traversal**: Explore entity neighborhoods (1-2 hops)
4. **Context Building**: Aggregate entities, relations, and text
5. **LLM Generation**: Answer using retrieved context

## Project Structure

```
graph_rag/
├── __init__.py       # Package metadata
├── config.py         # Configuration management
├── models.py         # Domain models (Entity, Chunk, etc.)
├── database.py       # Neo4j client
├── llm.py            # Ollama client & entity extractor
├── embeddings.py     # Sentence transformer embeddings
├── chunker.py        # Text chunking
├── kg_builder.py     # Knowledge graph construction
├── retriever.py      # Graph traversal & RAG
├── cli.py            # CLI interface
└── ui.py             # Streamlit web UI
```

## License

MIT
