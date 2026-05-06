"""
PubMed Central scraper service.

Uses NCBI's free E-utilities API (no key required, polite rate-limiting applied).
Optional: set NCBI_API_KEY in .env to raise rate limit from 3 → 10 req/sec.
"""

import asyncio
import httpx
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional
from app.utils.logger import logger


EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
PMC_PDF_BASE = "https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/pdf/"


class PubMedScraper:
    def __init__(self, api_key: Optional[str] = None):
        # NCBI API key is optional — raises rate limit 3 → 10 req/sec
        self.api_key = api_key
        # Delay between requests (seconds). 0.4s is safe without a key.
        self._delay = 0.15 if api_key else 0.4

    def _params(self, extra: dict) -> dict:
        """Merge base params (api_key if set) with endpoint-specific params."""
        p = {"retmode": "json"}
        if self.api_key:
            p["api_key"] = self.api_key
        p.update(extra)
        return p

    # ── Search ────────────────────────────────────────────────────────────────

    async def search(self, topic: str, max_results: int = 10) -> List[str]:
        """
        Search PubMed Central for open-access papers on a topic.
        Returns a list of PMC IDs (e.g. ['PMC8374210', ...]).
        """
        params = self._params({
            "db": "pmc",
            "term": f"{topic} AND open access[filter]",
            "retmax": max_results,
            "sort": "relevance",
        })

        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(f"{EUTILS_BASE}/esearch.fcgi", params=params)
            resp.raise_for_status()
            data = resp.json()

        ids = data.get("esearchresult", {}).get("idlist", [])
        pmc_ids = [f"PMC{id_}" for id_ in ids]
        logger.info(f"PubMed search '{topic}' → {len(pmc_ids)} results")
        return pmc_ids

    # ── Metadata ─────────────────────────────────────────────────────────────

    async def fetch_metadata(self, pmc_ids: List[str]) -> List[Dict]:
        """
        Fetch title, authors, year, and abstract for a list of PMC IDs.
        Returns a list of metadata dicts.
        """
        if not pmc_ids:
            return []

        # Strip "PMC" prefix for the API
        numeric_ids = [id_.replace("PMC", "") for id_ in pmc_ids]
        params = self._params({
            "db": "pmc",
            "id": ",".join(numeric_ids),
            "rettype": "abstract",
        })

        async with httpx.AsyncClient(timeout=20) as client:
            await asyncio.sleep(self._delay)
            resp = await client.get(f"{EUTILS_BASE}/esummary.fcgi", params=params)
            resp.raise_for_status()
            data = resp.json()

        result = data.get("result", {})
        papers = []
        for id_ in numeric_ids:
            record = result.get(id_, {})
            if not record or record.get("error"):
                continue

            # Authors: list of {name, authtype, clusterid}
            authors_raw = record.get("authors", [])
            authors = [a.get("name", "") for a in authors_raw if a.get("name")]

            papers.append({
                "pmc_id": f"PMC{id_}",
                "title": record.get("title", f"PMC{id_}"),
                "authors": authors,
                "pub_year": self._parse_year(record.get("pubdate", "")),
                "source": record.get("source", ""),
            })

        return papers

    # ── Full Text Extraction (replaces PDF Download) ─────────────────────────

    async def fetch_full_text(self, pmc_id: str) -> Optional[str]:
        """
        Fetch the full text XML of the paper and extract paragraphs.
        Bypasses PMC's new anti-bot PDF protections.
        """
        numeric_id = pmc_id.replace("PMC", "")
        params = self._params({
            "db": "pmc",
            "id": numeric_id,
            "retmode": "xml",
        })

        await asyncio.sleep(self._delay)

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(f"{EUTILS_BASE}/efetch.fcgi", params=params)
                if resp.status_code != 200:
                    logger.warning(f"{pmc_id}: failed to fetch full text (status={resp.status_code})")
                    return None

                xml_data = resp.text
                if not xml_data.strip():
                    return None

                # Extract all <p> tags
                root = ET.fromstring(xml_data)
                paragraphs = []
                for p in root.iter('p'):
                    if p.text and p.text.strip():
                        # Extract inner text to handle bold/italic tags if needed
                        paragraphs.append("".join(p.itertext()).strip())

                if not paragraphs:
                    logger.warning(f"{pmc_id}: no paragraphs found in XML")
                    return None

                full_text = "\n\n".join(paragraphs)
                logger.info(f"{pmc_id}: extracted {len(paragraphs)} paragraphs of text")
                return full_text

        except Exception as e:
            logger.error(f"{pmc_id}: full text extraction failed — {e}")
            return None

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _parse_year(pubdate: str) -> Optional[int]:
        """Extract the 4-digit year from strings like '2023 Jan', '2023', etc."""
        if not pubdate:
            return None
        for token in pubdate.split():
            if token.isdigit() and len(token) == 4:
                return int(token)
        return None
