"""Grounding package: source-grounded, citation-enforced generation."""
from .models import (
    SourceDoc,
    SourcePool,
    GroundingStrength,
    GROUNDED_OR_SILENT_RULE,
)
from .source_pool import build_pool, assemble_pool, serper_to_docs
from .verify import resolve_citations, slo_coverage
from .academic_search import OpenAlexClient
from .arxiv_search import ArxivClient
from .textbook import TextbookIndex, build_textbook_index
from .discover import fetch_candidate_sources, filter_relevant, course_terms

__all__ = [
    "SourceDoc",
    "SourcePool",
    "GroundingStrength",
    "GROUNDED_OR_SILENT_RULE",
    "build_pool",
    "assemble_pool",
    "serper_to_docs",
    "resolve_citations",
    "slo_coverage",
    "OpenAlexClient",
    "ArxivClient",
    "TextbookIndex",
    "build_textbook_index",
    "fetch_candidate_sources",
]
