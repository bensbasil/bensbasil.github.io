import pdfplumber
import re
from typing import List, Dict
from fastapi import UploadFile
import tempfile
import os

class PDFProcessor:
    def __init__(self, embedding_model: str):
        self.embedding_model = embedding_model

    async def extract_text(self, file_path: str) -> Dict:
        pages = []
        text_content = ""
        metadata = {}
        with pdfplumber.open(file_path) as pdf:
            metadata = pdf.metadata
            for idx, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    pages.append({"page": idx + 1, "text": page_text})
                    text_content += page_text + "\n"
        return {"pages": pages, "metadata": metadata, "text": text_content}

    async def chunk_text(self, text: str, document_id: str) -> List[Dict]:
        # Semantic chunking approximation using paragraphs and sliding window or max tokens
        # Medical specific logic: detect sections
        chunks = []
        lines = text.split("\n")
        current_section = "General"
        current_chunk = []
        chunk_token_count = 0
        chunk_index = 0
        
        section_pattern = re.compile(r'^(abstract|introduction|methods|results|discussion|conclusion|references)$', re.IGNORECASE)
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Naive section detection
            if len(line.split()) < 5 and section_pattern.match(line):
                current_section = line.title()
                
            tokens = len(line.split())
            if chunk_token_count + tokens > 400:
                chunk_text = " ".join(current_chunk)
                chunks.append({
                    "text": chunk_text,
                    "page": None,  # Advanced implementations map this text back to page ranges
                    "section": current_section,
                    "keywords": self._extract_keywords(chunk_text),
                    "chunk_index": chunk_index
                })
                chunk_index += 1
                # Sliding window overlap
                current_chunk = current_chunk[-3:] + [line]
                chunk_token_count = sum(len(c.split()) for c in current_chunk)
            else:
                current_chunk.append(line)
                chunk_token_count += tokens

        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append({
                "text": chunk_text,
                "page": None,
                "section": current_section,
                "keywords": self._extract_keywords(chunk_text),
                "chunk_index": chunk_index
            })

        return chunks

    def _extract_keywords(self, text: str) -> List[str]:
        # Simple extraction for medical context
        indicators = ["may", "likely", "suggests", "confirms", "indicates"]
        found = [ind for ind in indicators if ind in text.lower()]
        return found

    async def process_medical_pdf(self, file: UploadFile, document_id: str) -> List[Dict]:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name

        try:
            extracted = await self.extract_text(temp_path)
            chunks = await self.chunk_text(extracted["text"], document_id)
            return chunks
        finally:
            os.remove(temp_path)
