"""
Candidate source discovery for the pre-generation sources preview.

Academic sources (OpenAlex + arXiv) are free and always fetched. Current/web
(Serper) is opt-in (it has a per-call cost) and only runs when include_web=True.
Returns a flat list of tier-tagged SourceDoc candidates the instructor can
curate before generation. Never raises.
"""
import asyncio
import logging
import re
from typing import List

from .academic_search import OpenAlexClient
from .arxiv_search import ArxivClient
from .models import SourceDoc

logger = logging.getLogger(__name__)

# Generic words that don't identify a subject — stripped before relevance matching.
_STOPWORDS = {
    "introduction", "intro", "principles", "fundamentals", "basics", "essentials",
    "course", "studies", "study", "applied", "advanced", "topics", "survey",
    "the", "and", "for", "with", "from",
}


def course_terms(query: str) -> set:
    """Salient subject terms from a course name/topic (drops generic filler)."""
    return {w for w in re.findall(r"[a-z]{4,}", (query or "").lower()) if w not in _STOPWORDS}


def filter_relevant(docs: List[SourceDoc], query: str) -> List[SourceDoc]:
    """Keep only academic sources that share a salient course term in title/abstract.

    Guards against loose academic-search matches (e.g. arXiv returning
    'Introduction to Electromagnetism' for a Marketing course). Falls back to
    returning everything if the query yields no salient terms.
    """
    terms = course_terms(query)
    if not terms:
        return docs
    kept = []
    for d in docs:
        hay = f"{d.title} {d.text}".lower()
        if any(t in hay for t in terms):
            kept.append(d)
        else:
            logger.debug(f"Dropped off-topic source: {d.title[:60]}")
    return kept


async def fetch_candidate_sources(course_name: str,
                                  include_web: bool = False,
                                  serper_api_key: str = "") -> List[SourceDoc]:
    async def _openalex():
        try:
            return await OpenAlexClient().search(course_name, k=5)
        except Exception as e:
            logger.warning(f"OpenAlex preview failed: {e}")
            return []

    async def _arxiv():
        try:
            return await ArxivClient().search(course_name, k=4)
        except Exception as e:
            logger.warning(f"arXiv preview failed: {e}")
            return []

    openalex, arxiv = await asyncio.gather(_openalex(), _arxiv())
    # Drop off-topic academic matches (loose arXiv/OpenAlex hits) before returning.
    docs: List[SourceDoc] = filter_relevant((openalex or []) + (arxiv or []), course_name)

    if include_web and serper_api_key:
        try:
            from serper_service import SerperSearchService
            from .source_pool import serper_to_docs
            svc = SerperSearchService(serper_api_key)
            query = f"{course_name} latest developments and industry applications"
            serp = await svc.search_industry_resources(query, 5)
            docs += serper_to_docs(serp)
        except Exception as e:
            logger.warning(f"Web (Serper) preview failed: {e}")

    return docs
