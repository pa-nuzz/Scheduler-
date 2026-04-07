import re
from typing import List
class ChunkerService:
    @staticmethod
    def recursive_chunking(text: str, chunk_size:int=800, chunk_overlap: int =100) -> List[str]:
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            start += chunk_size - chunk_overlap
        return chunks
    

    @staticmethod
    def semantic_chunking(text:str)-> list[str]:
        sentences = re.split(r'(?<=[.!?]) +', text)
        group_size = 4
        return [' '.join(sentences[i:i+group_size]) for i in range(0, len(sentences),
group_size)]
    