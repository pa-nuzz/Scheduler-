from typing import List, Dict, Any


class RAGPipeline:
 

    def __init__(self, embedder, vector_store, memory, llm):
        self.embedder = embedder
        self.vector_store = vector_store
        self.memory = memory
        self.llm = llm

    def _format_history(self, history: List[Dict[str, str]]) -> str:
        if not history:
            return "No previous conversation."
        lines = []
        for entry in history:
            lines.append(f"User: {entry.get('user', '')}")
            lines.append(f"Assistant: {entry.get('assistant', '')}")
        return "\n".join(lines)

    def _format_context(self, results: List[Dict[str, Any]]) -> str:
        if not results:
            return "No relevant documents found."
        parts = []
        for i, r in enumerate(results, 1):
            filename = r.get("metadata", {}).get("filename", "Unknown")
            parts.append(f"[Document {i} - {filename}]\n{r.get('text', '')}")
        return "\n\n".join(parts)

    async def run(self, query: str, session_id: str) -> Dict[str, Any]:
        """Run the full RAG pipeline and return the answer with source citations."""
        # 1. Embed the query
        query_vector = await self.embedder.get_query_embedding(query)

        # 2. Retrieve the most relevant chunks from qdrant
        results = await self.vector_store.search(query_vector, top_k=5)

        # 3. Pull chat history from Redis for multiturncontext
        history = await self.memory.get_history(session_id, limit=5)

        # 4. Build the prompt teling the llm to use only the context
        prompt = f"""You are a helpful assistant. Answer using only the context below.

Context:
{self._format_context(results)}

Previous Conversation:
{self._format_history(history)}

User Question: {query}

Answer:"""

        # 5. Generate the answer
        answer = await self.llm.generate_answer(prompt)

        # 6. Save this turn to Redis memory
        await self.memory.save(session_id, query, answer)

        return {
            "answer": answer,
            "sources": [
                {
                    "text": r["text"][:200] + "..." if len(r["text"]) > 200 else r["text"],
                    "metadata": r.get("metadata", {}),
                    "score": r.get("score", 0),
                }
                for r in results[:3]
            ],
        }
