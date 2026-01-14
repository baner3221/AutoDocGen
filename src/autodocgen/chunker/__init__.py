"""
Intelligent chunking module for processing large C++ files.
"""

from autodocgen.chunker.intelligent_chunker import IntelligentChunker
from autodocgen.chunker.context_builder import ContextBuilder
from autodocgen.chunker.models import CodeChunk, ChunkContext

__all__ = [
    "IntelligentChunker",
    "ContextBuilder",
    "CodeChunk",
    "ChunkContext",
]
