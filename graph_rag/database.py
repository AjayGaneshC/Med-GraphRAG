"""Neo4j database client."""
from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Any, Dict, Generator, List, Optional

from neo4j import GraphDatabase, Driver

logger = logging.getLogger(__name__)


class Neo4jClient:
    """Neo4j database client with connection pooling."""
    
    def __init__(self, uri: str, user: str, password: str):
        self.uri = uri
        self.user = user
        self.password = password
        self._driver: Optional[Driver] = None
    
    @property
    def driver(self) -> Driver:
        if self._driver is None:
            self._driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
            )
        return self._driver
    
    def close(self):
        if self._driver:
            self._driver.close()
            self._driver = None
    
    @contextmanager
    def session(self) -> Generator:
        session = self.driver.session()
        try:
            yield session
        finally:
            session.close()
    
    def execute_write(self, query: str, params: Optional[Dict[str, Any]] = None) -> None:
        """Execute a write query."""
        params = params or {}
        with self.session() as session:
            session.execute_write(lambda tx: tx.run(query, **params))
    
    def execute_read(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict]:
        """Execute a read query and return results."""
        params = params or {}
        with self.session() as session:
            result = session.execute_read(lambda tx: list(tx.run(query, **params)))
            return [dict(record) for record in result]
    
    def setup_schema(self):
        """Create indexes and constraints for the knowledge graph."""
        constraints = [
            "CREATE CONSTRAINT doc_id IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE",
            "CREATE CONSTRAINT chunk_id IF NOT EXISTS FOR (c:Chunk) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT occurrence_id IF NOT EXISTS FOR (o:Occurrence) REQUIRE o.id IS UNIQUE",
            "CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:CanonicalEntity) REQUIRE e.id IS UNIQUE",
        ]
        indexes = [
            "CREATE INDEX entity_name IF NOT EXISTS FOR (e:CanonicalEntity) ON (e.name)",
            "CREATE INDEX entity_type IF NOT EXISTS FOR (e:CanonicalEntity) ON (e.entity_type)",
            "CREATE INDEX occurrence_text IF NOT EXISTS FOR (o:Occurrence) ON (o.text)",
        ]
        
        # Vector indexes (Neo4j 5.11+)
        vector_indexes = [
            "CREATE VECTOR INDEX chunk_embedding_index IF NOT EXISTS FOR (c:Chunk) ON c.embedding OPTIONS {indexConfig: {`vector.dimensions`: 384, `vector.similarity_function`: 'cosine'}}",
            "CREATE VECTOR INDEX entity_embedding_index IF NOT EXISTS FOR (e:CanonicalEntity) ON e.embedding OPTIONS {indexConfig: {`vector.dimensions`: 384, `vector.similarity_function`: 'cosine'}}",
        ]
        
        for constraint in constraints:
            try:
                self.execute_write(constraint)
            except Exception as e:
                logger.debug(f"Constraint may exist: {e}")
        
        for index in indexes:
            try:
                self.execute_write(index)
            except Exception as e:
                logger.debug(f"Index may exist: {e}")
        
        # Try vector indexes (may fail on Community edition)
        for vindex in vector_indexes:
            try:
                self.execute_write(vindex)
            except Exception as e:
                logger.warning(f"Vector index not created (Enterprise feature): {e}")
        
        logger.info("Neo4j schema setup complete")
    
    def clear_database(self):
        """Clear all data from the database."""
        self.execute_write("MATCH (n) DETACH DELETE n")
        logger.info("Database cleared")
