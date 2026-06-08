"""
Candidate source discovery for the pre-generation sources preview.

Academic sources (OpenAlex + arXiv) are free and always fetched. Current/web
(Serper) is opt-in (it has a per-call cost) and only runs when include_web=True.
Returns a flat list of tier-tagged SourceDoc candidates the instructor can
curate before generation. Never raises.
"""
import asyncio
import logging
from typing import List

from .academic_search import OpenAlexClient
from .arxiv_search import ArxivClient
from .models import SourceDoc

logger = logging.getLogger(__name__)


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
    docs: List[SourceDoc] = (openalex or []) + (arxiv or [])

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
