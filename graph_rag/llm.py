"""Ollama LLM client for entity and relation extraction."""
from __future__ import annotations

import json
import logging
import re
from typing import List, Optional, Tuple

import httpx

from .models import EntityType, RelationType, ExtractionResult

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = '''You are a medical knowledge graph extraction expert. Extract entities and relations from the following medical text.

ENTITY TYPES:
- DISEASE: diseases, conditions, disorders, syndromes
- DRUG: medications, treatments, therapeutics, vaccines
- GENE: genes, genetic variants
- PROTEIN: proteins, enzymes, receptors
- SYMPTOM: symptoms, signs, clinical findings
- PROCEDURE: medical procedures, surgeries, tests
- ANATOMY: body parts, organs, tissues, cells
- ORGANISM: pathogens, viruses, bacteria
- CHEMICAL: molecules, compounds, biomarkers
- BIOMARKER: diagnostic markers, lab values

RELATION TYPES:
- TREATS: drug/procedure treats disease
- CAUSES: entity causes condition/symptom
- ASSOCIATED_WITH: entities are clinically associated
- INTERACTS_WITH: drug-drug or drug-gene interactions
- TARGETS: drug targets protein/receptor
- INHIBITS: entity inhibits another
- ACTIVATES: entity activates another
- DIAGNOSES: test/biomarker diagnoses condition
- PREVENTS: intervention prevents condition
- LOCATED_IN: anatomical location

TEXT:
{text}

Extract all medical entities and their relationships. Respond with ONLY valid JSON:
{{
  "entities": [
    {{"name": "entity name", "type": "ENTITY_TYPE", "start": 0, "end": 10}}
  ],
  "relations": [
    {{"source": "entity1 name", "target": "entity2 name", "type": "RELATION_TYPE", "confidence": 0.9}}
  ]
}}'''


class OllamaClient:
    """Client for Ollama LLM inference."""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.2"):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._client = httpx.Client(timeout=120.0)
    
    def close(self):
        self._client.close()
    
    def generate(self, prompt: str, temperature: float = 0.1) -> str:
        """Generate text from Ollama."""
        try:
            response = self._client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "temperature": temperature,
                    "stream": False,
                },
            )
            response.raise_for_status()
            return response.json().get("response", "")
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise
    
    def check_health(self) -> bool:
        """Check if Ollama is running."""
        try:
            response = self._client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except:
            return False
    
    def list_models(self) -> List[str]:
        """List available models."""
        try:
            response = self._client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            models = response.json().get("models", [])
            return [m.get("name", "") for m in models]
        except:
            return []


class EntityExtractor:
    """Extract medical entities and relations using Ollama LLM."""
    
    def __init__(self, ollama_client: OllamaClient):
        self.llm = ollama_client
    
    def _parse_json_response(self, response: str) -> Tuple[List[dict], List[dict]]:
        """Parse JSON from LLM response."""
        # Try to find JSON in response
        json_match = re.search(r'\{[\s\S]*\}', response)
        if not json_match:
            logger.warning("No JSON found in response")
            return [], []
        
        try:
            data = json.loads(json_match.group())
            entities = data.get("entities", [])
            relations = data.get("relations", [])
            return entities, relations
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON: {e}")
            return [], []
    
    def _validate_entity_type(self, type_str: str) -> Optional[EntityType]:
        """Validate and normalize entity type."""
        type_str = type_str.upper().strip()
        try:
            return EntityType(type_str)
        except ValueError:
            # Try fuzzy matching
            for et in EntityType:
                if et.value in type_str or type_str in et.value:
                    return et
            return None
    
    def _validate_relation_type(self, type_str: str) -> Optional[RelationType]:
        """Validate and normalize relation type."""
        type_str = type_str.upper().strip().replace(" ", "_")
        try:
            return RelationType(type_str)
        except ValueError:
            for rt in RelationType:
                if rt.value in type_str or type_str in rt.value:
                    return rt
            return None
    
    def extract(self, text: str, chunk_id: str) -> ExtractionResult:
        """Extract entities and relations from text."""
        prompt = EXTRACTION_PROMPT.format(text=text[:3000])  # Limit context size
        
        try:
            response = self.llm.generate(prompt)
            raw_entities, raw_relations = self._parse_json_response(response)
            
            # Validate entities
            entities = []
            for ent in raw_entities:
                name = ent.get("name", "").strip()
                etype = self._validate_entity_type(ent.get("type", ""))
                if name and etype:
                    entities.append({
                        "name": name,
                        "type": etype.value,
                        "start": ent.get("start", 0),
                        "end": ent.get("end", len(name)),
                    })
            
            # Validate relations
            relations = []
            entity_names = {e["name"].lower() for e in entities}
            for rel in raw_relations:
                source = rel.get("source", "").strip()
                target = rel.get("target", "").strip()
                rtype = self._validate_relation_type(rel.get("type", ""))
                
                if source and target and rtype:
                    # Check if entities exist
                    if source.lower() in entity_names and target.lower() in entity_names:
                        relations.append({
                            "source": source,
                            "target": target,
                            "type": rtype.value,
                            "confidence": float(rel.get("confidence", 0.8)),
                        })
            
            logger.info(f"Extracted {len(entities)} entities, {len(relations)} relations from chunk {chunk_id}")
            return ExtractionResult(entities=entities, relations=relations, chunk_id=chunk_id)
            
        except Exception as e:
            logger.error(f"Extraction failed for chunk {chunk_id}: {e}")
            return ExtractionResult(entities=[], relations=[], chunk_id=chunk_id)
