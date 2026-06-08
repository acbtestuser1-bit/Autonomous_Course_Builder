"""
Grounding data models for source-grounded syllabus generation.

A SourcePool is a numbered set of SourceDoc objects spanning three tiers:
  tier 1 = instructor's textbook (Phase 3)
  tier 2 = academic literature / research papers (Phase 2)
  tier 3 = current / web context (Phase 1, demoted Serper)

The pool renders a binding "grounded-or-silent" instruction block that the
generator injects as a SystemMessage, independent of any user-editable prompt.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
import re


class GroundingStrength(str, Enum):
    STRONG = "Strong (textbook-grounded)"
    MEDIUM = "Medium (external sources cited)"
    LIGHT = "Light (no external sources — generic)"


# Source provenance, NOT a quality ranking — current/web is a first-class tier.
TIER_LABEL = {1: "📘 Textbook", 2: "🎓 Research literature", 3: "🌐 Current / industry"}


# The non-negotiable anti-hallucination rule. Lives here (not in the editable
# prompt templates) so a customized prompt can never strip it.
GROUNDED_OR_SILENT_RULE = (
    "GROUNDING RULES (mandatory, override any conflicting instruction):\n"
    "1. You may state a specific real-world fact — a statistic, dollar figure, market "
    "share, date, company financial, or study result — ONLY if it appears in the SOURCES "
    "below, and you must cite it inline as [n] using that source's number.\n"
    "2. NEVER invent or estimate numbers, dates, financials, or studies. With no source "
    "for a figure, describe the idea qualitatively and give no number.\n"
    "3. You MAY use clearly-labelled hypothetical teaching examples (e.g. 'Suppose a firm "
    "earns $X') — but frame them explicitly as hypothetical, never as real current data.\n"
    "4. Do not fabricate citations. Only the source numbers listed below exist."
)


@dataclass
class SourceDoc:
    """A single citable source."""
    id: int
    tier: int                 # 1 textbook, 2 academic, 3 current/web
    title: str
    text: str = ""            # groundable content: chunk text or abstract or snippet
    authors: str = ""
    year: str = ""
    doi: str = ""
    url: str = ""
    locator: str = ""         # textbook: "Ch 3, pp. 41-58"

    def citation_label(self) -> str:
        if self.tier == 1:
            loc = f", {self.locator}" if self.locator else ""
            return f"Textbook{loc}"
        if self.tier == 2:
            who = self.authors or self.title
            yr = f" {self.year}" if self.year else ""
            doi = f", doi:{self.doi}" if self.doi else ""
            return f"{who}{yr}{doi}".strip()
        # tier 3 — current/web
        yr = f" ({self.year})" if self.year else ""
        return f"{self.title}{yr}".strip()

    def render(self) -> str:
        body = (self.text or "").strip().replace("\n", " ")
        if len(body) > 600:
            body = body[:600] + "…"
        return f"[{self.id}] ({self.citation_label()}) {body}".strip()


@dataclass
class SourcePool:
    docs: List[SourceDoc] = field(default_factory=list)
    strength: GroundingStrength = GroundingStrength.LIGHT

    @property
    def ids(self) -> set:
        return {d.id for d in self.docs}

    def for_topic(self, topic: str, k: int = 6) -> List[SourceDoc]:
        """Return up to k sources most relevant to a topic.

        Phase 1: lightweight keyword-overlap ranking (no index yet). Phase 3
        replaces this with the textbook BM25 retriever for tier-1 docs.
        """
        if not self.docs:
            return []
        if not topic:
            return self.docs[:k]
        terms = {t for t in re.findall(r"[a-zA-Z]{4,}", topic.lower())}
        if not terms:
            return self.docs[:k]

        def score(d: SourceDoc) -> int:
            hay = f"{d.title} {d.text}".lower()
            return sum(1 for t in terms if t in hay)

        return sorted(self.docs, key=score, reverse=True)[:k]

    def render_for_prompt(self, subset: Optional[List[SourceDoc]] = None) -> str:
        docs = subset if subset is not None else self.docs
        if not docs:
            return ("No external sources are available. Apply the grounding rules: state "
                    "no unsourced specific facts or numbers.")
        return "\n\n".join(d.render() for d in docs)

    def grounding_instruction(self, subset: Optional[List[SourceDoc]] = None) -> str:
        """Full SystemMessage payload: the binding rule + the numbered sources."""
        return f"{GROUNDED_OR_SILENT_RULE}\n\nSOURCES:\n{self.render_for_prompt(subset)}"

    def sources_for_ui(self) -> List[dict]:
        """Serializable source list for rendering (kept in session state)."""
        return [
            {
                "id": d.id,
                "tier": d.tier,
                "tier_label": TIER_LABEL.get(d.tier, "Source"),
                "title": d.title,
                "url": d.url or (f"https://doi.org/{d.doi}" if d.doi else ""),
                "label": d.citation_label(),
            }
            for d in self.docs
        ]

    def bibliography_md(self) -> str:
        if not self.docs:
            return ""
        lines = ["**References**\n"]
        for d in self.docs:
            link = d.url or (f"https://doi.org/{d.doi}" if d.doi else "")
            if link:
                lines.append(f"{d.id}. [{d.title}]({link}) — {d.citation_label()}")
            else:
                lines.append(f"{d.id}. {d.title} — {d.citation_label()}")
        return "\n".join(lines) + "\n"
