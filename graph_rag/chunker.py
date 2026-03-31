"""Text chunking with sentence-aware boundaries."""
from __future__ import annotations

import re
from typing import List, Generator
from uuid import uuid4

from .models import Chunk


class TextChunker:
    """Split text into overlapping chunks with sentence-aware boundaries."""
    
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        # Sentence boundary pattern
        self._sentence_pattern = re.compile(r'(?<=[.!?])\s+(?=[A-Z])')
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        sentences = self._sentence_pattern.split(text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _find_sentence_boundary(self, text: str, pos: int, direction: int = 1) -> int:
        """Find nearest sentence boundary from position."""
        boundaries = ['.', '!', '?']
        search_range = 100  # Look within 100 chars
        
        if direction > 0:  # Forward
            for i in range(pos, min(pos + search_range, len(text))):
                if text[i] in boundaries:
                    return i + 1
        else:  # Backward
            for i in range(pos, max(pos - search_range, 0), -1):
                if text[i] in boundaries:
                    return i + 1
        return pos
    
    def chunk(self, text: str, doc_id: str) -> List[Chunk]:
        """Split text into chunks."""
        if not text or not text.strip():
            return []
        
        text = text.strip()
        text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
        
        chunks = []
        start = 0
        index = 0
        
        while start < len(text):
            # Calculate end position
            end = start + self.chunk_size
            
            if end >= len(text):
                end = len(text)
            else:
                # Try to find sentence boundary
                boundary = self._find_sentence_boundary(text, end, direction=-1)
                if boundary > start + self.chunk_size // 2:  # Don't go too far back
                    end = boundary
            
            chunk_text = text[start:end].strip()
            
            if chunk_text:
                chunks.append(Chunk(
                    id=f"chunk_{doc_id}_{index}_{uuid4().hex[:8]}",
                    doc_id=doc_id,
                    text=chunk_text,
                    index=index,
                    start_char=start,
                    end_char=end,
                    embedding=None,
                ))
                index += 1
            
            # Move start with overlap
            if end >= len(text):
                break
            start = end - self.chunk_overlap
            if start >= end:  # Safety check
                start = end
        
        return chunks
    
    def chunk_generator(self, text: str, doc_id: str) -> Generator[Chunk, None, None]:
        """Generator version for large texts."""
        for chunk in self.chunk(text, doc_id):
            yield chunk
