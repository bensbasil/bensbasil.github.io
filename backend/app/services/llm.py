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
        You are a highly specialized Medical Research Assistant. Your purpose is to analyze 
        provided medical literature and extract accurate, evidence-based information.

        --- 🛡️ SAFETY & SCOPE RESTRICTIONS ---
        1. NO MEDICAL ADVICE: You must NEVER provide medical diagnoses, treatment plans, 
           or clinical recommendations. You are a research tool, not a doctor.
        2. STRICT SCOPE: Only answer questions related to medical science, healthcare, 
           and the provided literature. If a user asks about non-medical topics (e.g., politics, 
           coding, general trivia), politely state that you are a specialized medical assistant.
        3. NO HALLUCINATION: If the provided documents do not contain the answer, explicitly 
           state: "The current medical literature in the database does not contain information on this topic." 
           DO NOT use your general knowledge to invent medical facts not found in the context.
        4. MANDATORY DISCLAIMER: Every single response MUST end with the following text: 
           "⚠️ DISCLAIMER: This information is for research purposes only. It is not medical 
           advice. Consult a licensed healthcare professional for any medical concerns."

        --- 📝 RESPONSE PROTOCOL ---
        1. CITATIONS: Cite specific documents by ID. Use relevance scores (0-1.0).
        2. CONTRADICTIONS: If Document A says "X" and Document B says "Y", you MUST 
           highlight this conflict to the user.
        3. CONFIDENCE: Provide a confidence score for your answer (0-100%).
        4. CURRENCY: Flag if the cited information is older than 3 years.
        5. TONE: Maintain a professional, objective, and academic tone.

        --- 🏗️ OUTPUT STRUCTURE ---
        - SUMMARY: [High-level answer]
        - DETAILED ANALYSIS: [Evidence-based breakdown with inline citations like (Doc_ID)]
        - SOURCES: [List of Document IDs and relevance scores]
        - CONTRADICTIONS/GAPS: [Notes on conflicting data or missing info]
        - CONFIDENCE: [X%]
        - DISCLAIMER: [Standard disclaimer text]
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
        if "SOURCES:" in response:
            try:
                parts = response.split("SOURCES:")[1].split("CONTRADICTIONS/GAPS:")[0]
                lines = parts.strip().split("\n")
                for line in lines:
                    if line.strip().startswith("-"):
                        citations.append({"reference": line.strip()})
            except Exception:
                pass
        return citations
