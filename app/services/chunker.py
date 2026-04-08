import re
from typing import List


class ChunkerService:
    """2 chunking strategies for splitting document text before embedding."""

    @staticmethod
    def recursive_chunking(text: str, chunk_size: int = 800, chunk_overlap: int = 100) -> List[str]:
        """ split text into fixed-size character chunks with overlap bc 
        it prevent losing context at boundrys
        """
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            start += chunk_size - chunk_overlap
        return chunks

    @staticmethod
    def semantic_chunking(text: str, sentences_per_chunk: int = 4) -> List[str]:
        """
        split text by grouping N sentences together per chunk bc 
        it creats natural chunk preserce context beter
        """
        sentences = re.split(r'(?<=[.!?]) +', text)
        chunks = []
        for i in range(0, len(sentences), sentences_per_chunk):
            chunk = ' '.join(sentences[i:i + sentences_per_chunk])
            chunks.append(chunk)
        return chunks
