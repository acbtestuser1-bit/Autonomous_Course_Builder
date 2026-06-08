"""
Textbook ingestion + retrieval (Tier 1 grounding).

Parses a table of contents (for ToC-seeded scheduling), chunks the text
section-aware, and builds a BM25 lexical index for per-topic retrieval.
Pure-lexical (no embeddings) — free and light on memory.

rank_bm25 is optional at import time; if it is missing the index falls back to
keyword-overlap ranking, so the app never crashes on a fresh environment.
Operates on already-extracted text (the existing upload pipeline handles PDF /
DOCX / TXT extraction), keeping file-object plumbing out of the generator.
"""
import logging
import re
from dataclasses import dataclass
from typing import List, Optional

from .models import SourceDoc

logger = logging.getLogger(__name__)

try:
    from rank_bm25 import BM25Okapi
    _BM25_AVAILABLE = True
except Exception:  # pragma: no cover - optional dep
    _BM25_AVAILABLE = False


# Chapter/section heading detector — matches ToC lines and in-body headings.
_HEADING_RE = re.compile(
    r'^\s*(?:chapter|ch\.?|unit|part|module|section)\s+(\d+|[ivxlcm]+)\b[:.\-\s]*(.+?)\s*$',
    re.IGNORECASE | re.MULTILINE,
)


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", (text or "").lower())


@dataclass
class TocEntry:
    title: str


@dataclass
class Chunk:
    text: str
    locator: str  # e.g. "Chapter 3: Demand"


def parse_toc(text: str) -> List[TocEntry]:
    """Extract an ordered, deduplicated chapter list from the document text."""
    entries: List[TocEntry] = []
    seen = set()
    for m in _HEADING_RE.finditer(text or ""):
        num = m.group(1).strip()
        title = m.group(2).strip()
        # strip dot leaders and trailing page numbers ("Demand ...... 41")
        title = re.sub(r'\.{2,}.*$', '', title).strip()
        title = re.sub(r'[\.\s]*\d+$', '', title).strip()
        if not (3 <= len(title) <= 120):
            continue
        label = f"Chapter {num}: {title}"
        key = label.lower()
        if key not in seen:
            seen.add(key)
            entries.append(TocEntry(title=label))
    return entries[:40]


def _pack(segment: str, locator: str, target_words: int) -> List[Chunk]:
    words = segment.split()
    if not words:
        return []
    out: List[Chunk] = []
    for i in range(0, len(words), target_words):
        out.append(Chunk(text=" ".join(words[i:i + target_words]),
                         locator=locator or "Textbook excerpt"))
    return out


def chunk_text(text: str, target_words: int = 700) -> List[Chunk]:
    """Section-aware chunking: split on chapter headings when present, else pack
    paragraphs to ~target_words."""
    text = (text or "").strip()
    if not text:
        return []

    matches = list(_HEADING_RE.finditer(text))
    chunks: List[Chunk] = []
    if len(matches) >= 3:
        for idx, m in enumerate(matches):
            start = m.start()
            end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
            segment = text[start:end].strip()
            locator = re.sub(r'\s+', ' ', m.group(0)).strip()[:80]
            chunks.extend(_pack(segment, locator, target_words))
    else:
        chunks.extend(_pack(text, "", target_words))
    return chunks


class TextbookIndex:
    """BM25 (or keyword-fallback) retrieval over a chunked textbook."""

    def __init__(self, text: str):
        self.full_text = text or ""
        self.toc = parse_toc(self.full_text)
        self.chunks = chunk_text(self.full_text)
        self._bm25 = None
        self._tokenized: List[List[str]] = []
        if self.chunks:
            self._tokenized = [_tokenize(c.text) for c in self.chunks]
            if _BM25_AVAILABLE:
                try:
                    self._bm25 = BM25Okapi(self._tokenized)
                except Exception as e:  # pragma: no cover
                    logger.warning(f"BM25 init failed, using keyword fallback: {e}")

    @property
    def available(self) -> bool:
        return bool(self.chunks)

    def chapter_titles(self) -> List[str]:
        return [e.title for e in self.toc]

    def retrieve(self, query: str, k: int = 4) -> List[SourceDoc]:
        if not self.chunks:
            return []
        q_tokens = _tokenize(query)
        if self._bm25 is not None:
            scores = self._bm25.get_scores(q_tokens)
            order = sorted(range(len(self.chunks)), key=lambda i: scores[i], reverse=True)
        else:
            q_set = set(q_tokens)
            order = sorted(
                range(len(self.chunks)),
                key=lambda i: len(q_set & set(self._tokenized[i])),
                reverse=True,
            )

        results: List[SourceDoc] = []
        for i in order[:k]:
            c = self.chunks[i]
            results.append(SourceDoc(
                id=0,  # assigned by build_pool
                tier=1,
                title=c.locator or f"Textbook excerpt {i + 1}",
                text=c.text[:1200],
                locator=c.locator,
            ))
        return results


def build_textbook_index(text: str) -> Optional[TextbookIndex]:
    """Build an index from extracted document text; None if there's nothing usable."""
    if not text or not text.strip():
        return None
    idx = TextbookIndex(text)
    if not idx.available:
        return None
    logger.debug(f"Textbook index: {len(idx.chunks)} chunks, {len(idx.toc)} ToC entries, "
                 f"bm25={'on' if idx._bm25 is not None else 'fallback'}")
    return idx
