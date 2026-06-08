"""
Citation resolution and coverage checks.

resolve_citations strips any [n] marker that does not map to a real source in
the pool (i.e. a fabricated citation), and reports which sources were actually
used. slo_coverage checks that each declared SLO code appears in the content.
"""
import re
from typing import Any, Dict, List, Tuple

from .models import SourcePool

_CITE_RE = re.compile(r"\[(\d{1,3})\]")


def resolve_citations(text: str, pool: SourcePool) -> Tuple[str, Dict[str, Any]]:
    valid = pool.ids
    cited: set = set()
    orphans: set = set()

    def repl(match: "re.Match") -> str:
        n = int(match.group(1))
        if n in valid:
            cited.add(n)
            return match.group(0)
        orphans.add(n)
        return ""  # strip fabricated / orphan citation marker

    clean = _CITE_RE.sub(repl, text)
    # tidy artifacts left by stripped markers
    clean = re.sub(r"[ \t]{2,}", " ", clean)
    clean = re.sub(r"\s+([.,;:])", r"\1", clean)

    report = {
        "sources_available": len(valid),
        "citations_used": sorted(cited),
        "citation_count": len(cited),
        "orphans_removed": sorted(orphans),
        "coverage": round(len(cited) / len(valid), 2) if valid else 0.0,
    }
    return clean, report


def slo_coverage(text: str, slo_codes: List[str]) -> Dict[str, Any]:
    lowered = text.lower()
    present = [c for c in slo_codes if c and c.lower() in lowered]
    missing = [c for c in slo_codes if c and c not in present]
    return {
        "slo_total": len([c for c in slo_codes if c]),
        "slo_present": present,
        "slo_missing": missing,
        "slo_coverage": round(len(present) / len(slo_codes), 2) if slo_codes else 0.0,
    }
