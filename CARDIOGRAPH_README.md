# CardioGraph - Cardiovascular Medical Knowledge Graph System

## Overview

A modern, full-stack medical knowledge graph system with a cardiovascular-themed React frontend and FastAPI backend, designed for extracting and querying medical entities and relationships from documents.

## Architecture

### Backend (FastAPI)
- **Location**: `/home/crackedengineer/Ajay-Codes/Graph-RAG/graph_rag/api.py`
- **Port**: 8000
- **Database**: Neo4j 5.x (bolt://localhost:7687)
- **LLM**: Ollama (llama3:latest)
- **Embeddings**: sentence-transformers/all-MiniLM-L6-v2

### Frontend (React + Vite)
- **Location**: `/home/crackedengineer/Ajay-Codes/Graph-RAG/frontend`
- **Port**: 3000
- **Framework**: React 18 with Vite
- **Styling**: TailwindCSS with custom cardiovascular theme
- **Animations**: Framer Motion
- **Visualization**: react-force-graph-2d

## Cardiovascular Theme Design

### Color Palette
- **Primary Red**: #dc2626 (Deep cardiovascular red)
- **Secondary**: #b91c1c (Darker red)
- **Accent**: #f87171 (Light red)
- **Danger**: #7f1d1d (Very dark red)
- **Pulse**: #ef4444 (Bright red)

### Custom Animations
- **Heartbeat**: Pulsating animation for heart icons (1.2s infinite)
- **Blood Flow**: Flowing gradient effect for active elements
- **Pulse Indicator**: Ring pulse effect for status indicators
- **Smooth Transitions**: Framer Motion for page transitions

### Visual Elements
- Heart icon with heartbeat animation in header
- Gradient backgrounds (red-900 to gray-900)
- Custom scrollbar with red theme
- Animated metric cards with hover effects
- Status indicators with pulse effects

## Features

### 1. Dashboard
- **Real-time Metrics**: Documents, chunks, entities, relations
- **Entity Distribution**: Breakdown by type (10 entity types)
- **System Vitals**: Occurrences, entity types, connections
- **Auto-refresh**: Updates every 60 seconds
- **Health Status**: Real-time system health monitoring

### 2. Query Interface
- **Natural Language**: Ask questions in plain English
- **Graph Visualization**: Interactive force-directed graph
- **Context Display**: Supporting evidence from knowledge graph
- **Real-time Results**: Powered by graph traversal + LLM

### 3. Document Ingestion
- **Multi-format Support**: PDF, DOCX, TXT, HTML, JSON, CSV, XML, MD, RTF
- **Drag & Drop**: Intuitive file upload
- **Text Paste**: Direct text input
- **Progress Feedback**: Real-time ingestion status
- **Batch Upload**: Multiple files simultaneously

### 4. Graph Explorer
- **Entity Browser**: Filter by 10 entity types
- **Interactive Graph**: Click nodes to explore neighborhoods
- **Entity List**: Searchable, filterable entity catalog
- **Graph Controls**: Adjust max nodes, refresh data
- **Type Filtering**: DRUG, DISEASE, SYMPTOM, GENE, PROTEIN, etc.

### 5. Settings Panel
- **Schema Initialization**: Create/update database schema
- **Clear Database**: Reset all data (with confirmation)
- **System Configuration**: View backend settings
- **Database Management**: Direct Neo4j control

## Entity Types (Medical Domain)

1. **DRUG**: Medications and pharmaceuticals
2. **DISEASE**: Medical conditions
3. **SYMPTOM**: Clinical symptoms
4. **GENE**: Genetic entities
5. **PROTEIN**: Protein molecules
6. **PROCEDURE**: Medical procedures
7. **ANATOMY**: Anatomical structures
8. **ORGANISM**: Biological organisms
9. **CHEMICAL**: Chemical compounds
10. **BIOMARKER**: Biological markers

## Relationship Types

1. TREATS
2. CAUSES
3. ASSOCIATED_WITH
4. TARGETS
5. INHIBITS
6. ACTIVATES
7. DIAGNOSES
8. PREVENTS
9. INTERACTS_WITH
10. LOCATED_IN
11. PART_OF
12. PRODUCES

## Technology Stack

### Frontend
- **React 18**: Modern hooks-based architecture
- **Vite**: Lightning-fast build tool and HMR
- **TailwindCSS 3**: Utility-first CSS framework
- **Framer Motion**: Production-ready animation library
- **Axios**: Promise-based HTTP client
- **Lucide React**: Beautiful icon library
- **React Force Graph 2D**: WebGL-powered graph visualization

### Backend
- **FastAPI**: Modern Python web framework
- **Neo4j**: Graph database
- **Ollama**: Local LLM inference
- **Sentence Transformers**: Semantic embeddings
- **Python 3.13**: Latest Python runtime

## Running the System

### Start Backend
```bash
cd /home/crackedengineer/Ajay-Codes/Graph-RAG
python -m uvicorn graph_rag.api:app --host 0.0.0.0 --port 8000 --reload
```

### Start Frontend
```bash
cd /home/crackedengineer/Ajay-Codes/Graph-RAG/frontend
npm run dev
```

### Access Points
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Neo4j Browser**: http://localhost:7474

## API Endpoints

### Core Operations
- `GET /api/health` - System health check
- `GET /api/stats` - Knowledge graph statistics
- `POST /api/query` - Natural language query
- `POST /api/ingest/files` - Upload files
- `POST /api/ingest/text` - Ingest text
- `GET /api/entities` - Browse entities
- `GET /api/graph/subgraph` - Get graph data
- `GET /api/graph/entity/{id}` - Entity neighborhood
- `POST /api/database/init` - Initialize schema
- `DELETE /api/database/clear` - Clear database

## UI Components

### Sidebar
- Navigation menu with icons
- Active page indicator
- Health status indicator
- Real-time entity/relation counts
- Cardiovascular branding

### Dashboard
- 4 metric cards (documents, chunks, entities, relations)
- Entity distribution grid
- System vitals display
- Refresh button
- Loading states

### Query
- Search input with heart icon
- Submit button with animation
- Answer display section
- Supporting context cards
- Graph visualization panel

### Ingest
- Tab switcher (files/text)
- Drag & drop zone
- File list with remove
- Text area input
- Progress feedback
- Success/error messages

### Explorer
- Entity type filter buttons
- Scrollable entity list
- Large graph visualization
- Node click handlers
- Adjustable node count
- Color-coded entities

### Settings
- Initialize schema button
- Clear database with confirmation
- System configuration display
- Warning indicators
- Action feedback

## Development Notes

### State Management
- React hooks (useState, useEffect)
- Props passing for data flow
- API service layer abstraction
- Loading and error states

### Styling Approach
- TailwindCSS utility classes
- Custom theme extensions
- Responsive breakpoints
- Dark mode optimized
- Accessibility friendly

### Performance
- Code splitting
- Lazy loading
- Optimized re-renders
- Debounced inputs
- Efficient graph rendering

### Code Organization
```
frontend/
├── src/
│   ├── components/     # React components
│   │   ├── Dashboard.jsx
│   │   ├── Query.jsx
│   │   ├── Ingest.jsx
│   │   ├── Explorer.jsx
│   │   ├── SettingsPanel.jsx
│   │   └── Sidebar.jsx
│   ├── services/       # API layer
│   │   └── api.js
│   ├── App.jsx         # Main app component
│   ├── main.jsx        # Entry point
│   └── index.css       # Global styles
├── tailwind.config.js  # Tailwind configuration
├── vite.config.js      # Vite configuration
└── package.json        # Dependencies
```

## Customization

### Changing Colors
Edit `/frontend/tailwind.config.js` to modify the cardiovascular color palette.

### Adding Entity Types
Update the `entityTypes` array in Explorer.jsx and add corresponding colors.

### Modifying Animations
Edit keyframes in `/frontend/src/index.css` for custom animations.

## Future Enhancements

- [ ] User authentication
- [ ] Saved queries
- [ ] Export graph data
- [ ] Advanced filters
- [ ] Real-time collaboration
- [ ] Mobile app
- [ ] PDF report generation
- [ ] Multi-language support
- [ ] Custom entity types
- [ ] Graph analytics dashboard

## Support

For issues or questions about the CardioGraph system, check:
- Backend logs: Terminal running FastAPI
- Frontend console: Browser developer tools
- Neo4j logs: Docker container logs
- Ollama logs: Ollama service logs

## License

This project is part of the Graph RAG medical knowledge graph system.
