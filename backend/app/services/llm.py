from typing import List, Dict, Optional, AsyncGenerator
import google.generativeai as genai
import json
import httpx
import ollama
from huggingface_hub import AsyncInferenceClient
from app.utils.logger import logger

class MedicalRAGLLM:
    def __init__(self, settings):
        self.settings = settings
        self.provider = settings.LLM_PROVIDER.lower()
        self.system_prompt = self.build_system_prompt()
        
        if self.provider == "gemini":
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel(
                model_name='models/gemini-2.0-flash' # Updated to a more recent stable model
            )
        elif self.provider == "ollama":
            self.ollama_client = ollama.AsyncClient(host=settings.OLLAMA_BASE_URL)
        elif self.provider == "huggingface":
            self.hf_client = AsyncInferenceClient(
                model=settings.HF_MODEL,
                token=settings.HF_API_KEY
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

        prompt = f"{context_block}\nUSER QUESTION:\n{question}"

        if self.provider == "gemini":
            async for token in self._generate_gemini(prompt, conversation_history):
                yield token
        elif self.provider == "ollama":
            async for token in self._generate_ollama(prompt, conversation_history):
                yield token
        elif self.provider == "huggingface":
            async for token in self._generate_huggingface(prompt, conversation_history):
                yield token
        else:
            yield f"Error: Unknown LLM provider '{self.provider}'"

    async def _generate_gemini(self, prompt: str, history: Optional[List]) -> AsyncGenerator[str, None]:
        contents = [{"role": "user", "parts": [self.system_prompt]}] # System instructions as first turn
        if history:
            for msg in history:
                role = "model" if msg["role"] == "assistant" else "user"
                contents.append({"role": role, "parts": [msg["content"]]})
        
        contents.append({"role": "user", "parts": [prompt]})

        try:
            response = await self.model.generate_content_async(contents, stream=True)
            async for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            logger.error(f"Gemini error: {e}")
            yield f"\n⚠️ Gemini Error: {str(e)}"

    async def _generate_ollama(self, prompt: str, history: Optional[List]) -> AsyncGenerator[str, None]:
        messages = [{"role": "system", "content": self.system_prompt}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": prompt})

        try:
            stream = await self.ollama_client.chat(
                model=self.settings.OLLAMA_MODEL,
                messages=messages,
                stream=True,
            )
            async for chunk in stream:
                yield chunk['message']['content']
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            yield f"\n⚠️ Ollama Error: {str(e)}"

    async def _generate_huggingface(self, prompt: str, history: Optional[List]) -> AsyncGenerator[str, None]:
        messages = [{"role": "system", "content": self.system_prompt}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": prompt})

        try:
            stream = await self.hf_client.chat_completion(
                messages=messages,
                max_tokens=1024,
                stream=True
            )
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"Hugging Face error: {e}")
            yield f"\n⚠️ Hugging Face Error: {str(e)}"

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
