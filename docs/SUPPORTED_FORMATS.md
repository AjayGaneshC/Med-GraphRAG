# Supported Document Formats

The Medical Graph RAG system supports automatic ingestion of multiple document formats.

## Supported Formats

### ✅ Text Formats
- **Plain Text** (`.txt`)
- **Markdown** (`.md`)

### ✅ Document Formats
- **PDF** (`.pdf`) - Extracts text from all pages
- **Word** (`.docx`, `.doc`) - Extracts text and tables
- **Rich Text** (`.rtf`) - Basic text extraction

### ✅ Web Formats
- **HTML** (`.html`, `.htm`) - Strips tags, keeps content
  - Automatically removes scripts, styles, navigation
  - Preserves main content structure

### ✅ Data Formats
- **CSV** (`.csv`) - Converts tabular data to text
  - Includes column names and summary statistics
  - Shows sample rows for context
  
- **JSON** (`.json`) - Structured data extraction
  - Pretty-prints structure
  - Flattens nested objects for text search
  
- **XML** (`.xml`) - Extracts text content

## Usage Examples

### CLI Ingestion

```bash
# Single file
graph-rag ingest data/research_paper.pdf
graph-rag ingest data/clinical_trial.docx
graph-rag ingest data/medications.csv

# Directory (auto-detects all supported formats)
graph-rag ingest data/medical_docs/
```

### Web UI Ingestion

1. Navigate to **📥 Ingest** tab
2. Click **Upload Files** or **Paste Text**
3. Drag & drop files or select from file picker
4. Supports all formats simultaneously
5. Real-time progress tracking

### Python API

```python
from graph_rag.document_loaders import DocumentLoader
from graph_rag.kg_builder import KnowledgeGraphBuilder

# Load any supported file
content, format_type = DocumentLoader.load_file("document.pdf")

# Or from uploaded bytes
file_bytes = uploaded_file.read()
content, format_type = DocumentLoader.load_from_bytes(
    file_bytes, 
    filename="document.pdf"
)

# Ingest into knowledge graph
builder.ingest_text(content, title="My Document")
```

## Format-Specific Features

### PDF
- Multi-page extraction
- Handles text-based PDFs (not scanned images)
- Preserves paragraph structure

### Word Documents
- Extracts main text
- Extracts tables
- Preserves formatting context

### HTML
- Removes navigation, scripts, styles
- Focuses on main content
- Cleans whitespace

### CSV
- Shows column statistics
- Includes sample rows
- Preserves relationships between columns

### JSON
- Displays structure
- Flattens nested data
- Maintains key-value context

## Testing Sample Files

The `data/` directory includes sample files for testing:

```bash
# Test different formats
graph-rag ingest data/test_medical.html    # HTML
graph-rag ingest data/test_medical.json    # JSON
graph-rag ingest data/test_medications.csv # CSV
```

## File Size Recommendations

- **Optimal**: < 10 MB per file
- **Maximum**: Up to 100 MB (may be slow)
- **Large datasets**: Split into smaller files

## Troubleshooting

### PDF Not Loading
- Ensure PDF contains text (not scanned images)
- Try converting scanned PDFs with OCR first

### Word Document Issues
- Convert `.doc` to `.docx` for better compatibility
- Some complex formatting may not preserve

### CSV/JSON Processing
- Large files (>1000 rows) are automatically truncated
- Complex nested JSON may need preprocessing

## Need More Formats?

The document loader is extensible. To add a new format:

1. Install required library
2. Add loader method in `document_loaders.py`
3. Update `load_file()` mapping
4. Test with sample files
