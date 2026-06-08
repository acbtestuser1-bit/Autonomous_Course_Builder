# Page One (Syllabus) — Redesign Spec

**Target folder:** `ai-course-builder-deploy_prompts/` (the deployed-equivalent codebase)
**Scope:** Page one only (the Syllabus tab). Other tabs unchanged for now.
**Hard constraints:** No new paid services / no added per-run cost. Keep Railway footprint light. Folders stay separate (no merging the three variants).

---

## 1. Goals

1. **Make the textbook the spine of generation** — and degrade gracefully when there's no textbook.
2. **Replace weak Serper web search** with real academic sources (research papers, DOIs).
3. **Eliminate fabricated statistics** — the model may only state facts it can attribute to a provided source.
4. **Reduce input friction** — collapse the long required-field wall; make sources visible and curatable.
5. **Reframe quality academically** — optimize for *constructive alignment* (SLO ↔ assessment ↔ schedule ↔ Bloom), not impressive-sounding prose.

Non-goals (this page): voice/video, the other three tabs, multi-user persistence.

---

## 2. Current state (verified in code)

| Area | Current behavior | File:line | Problem |
|---|---|---|---|
| Textbook upload | Full-text `PyPDF2` extract, **all pages concatenated into one string**, dumped raw into the prompt | [utils.py:281](utils.py#L281), [ui_components.py:345](ui_components.py#L345) | Overflows context, costs a fortune, garbage on multi-column PDFs, no retrieval. Only works for a short sample syllabus. |
| Web search | Generic Google-via-Serper with `"... 2024 2025"` appended; only 200-char snippets reach the model | [serper_service.py:30](serper_service.py#L30), [serper_service.py:112](serper_service.py#L112) | Not academic. No papers/DOIs. Model never reads full source. |
| Intro prompt | **Commands** "cite exact numbers, dates, companies"; gives fabricated-looking examples | [prompts.py:50-86](prompts.py#L50-L86) | Structurally induces hallucinated statistics. |
| Grounding reach | `current_references` injected only into **introduction** + **materials** | [generators.py:237,241](generators.py#L237-L241) | Schedule, assessment, overview generated blind. |
| Schedule | Week themes invented by LLM as JSON, no source | [generators.py:131-174](generators.py#L131-L174) | Generic topic lists; ignores the actual textbook. |
| Failure mode | `_search_current_references` **raises** if Serper fails | [generators.py:99](generators.py#L99) | No grounding floor. |
| Prompt plumbing | `pm.get_prompt(cat, name, **kwargs)` → `template.format(**kwargs)`; user can override any template; missing `{var}` returns raw template | [prompt_manager.py:38-72](prompt_manager.py#L38-L72) | **Grounding must NOT depend on a `{sources}` placeholder** a custom prompt could drop. |
| Input form | ~16 required fields, long top-to-bottom wall | [app.py:121-296](app.py#L121-L296) | High friction; sources are buried/optional. |

---

## 3. Design principles

- **Grounded-or-silent.** No claim with a specific number/name unless a source supports it. If unsupported → general language, no invented figure.
- **Sources injected out-of-band.** Grounded source pool is prepended as a dedicated `SystemMessage` in the message list, *not* only via an editable `{sources}` placeholder — so customized prompts can't accidentally strip grounding. (Editable templates still get an optional `{sources}` for display, but the system block is the guarantee.)
- **Always have a floor.** Tier 2 (academic API) is always available, so the no-textbook path is still grounded. Never hard-raise on a single source failure.
- **No new costs.** OpenAlex (free, keyless) for papers; BM25 lexical retrieval for the textbook (no paid embeddings). PDF text via `pdfplumber` (MIT). Everything reuses the existing OpenAI key only for generation, as today.

---

## 4. Target architecture

```
            ┌──────────────────────── SOURCE POOL BUILDER ───────────────────────┐
            │                                                                     │
 textbook → │  Tier 1  pdfplumber extract → ToC parse → section-aware chunk →     │
 (optional) │          BM25 index   ──(retrieve top-k per topic/section)──┐       │
            │                                                             │       │
 topic   ─→ │  Tier 2  OpenAlex API (ALWAYS) → real papers w/ abstract+DOI ├─► SourcePool
            │          [Crossref/arXiv optional later]                    │   (numbered,
            │                                                             │    deduped,
 optional → │  Tier 3  Serper (DEMOTED) → "current context" only ─────────┘    tiered)
            │                                                                     │
            └─────────────────────────────────────────────────────────────────────┘
                                          │
                                          ▼
            ┌──────────────── GROUNDED SECTION GENERATION ───────────────┐
            │ per section: retrieve relevant subset → build SystemMessage │
            │ "SOURCES [1..n] ... cite [k]; never invent numbers" →       │
            │ LLM → section text with inline [k] citations                │
            └─────────────────────────────────────────────────────────────┘
                                          │
                                          ▼
            ┌──────────────── VERIFY + QA ───────────────┐
            │ citation resolver: every [k] maps to a real │
            │ source; strip/flag orphans. SLO-coverage    │
            │ check. Grounding-strength label.            │
            └─────────────────────────────────────────────┘
```

---

## 5. Component specs

### 5.1 New module `grounding/` (new files)

```
grounding/
  __init__.py
  models.py          # SourceDoc, Citation, SourcePool, GroundingStrength
  textbook.py        # extract → ToC parse → chunk → BM25 index + retrieve
  academic_search.py # OpenAlex client (+ optional Crossref/arXiv)
  source_pool.py     # merge tiers, dedupe, number, format for prompt
  verify.py          # citation resolution + faithfulness check
```

**`models.py`**
```python
@dataclass
class SourceDoc:
    id: int                     # stable index in the pool: [1], [2], ...
    tier: int                   # 1 textbook, 2 academic, 3 current
    title: str
    text: str                   # chunk text or abstract (the groundable content)
    authors: str = ""           # academic
    year: str = ""
    doi: str = ""               # academic → citation
    url: str = ""
    locator: str = ""           # textbook: "Ch 3, pp. 41-58"

class GroundingStrength(str, Enum):
    STRONG = "Strong (textbook + literature)"
    MEDIUM = "Medium (literature only)"
    LIGHT  = "Light (no sources — generic, uncited)"

@dataclass
class SourcePool:
    docs: list[SourceDoc]
    strength: GroundingStrength
    def for_topic(self, topic: str, k: int) -> list[SourceDoc]: ...  # BM25 over docs
    def render_for_prompt(self, subset: list[SourceDoc]) -> str: ...  # numbered block
    def bibliography_md(self) -> str: ...                            # References section
```

**`textbook.py`**
- `extract_text(file) -> list[Page]` using `pdfplumber` (fallback to existing PyPDF2 if pdfplumber fails). DOCX/TXT/MD reuse current `process_uploaded_file`.
- `parse_toc(pages) -> list[TocEntry]` — detect a contents page (regex on "Contents", dotted leaders, chapter numbering). Used to (a) seed the weekly schedule, (b) label chunk locators.
- `chunk(pages, toc) -> list[SourceDoc(tier=1)]` — section-aware: split on detected chapter/section boundaries, then pack to ~600–800 tokens with ~80-token overlap. Locator = chapter + page range.
- `Index(docs)` — wraps `rank_bm25.BM25Okapi`; `retrieve(query, k)` returns top-k chunks. Pure-python, no embeddings, no GPU, ~no memory cost.
- Held in `st.session_state` for the session (rebuilt only when a new file is uploaded).

**`academic_search.py`** (Tier 2 — replaces weak Serper for academic grounding)
- OpenAlex `GET https://api.openalex.org/works?search=<q>&filter=...&per_page=k&mailto=<contact>`
  - Free, no API key, ~100k/day with polite pool. Returns title, authorships, publication_year, DOI, abstract (reconstruct from `abstract_inverted_index`), open-access URL.
- `search(topic, k) -> list[SourceDoc(tier=2)]`. Filters: recent-ish but not hard-gated to 2024/2025 (academic relevance ≠ recency). Prefer works with abstracts.
- Resilient: timeout + empty-list on failure (never raises).
- Optional later: Crossref (`api.crossref.org`, free) for DOI completeness; arXiv for CS/preprints. Flagged, not in Phase 1–3.

**`source_pool.py`**
- `build(course_context, topic, textbook_index, use_serper) -> SourcePool`
  - Tier 1: `textbook_index.retrieve(topic, k1)` if a textbook exists.
  - Tier 2: `academic_search.search(topic, k2)` — always.
  - Tier 3: Serper current-context, only if user opts in; tagged tier 3, never used for academic claims.
  - Merge, dedupe (by DOI/title), assign stable `id`s, compute `GroundingStrength`.

**`verify.py`**
- `resolve_citations(text, pool) -> (clean_text, report)` — find `[k]` markers; drop/flag any `k` not in pool; produce a coverage report (which sources were actually cited).
- `slo_coverage(text, slos) -> report` — lightweight check that each SLO code appears / is addressed.
- (Optional, cheap) `faithfulness(text, pool)` — one LLM-judge pass: "does each cited claim match its source snippet?" Reuses existing model; one extra call per generation, gated behind a flag so cost stays opt-in.

### 5.2 Generator changes (`generators.py` — `SyllabusGenerator`)

- `__init__`: build/lookup textbook index from session; keep Serper optional.
- **Replace** `_search_current_references` → `_build_source_pool(course_context, topic)` returning a `SourcePool`. Never raises.
- **Schedule grounding:** `_generate_schedule_metadata` — if a textbook ToC exists, seed `week_theme`s from chapters (map N chapters → `weeks`); else fall back to current LLM-JSON path. ToC-seeded schedule is the single biggest "uses the textbook" win.
- **Inject sources into every content section**, not just intro/materials. Each `_generate_*_section` gets the relevant source subset and prepends a grounding `SystemMessage`:
  ```
  SOURCES (cite as [n]; you may ONLY state specific facts/numbers found here;
  if a claim has no source, write it generally and add no number):
  [1] (textbook, Ch 3 pp.41-58) ...text...
  [2] (Smith & Lee 2023, doi:10.xxxx) ...abstract...
  ```
  This block is added in the message list in the generator, independent of the editable template → survives prompt customization.
- `_build_rationale`: report grounding strength, #sources, #citations, SLO coverage (replaces the unconditional "Current references ... included via live search" line).

### 5.3 Prompt rewrites (`prompts.py` — `SYLLABUS_PROMPTS`)

Concrete change for the worst offender, **introduction**:

- **Remove** the "Open with SPECIFIC 2024-2025 event/data point — cite exact numbers" block and the fabricated examples ([prompts.py:50-86](prompts.py#L50-L86)).
- **Replace** with citation-required, grounded framing:
  > Write a substantive introduction for {course_name} ({program_type}). Ground every specific claim in the SOURCES provided to you and cite as [n]. Do **not** invent statistics, dates, company figures, or studies. If you lack a source for a specific number, describe the idea qualitatively instead. Open by motivating why this subject matters to a {program_type} learner, anchored in the course's themes and (if available) the assigned textbook.
- Apply the same "grounded-or-silent" clause to `materials`, `assessment`, `course_overview`, `schedule`.
- Keep the existing anti-pattern list (no "in today's world," etc.) — that part is good.
- **System messages** that currently say "grounded in specific 2024-2025 events and data" ([generators.py:291](generators.py#L291)) and "specific example prompts using real companies" ([generators.py:410](generators.py#L410)) → reworded to "grounded in the provided sources; no fabricated specifics."
- Because templates are user-overridable, defaults carry `{sources}` for display, but the generator's system block is the real guarantee (see 5.2).

### 5.4 UX redesign (`app.py` `render_syllabus_tab`, `ui_components.py`)

- **Progressive disclosure.** Top: a compact "Course Basics" card (code, name, program, weeks, sessions, duration). Collapse Professor details, AI policy, advanced suggestion settings into `st.expander`s. Make professor contact fields **optional** (they don't affect content quality; only header rendering).
- **"Course Materials & Sources" panel** (new, first-class, above Generate):
  - Textbook uploader (drag-drop) → on upload: extract + index + show *"✓ Indexed: 312 pages, 14 chapters, 480 chunks."*
  - Live "Papers found: N" from OpenAlex preview for the course name.
  - **Grounding-strength meter**: Strong / Medium / Light, with one-line explanation.
  - Curate: list retrieved papers with checkboxes (drop irrelevant), a "paste DOI" box to add one, optional "include current web context (Serper)" toggle (default off).
- Drop the mandatory free-text "file description" requirement; infer role from tier. (Keep an optional note field.)

### 5.5 Dependencies (all free / MIT-ish)

```
pdfplumber>=0.11      # MIT — better text extraction than PyPDF2
rank-bm25>=0.2.2      # Apache-2.0 — pure-python lexical retrieval, no embeddings
# (no torch, no sentence-transformers, no paid embedding API)
```
OpenAlex/Crossref/arXiv: HTTP only, no SDK, no key. Reuse existing `aiohttp`.

---

## 6. File-by-file change list

**New**
- `grounding/__init__.py`, `models.py`, `textbook.py`, `academic_search.py`, `source_pool.py`, `verify.py`

**Modified**
- `generators.py` — `SyllabusGenerator`: source pool, per-section injection, ToC-seeded schedule, grounded rationale.
- `prompts.py` — rewrite `SYLLABUS_PROMPTS` (intro, materials, assessment, overview, schedule) to grounded/cited; add `{sources}` display var.
- `serper_service.py` — keep, demote to Tier 3 "current context" only.
- `utils.py` — `process_uploaded_file`: route PDFs through `grounding.textbook` (pdfplumber + fallback).
- `ui_components.py` — replace `render_file_upload_section` with the Sources panel; progressive-disclosure helpers.
- `app.py` — `render_syllabus_tab`: reorder into Basics + expanders + Sources panel; pass curated pool into generation.
- `qa_agent.py` — add citation-faithfulness + SLO-coverage signals to the syllabus review.
- `requirements.txt` — add `pdfplumber`, `rank-bm25`.
- `config.py` — add `GroundingStrength` import path / any new context fields if needed.

---

## 7. Phased rollout (each independently shippable + testable)

| Phase | Deliverable | Acceptance criteria | Est. |
|---|---|---|---|
| **1. De-hallucinate** | Prompt rewrites + grounded SystemMessage scaffold + citation resolver (`verify.resolve_citations`). No new sources yet — just stop fabrication and enforce "grounded-or-silent." | Generated intro/assessment contain **no invented statistics**; any `[n]` resolves or is stripped; QA reports citation coverage. | small |
| **2. Academic tier** | `academic_search.py` (OpenAlex) + `source_pool.py`; inject into all sections; References section with DOIs. | No-textbook generation cites ≥3 real papers with working DOIs; Serper demoted/optional. | medium |
| **3. Textbook RAG** | `textbook.py` (pdfplumber + ToC + BM25); ToC-seeded schedule; per-section chunk retrieval with chapter/page locators. | A real 200+ page PDF indexes without context overflow; schedule mirrors chapters; sections cite chapter/page. | medium |
| **4. UX** | Progressive-disclosure form + Sources panel + grounding-strength meter + curation. | New-instructor "time to first generate" drops; sources visible & editable pre-generation. | medium |

Recommended order = 1 → 2 → 3 → 4 (cheapest, highest-credibility win first; UX last once the data model is settled).

---

## 8. Risks / open questions

- **PDF variety.** Scanned/image-only textbooks have no text layer → pdfplumber returns empty. Mitigation: detect and warn ("this PDF appears scanned; OCR not supported"), fall to Tier 2. (OCR would add cost/deps — out of scope.)
- **OpenAlex relevance.** Keyword search can be noisy for broad course names. Mitigation: query with course name + top SLO keywords; let the instructor curate in the Sources panel.
- **BM25 vs semantic.** Lexical retrieval is weaker than embeddings for paraphrase. Acceptable because (a) topic↔chapter vocabulary overlaps heavily and (b) ToC mapping handles structure. Embeddings remain a future opt-in upgrade on the existing OpenAI key (negligible cost) if quality demands it.
- **Custom-prompt drift.** Users who heavily edit prompts could weaken citation instructions. Mitigation: the generator's system block (not the editable template) carries the binding "grounded-or-silent" rule.
- **Latency.** Per-section retrieval + an optional faithfulness pass add calls. Mitigation: retrieval is local (BM25, instant); faithfulness check is one opt-in call.

---

## 9. What this buys you vs. ChatGPT

After Phase 1–3, page one produces a syllabus whose **specific claims are cited to real papers and the instructor's own textbook**, whose **schedule follows the actual book**, and whose **SLO/assessment alignment is checked** — none of which a raw ChatGPT prompt does reliably. That is the defensible differentiator, achieved with **zero new paid services**.
