"""
Academic literature search (Tier 2) via OpenAlex.

OpenAlex is free, requires no API key, and exposes ~250M scholarly works with
abstracts, authors, years, and DOIs. We use the "polite pool" (a contact email)
for better rate limits. Returns tier-2 SourceDoc objects; never raises.
"""
import logging
from typing import List, Optional

import aiohttp

from .models import SourceDoc

logger = logging.getLogger(__name__)

OPENALEX_URL = "https://api.openalex.org/works"
# Polite-pool contact. Neutral by design; override via OpenAlexClient(contact_email=...).
DEFAULT_CONTACT = "ai-course-builder@users.noreply.github.com"


def _reconstruct_abstract(inverted_index: Optional[dict], max_chars: int = 1500) -> str:
    """OpenAlex stores abstracts as an inverted index {word: [positions]}."""
    if not inverted_index:
        return ""
    positions: dict = {}
    for word, idxs in inverted_index.items():
        for i in idxs:
            positions[i] = word
    text = " ".join(positions[i] for i in sorted(positions))
    return text[:max_chars]


class OpenAlexClient:
    """Minimal async OpenAlex client for the academic grounding tier."""

    def __init__(self, contact_email: str = DEFAULT_CONTACT):
        self.contact = contact_email

    async def search(self, query: str, k: int = 5) -> List[SourceDoc]:
        params = {
            "search": query,
            "per_page": str(max(1, k)),
            "mailto": self.contact,
            "filter": "has_abstract:true",
            "sort": "relevance_score:desc",
        }
        try:
            timeout = aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(OPENALEX_URL, params=params) as resp:
                    if resp.status != 200:
                        logger.warning(f"OpenAlex request failed: HTTP {resp.status}")
                        return []
                    data = await resp.json()
        except Exception as e:
            logger.warning(f"OpenAlex search failed: {e}")
            return []

        docs: List[SourceDoc] = []
        for work in data.get("results", []):
            authorships = work.get("authorships", []) or []
            first_author = ""
            if authorships:
                first_author = (authorships[0].get("author", {}) or {}).get("display_name", "") or ""
            etal = " et al." if len(authorships) > 1 else ""

            doi = (work.get("doi") or "").replace("https://doi.org/", "")
            landing = ((work.get("primary_location") or {}).get("landing_page_url")) or ""
            url = landing or (f"https://doi.org/{doi}" if doi else "")

            abstract = _reconstruct_abstract(work.get("abstract_inverted_index"))
            if not abstract:
                # without groundable text the source can't support a claim; skip it
                continue

            docs.append(SourceDoc(
                id=0,  # assigned by build_pool
                tier=2,
                title=work.get("title") or "Untitled work",
                text=abstract,
                authors=f"{first_author}{etal}".strip(),
                year=str(work.get("publication_year") or ""),
                doi=doi,
                url=url,
            ))
        logger.debug(f"OpenAlex returned {len(docs)} usable works for query '{query}'")
        return docs
