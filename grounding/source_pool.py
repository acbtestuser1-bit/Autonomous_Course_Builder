"""
Source-pool builder.

Phase 1: current-context (Serper) only — reframes the existing web-search
results as numbered, citable tier-3 sources.
Phase 2 will pass `academic_results` (OpenAlex); Phase 3 `textbook_results`.
The tier ordering and numbering live here so callers stay simple.
"""
from typing import Any, Dict, List, Optional

from .models import SourceDoc, SourcePool, GroundingStrength


def _dedupe_key(title: str, doi: str = "") -> str:
    if doi:
        return f"doi:{doi.lower()}"
    return "t:" + " ".join((title or "").lower().split())


def serper_to_docs(serper_results: Optional[List[Dict[str, Any]]]) -> List[SourceDoc]:
    """Convert raw Serper parsed results into tier-3 (current/industry) SourceDocs."""
    docs: List[SourceDoc] = []
    for r in (serper_results or []):
        docs.append(SourceDoc(
            id=0,
            tier=3,
            title=(r.get("title") or "").strip() or "Untitled source",
            text=r.get("snippet", "") or "",
            year=str(r.get("date", "") or ""),
            url=r.get("link", "") or "",
        ))
    return docs


def assemble_pool(docs_in: List[SourceDoc]) -> SourcePool:
    """Number + dedupe an ordered set of SourceDocs (tier already set) and compute
    grounding strength. Sorted by tier so textbook→research→current numbering is stable.

    All three tiers are first-class grounding — the tier only affects citation
    style and ordering, not whether a source 'counts'.
    """
    docs: List[SourceDoc] = []
    seen: set = set()
    next_id = 1
    for d in sorted(docs_in or [], key=lambda x: x.tier):
        key = _dedupe_key(d.title, d.doi)
        if not d.title or key in seen:
            continue
        seen.add(key)
        d.id = next_id
        docs.append(d)
        next_id += 1

    has_textbook = any(d.tier == 1 for d in docs)
    has_external = any(d.tier in (2, 3) for d in docs)
    if has_textbook:
        strength = GroundingStrength.STRONG  # instructor's own material is the best grounding
    elif has_external:
        strength = GroundingStrength.MEDIUM
    else:
        strength = GroundingStrength.LIGHT

    return SourcePool(docs=docs, strength=strength)


def build_pool(serper_results: Optional[List[Dict[str, Any]]] = None,
               academic_results: Optional[List[SourceDoc]] = None,
               textbook_results: Optional[List[SourceDoc]] = None) -> SourcePool:
    """Assemble a pool from raw search outputs (textbook + academic + current)."""
    combined: List[SourceDoc] = []
    for d in (textbook_results or []):
        d.tier = 1
        combined.append(d)
    for d in (academic_results or []):
        d.tier = 2
        combined.append(d)
    combined.extend(serper_to_docs(serper_results))
    return assemble_pool(combined)
