# Multi-Format Document Support - Changelog

## Added Features

### New Document Loaders
Added comprehensive support for multiple document formats through new `document_loaders.py` module:

#### Text Formats
- ✅ Plain text (`.txt`)
- ✅ Markdown (`.md`)

#### Document Formats
- ✅ PDF (`.pdf`) - Full text extraction from all pages
- ✅ Word Documents (`.docx`, `.doc`) - Text and table extraction
- ✅ Rich Text Format (`.rtf`) - Basic text extraction

#### Web Formats
- ✅ HTML (`.html`, `.htm`) - Content extraction with tag removal
- ✅ XML (`.xml`) - Text content extraction

#### Data Formats
- ✅ CSV (`.csv`) - Tabular data with statistics
- ✅ JSON (`.json`) - Structured data with nested support

### Updated Components

1. **Web UI (`graph_rag/webapp.py`)**
   - Updated file uploader to accept all formats
   - Enhanced error handling with detailed feedback
   - Shows format-specific processing status

2. **CLI (`graph_rag/cli.py`)**
   - Auto-detection of all supported file types
   - Format-aware error reporting
   - Progress tracking for multi-format batches

3. **Dependencies (`pyproject.toml`)**
   - Added `pypdf>=4.0` for PDF processing
   - Added `python-docx>=1.1` for Word documents
   - Added `beautifulsoup4>=4.12` and `lxml>=5.1` for HTML/XML
   - Added `openpyxl>=3.1` for potential Excel support

4. **Documentation**
   - Updated `README.md` with format support info
   - Created `docs/SUPPORTED_FORMATS.md` with comprehensive guide
   - Added quick links section to README

### Test Files
Created sample files for testing:
- `data/test_medical.html` - Aspirin information
- `data/test_medical.json` - Lisinopril drug data
- `data/test_medications.csv` - Common medications table

## Usage Examples

### CLI
```bash
# Ingest any supported format
graph-rag ingest data/research.pdf
graph-rag ingest data/clinical_trial.docx
graph-rag ingest data/medications.csv

# Auto-detect all formats in directory
graph-rag ingest data/medical_docs/
```

### Web UI
- Navigate to 📥 Ingest tab
- Upload PDF, Word, HTML, CSV, JSON, XML, RTF files
- Drag & drop multiple formats simultaneously

### Python API
```python
from graph_rag.document_loaders import DocumentLoader

# Load any format
content, format_type = DocumentLoader.load_file("document.pdf")

# From bytes (for uploads)
content, fmt = DocumentLoader.load_from_bytes(file_bytes, "doc.pdf")
```

## Statistics After Testing

Knowledge Graph now contains:
- **4 Documents** (txt, html, json from different formats)
- **194 Canonical Entities** (92 drugs, 32 diseases, 23 symptoms...)
- **117 Relations**
- **254 Entity Occurrences**

## Technical Implementation

### DocumentLoader Class
- Static methods for each format
- Consistent interface: `load_file(path) -> (content, format)`
- Fallback handling for missing dependencies
- Temporary file handling for byte streams

### Format-Specific Extraction
- **PDF**: `pypdf.PdfReader` with page-by-page extraction
- **Word**: `python-docx` for paragraphs and tables
- **HTML/XML**: `BeautifulSoup` with tag filtering
- **CSV**: `pandas` with statistics and sampling
- **JSON**: Recursive flattening for searchability

### Error Handling
- Graceful degradation for unsupported formats
- Clear error messages with format hints
- Batch processing continues on individual failures

## Future Enhancements
- Excel (.xlsx) support (dependency already added)
- PowerPoint (.pptx) support
- Image OCR for scanned PDFs
- Archive extraction (.zip, .tar.gz)
- Streaming for very large files
