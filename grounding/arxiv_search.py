"""
arXiv preprint search (academic tier) via the free arXiv API.

No API key, no extra dependency — the Atom response is parsed with the stdlib
xml.etree. Great for current AI / ML / data-science / quantitative-business
preprints. Returns tier-2 SourceDoc objects; never raises.
"""
import logging
import xml.etree.ElementTree as ET
from typing import List

import aiohttp

from .models import SourceDoc

logger = logging.getLogger(__name__)

ARXIV_URL = "http://export.arxiv.org/api/query"
_ATOM = "{http://www.w3.org/2005/Atom}"


class ArxivClient:
    """Minimal async arXiv client for the academic grounding tier."""

    async def search(self, query: str, k: int = 3) -> List[SourceDoc]:
        params = {
            "search_query": f"all:{query}",
            "start": "0",
            "max_results": str(max(1, k)),
            "sortBy": "relevance",
            "sortOrder": "descending",
        }
        try:
            timeout = aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(ARXIV_URL, params=params) as resp:
                    if resp.status != 200:
                        logger.warning(f"arXiv request failed: HTTP {resp.status}")
                        return []
                    raw = await resp.text()
        except Exception as e:
            logger.warning(f"arXiv search failed: {e}")
            return []

        try:
            root = ET.fromstring(raw)
        except Exception as e:
            logger.warning(f"arXiv response parse failed: {e}")
            return []

        docs: List[SourceDoc] = []
        for entry in root.findall(f"{_ATOM}entry"):
            summary = (entry.findtext(f"{_ATOM}summary") or "").strip().replace("\n", " ")
            if not summary:
                continue
            title = (entry.findtext(f"{_ATOM}title") or "Untitled").strip().replace("\n", " ")
            year = (entry.findtext(f"{_ATOM}published") or "")[:4]
            authors = [
                (a.findtext(f"{_ATOM}name") or "").strip()
                for a in entry.findall(f"{_ATOM}author")
            ]
            authors = [a for a in authors if a]
            first = authors[0] if authors else ""
            etal = " et al." if len(authors) > 1 else ""
            url = (entry.findtext(f"{_ATOM}id") or "").strip()  # e.g. http://arxiv.org/abs/2401.01234

            docs.append(SourceDoc(
                id=0,  # assigned by build_pool
                tier=2,
                title=title,
                text=summary[:1500],
                authors=f"{first}{etal} (arXiv)".strip(),
                year=year,
                url=url,
            ))
        logger.debug(f"arXiv returned {len(docs)} works for query '{query}'")
        return docs
