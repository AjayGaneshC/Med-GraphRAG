"""CLI interface for Graph RAG system."""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from .config import get_settings
from .database import Neo4jClient
from .llm import OllamaClient
from .embeddings import EmbeddingService
from .kg_builder import KnowledgeGraphBuilder
from .retriever import GraphRAG

app = typer.Typer(
    name="graph-rag",
    help="Medical Knowledge Graph RAG System",
    add_completion=False,
)
console = Console()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def get_clients():
    """Initialize all clients."""
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


@app.command()
def init():
    """Initialize the database schema."""
    console.print("[bold blue]Initializing Graph RAG database...[/bold blue]")
    
    db, ollama, embeddings, settings = get_clients()
    
    try:
        # Check Ollama
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Checking Ollama connection...", total=None)
            if ollama.check_health():
                models = ollama.list_models()
                console.print(f"[green]✓[/green] Ollama connected. Available models: {', '.join(models[:5])}")
            else:
                console.print("[yellow]⚠[/yellow] Ollama not running. Start it with: ollama serve")
            
            progress.update(task, description="Setting up Neo4j schema...")
            db.setup_schema()
            console.print("[green]✓[/green] Neo4j schema initialized")
            
            progress.update(task, description="Testing embedding model...")
            dim = embeddings.dimension
            console.print(f"[green]✓[/green] Embedding model loaded (dimension: {dim})")
        
        console.print("\n[bold green]Graph RAG initialized successfully![/bold green]")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)
    finally:
        db.close()
        ollama.close()


@app.command()
def ingest(
    path: Path = typer.Argument(..., help="Path to file or directory to ingest"),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="Document title"),
):
    """Ingest documents into the knowledge graph."""
    from .document_loaders import DocumentLoader
    
    if not path.exists():
        console.print(f"[red]Error: Path does not exist: {path}[/red]")
        raise typer.Exit(1)
    
    db, ollama, embeddings, settings = get_clients()
    
    try:
        builder = KnowledgeGraphBuilder(
            db_client=db,
            ollama_client=ollama,
            embedding_service=embeddings,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
        
        if path.is_file():
            files = [path]
        else:
            # Collect all supported file types
            supported_exts = DocumentLoader.get_supported_extensions()
            files = []
            for ext in supported_exts:
                files.extend(path.glob(f"**/*{ext}"))
        
        if not files:
            console.print(f"[yellow]No supported files found. Supported: {DocumentLoader.get_supported_extensions_display()}[/yellow]")
            raise typer.Exit(0)
        
        console.print(f"[blue]Found {len(files)} file(s) to ingest[/blue]\n")
        
        total_stats = {"chunks": 0, "occurrences": 0, "new_entities": 0, "relations": 0}
        errors = []
        
        with Progress(console=console) as progress:
            task = progress.add_task("Ingesting files...", total=len(files))
            
            for file_path in files:
                console.print(f"Processing: [cyan]{file_path.name}[/cyan]")
                
                try:
                    # Load file using document loader
                    content, format_type = DocumentLoader.load_file(str(file_path))
                    
                    if not content.strip():
                        errors.append(f"{file_path.name}: No text content extracted")
                        continue
                    
                    doc_title = title or file_path.stem
                    
                    stats = builder.ingest_text(
                        text=content,
                        title=doc_title,
                        source=str(file_path),
                    )
                    
                    for key in total_stats:
                        total_stats[key] += stats.get(key, 0)
                except Exception as e:
                    errors.append(f"{file_path.name}: {str(e)[:100]}")
                    logger.exception(f"Failed to process {file_path}")
                
                progress.advance(task)
        
        # Show errors if any
        if errors:
            console.print("\n[yellow]⚠ Some files had issues:[/yellow]")
            for error in errors:
                console.print(f"  [yellow]- {error}[/yellow]")
            console.print()
        
        # Show summary
        table = Table(title="Ingestion Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Count", style="green")
        
        table.add_row("Documents", str(len(files) - len(errors)))
        table.add_row("Chunks", str(total_stats["chunks"]))
        table.add_row("Entity Occurrences", str(total_stats["occurrences"]))
        table.add_row("New Canonical Entities", str(total_stats["new_entities"]))
        table.add_row("Relations", str(total_stats["relations"]))
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        logging.exception("Ingestion failed")
        raise typer.Exit(1)
    finally:
        db.close()
        ollama.close()


@app.command()
def query(
    question: str = typer.Argument(..., help="Question to ask"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show sources"),
):
    """Query the knowledge graph."""
    db, ollama, embeddings, settings = get_clients()
    
    try:
        rag = GraphRAG(
            db_client=db,
            ollama_client=ollama,
            embedding_service=embeddings,
        )
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task("Searching knowledge graph...", total=None)
            result = rag.query(question)
        
        # Show answer
        console.print(Panel(
            result.answer,
            title="[bold blue]Answer[/bold blue]",
            border_style="blue",
        ))
        
        if result.entities_found:
            console.print(f"\n[dim]Entities found: {', '.join(result.entities_found[:10])}[/dim]")
        
        if verbose and result.sources:
            console.print("\n[bold]Sources:[/bold]")
            for i, src in enumerate(result.sources, 1):
                console.print(f"\n[cyan]{i}. {src['document']}[/cyan]")
                console.print(f"[dim]{src['text'][:200]}...[/dim]")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)
    finally:
        db.close()
        ollama.close()


@app.command()
def stats():
    """Show knowledge graph statistics."""
    db, _, _, _ = get_clients()
    
    try:
        # Get counts
        counts_query = """
        MATCH (d:Document) WITH count(d) as docs
        MATCH (c:Chunk) WITH docs, count(c) as chunks
        MATCH (o:Occurrence) WITH docs, chunks, count(o) as occurrences
        MATCH (e:CanonicalEntity) WITH docs, chunks, occurrences, count(e) as entities
        MATCH ()-[r:RELATES_TO]->() WITH docs, chunks, occurrences, entities, count(r) as relations
        RETURN docs, chunks, occurrences, entities, relations
        """
        results = db.execute_read(counts_query)
        
        if results:
            r = results[0]
            table = Table(title="Knowledge Graph Statistics")
            table.add_column("Node/Relationship", style="cyan")
            table.add_column("Count", style="green")
            
            table.add_row("Documents", str(r["docs"]))
            table.add_row("Chunks", str(r["chunks"]))
            table.add_row("Occurrences", str(r["occurrences"]))
            table.add_row("Canonical Entities", str(r["entities"]))
            table.add_row("Relations", str(r["relations"]))
            
            console.print(table)
        else:
            console.print("[yellow]No data in knowledge graph yet[/yellow]")
        
        # Entity type breakdown
        type_query = """
        MATCH (e:CanonicalEntity)
        RETURN e.entity_type as type, count(*) as count
        ORDER BY count DESC
        """
        type_results = db.execute_read(type_query)
        
        if type_results:
            table2 = Table(title="Entities by Type")
            table2.add_column("Entity Type", style="cyan")
            table2.add_column("Count", style="green")
            
            for r in type_results:
                table2.add_row(r["type"], str(r["count"]))
            
            console.print(table2)
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)
    finally:
        db.close()


@app.command()
def clear(
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
):
    """Clear all data from the knowledge graph."""
    if not confirm:
        confirm = typer.confirm("Are you sure you want to delete all data?")
    
    if not confirm:
        console.print("[yellow]Aborted[/yellow]")
        raise typer.Exit(0)
    
    db, _, _, _ = get_clients()
    
    try:
        db.clear_database()
        console.print("[green]Database cleared successfully[/green]")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)
    finally:
        db.close()


def main():
    """Entry point."""
    app()


if __name__ == "__main__":
    main()
