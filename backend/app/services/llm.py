from typing import List, Dict, Optional, AsyncGenerator
import google.generativeai as genai
import json

class MedicalRAGLLM:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.system_prompt = self.build_system_prompt()
        self.model = genai.GenerativeModel(
            model_name='models/gemini-2.5-flash'
        )

    def build_system_prompt(self) -> str:
        return """
        You are a medical research assistant powered by AI. Your role is to help 
        doctors, researchers, and students find accurate answers in medical literature.
        
        CRITICAL RULES:
        1. Always cite specific sources with relevance scores
        2. Indicate your confidence (0-100%) in the answer
        3. Flag contradictions between retrieved documents
        4. Note if cited information is >2 years old
        5. Never provide medical diagnoses or treatment recommendations
        6. Always include: "Consult a licensed healthcare professional"
        
        OUTPUT FORMAT:
        ---
        ANSWER:
        [Your comprehensive answer based on retrieved sources]
        
        SOURCES CITED:
        - [Document 1]: "relevant quote" (Relevance: 95%, Page: 3)
        - [Document 2]: "relevant quote" (Relevance: 87%, Page: 5)
        
        CONFIDENCE: 92%
        
        IMPORTANT NOTES:
        - [Any contradictions, gaps, or safety warnings]
        
        PROFESSIONAL RECOMMENDATION:
        Consult a licensed healthcare professional before making medical decisions.
        ---
        """

    async def generate_answer(
        self,
        question: str,
        retrieved_chunks: List[Dict],
        conversation_history: Optional[List] = None
    ) -> AsyncGenerator[str, None]:
        
        context_block = "RETRIEVED CONTEXT:\n"
        for i, chunk in enumerate(retrieved_chunks):
            source_id = chunk.get("document_id", f"doc_{i}")
            score = chunk.get("score", 0)
            context_block += f"--- Document {source_id} (Score: {score}) ---\n"
            context_block += f"{chunk['text']}\n\n"

        prompt = f"{self.system_prompt}\n\n{context_block}\nUSER QUESTION:\n{question}"

        # Gemini supports chat sessions, but for RAG a single generate_content_async stream is robust
        # If conversation_history is provided, we can build a formal chat via `start_chat()`,
        # but for simple streaming with context, `generate_content_async` is ideal.
        
        contents = []
        if conversation_history:
            for msg in conversation_history:
                # Map standard roles to Gemini roles ('user' or 'model')
                role = "model" if msg["role"] == "assistant" else "user"
                contents.append({"role": role, "parts": [msg["content"]]})
                
        contents.append({"role": "user", "parts": [prompt]})

        response = await self.model.generate_content_async(
            contents,
            stream=True
        )

        async for chunk in response:
            if chunk.text:
                yield chunk.text

    def parse_citations(self, response: str) -> List[Dict]:
        citations = []
        if "SOURCES CITED:" in response:
            try:
                parts = response.split("SOURCES CITED:")[1].split("CONFIDENCE:")[0]
                lines = parts.strip().split("\n")
                for line in lines:
                    if line.strip().startswith("-"):
                        citations.append({"reference": line.strip()})
            except Exception:
                pass
        return citations
