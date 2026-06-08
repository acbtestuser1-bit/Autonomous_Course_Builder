"""
Content Generators - COMPLETE with PromptManager integration
"""

import logging
import json
import streamlit as st
from typing import Tuple, Optional, List, Dict
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from config import CourseContext, GeneratedContent, LectureFormat, get_program_appendix, get_ai_policy_text, get_all_course_slos, ProgramType
from serper_service import SerperSearchService
from qa_agent import QualityAssuranceAgent
from utils import format_slos_for_prompt, format_slos_for_content
from prompt_manager import get_prompt_manager
import asyncio
from grounding import (
    build_pool, assemble_pool, resolve_citations, slo_coverage,
    SourcePool, SourceDoc, OpenAlexClient, ArxivClient, fetch_candidate_sources,
)
from grounding.textbook import TextbookIndex


logger = logging.getLogger(__name__)


class _TopicGroundingMixin:
    """Shared topic-level grounding for the lecture & assignment generators.

    Expects the host class to set: self.source_pool, self.textbook_index,
    self.include_web, self.search_service.
    """

    async def _build_source_pool(self, topic: str, course_context: "CourseContext") -> SourcePool:
        """Build a citable pool grounded in THIS topic. Never raises."""
        textbook_results = []
        if getattr(self, "textbook_index", None) is not None and self.textbook_index.available:
            try:
                textbook_results = self.textbook_index.retrieve(topic, k=4)
            except Exception as e:
                logger.warning(f"Textbook retrieval failed: {e}")
        try:
            external = await fetch_candidate_sources(
                topic, getattr(self, "include_web", True), self.search_service.api_key
            )
        except Exception as e:
            logger.warning(f"Source discovery failed: {e}")
            external = []
        pool = assemble_pool(textbook_results + external)
        logger.debug(f"Topic pool ({topic}): {len(pool.docs)} docs, strength={pool.strength.value}")
        return pool

    def _grounding_messages(self, topic: str = "") -> list:
        """Binding grounded-or-silent SystemMessage + topic-relevant sources."""
        pool = getattr(self, "source_pool", None) or SourcePool()
        subset = pool.for_topic(topic, k=6) if topic else None
        return [SystemMessage(content=pool.grounding_instruction(subset))]


class SyllabusGenerator:
    """Syllabus generator with structured metadata and complexity hierarchy."""

    def __init__(self, api_key: str, serper_api_key: str, model_type: str = "gpt-4-turbo"):
        self.llm = ChatOpenAI(api_key=api_key, model=model_type, temperature=0.7)
        self.qa_agent = QualityAssuranceAgent(api_key, model_type)
        self.search_service = SerperSearchService(serper_api_key)
        self.pm = get_prompt_manager()
        self.source_pool = SourcePool()  # populated per-generation by _build_source_pool
        self.textbook_index: Optional[TextbookIndex] = None  # set by the caller if a textbook was uploaded
        self.curated_sources: Optional[List[SourceDoc]] = None  # pre-selected sources from the preview; None => search live
        self.include_web = True  # honor the "include current/industry web sources" toggle on the live path
    
    async def generate(self, course_context: CourseContext, 
                  custom_prompt: Optional[str] = None,
                  status_container=None) -> Tuple[GeneratedContent, dict]:
        """Generate syllabus with structured metadata and status updates."""
        
        def update_status(msg):
            if status_container:
                status_container.update(label=msg)
        
        try:
            logger.debug("Starting syllabus generation")
            
            update_status("🔍 Searching for current references...")
            logger.debug("Building source pool...")
            self.source_pool = await self._build_source_pool(course_context)
            current_references = self.source_pool.render_for_prompt()
            
            update_status("📝 Generating syllabus sections...")
            logger.debug("Generating syllabus sections with complexity level...")

            update_status("📅 Creating course schedule...")
            logger.debug("Generating structured schedule metadata...")
            schedule_metadata = await self._generate_schedule_metadata(course_context)
            logger.debug(f"Schedule metadata generated: {len(schedule_metadata)} weeks, {sum(len(week['sessions']) for week in schedule_metadata)} total sessions")

            sections = await self._generate_syllabus_sections(course_context, current_references, custom_prompt, schedule_metadata)

            update_status("📋 Assembling syllabus...")
            logger.debug("Assembling final syllabus...")
            final_content = self._assemble_syllabus(sections, course_context)

            # Citation enforcement: strip any fabricated [n] markers, append references.
            final_content, citation_report = resolve_citations(final_content, self.source_pool)
            bibliography = self.source_pool.bibliography_md()
            if bibliography:
                final_content = f"{final_content}\n\n{bibliography}"
            logger.debug(
                f"Citations: {citation_report['citation_count']} used, "
                f"{len(citation_report['orphans_removed'])} orphans removed"
            )

            update_status("✅ Running quality assurance...")
            logger.debug("Running QA review...")
            qa_review = await self.qa_agent.review_content(final_content, "syllabus", course_context)
            logger.debug(f"QA score: {qa_review['overall_score']}/100, passed: {qa_review.get('passed_qa', False)}")

            # Attach grounding metrics for the rationale + UI.
            slo_codes = [s.get("code", "") for s in get_all_course_slos(course_context)]
            qa_review["grounding"] = {
                "strength": self.source_pool.strength.value,
                "sources": self.source_pool.sources_for_ui(),
                **citation_report,
                **slo_coverage(final_content, slo_codes),
            }
            
            current_version = 1
            if hasattr(st, 'session_state') and hasattr(st.session_state, 'regeneration_count'):
                current_version = st.session_state.regeneration_count + 1

            generated_content = GeneratedContent(
                content=final_content,
                rationale=self._build_rationale(course_context, qa_review),
                quality_score=qa_review["overall_score"],
                suggestions=qa_review["recommendations"],
                version=current_version,
                timestamp=datetime.now(),
                schedule_metadata=schedule_metadata,
                suggestion_history=[]
            )
            
            update_status("✨ Complete!")
            
            logger.debug(f"SLO integration: {len(course_context.selected_slos + course_context.custom_slos)} SLOs integrated")
            
            return generated_content, qa_review
            
        except Exception as e:
            logger.error(f"Syllabus generation failed: {e}", exc_info=True)
            raise Exception(f"Syllabus generation failed: {e}")
    
    async def _build_source_pool(self, course_context: CourseContext) -> SourcePool:
        """Build a numbered, citable source pool. Never raises — degrades to an
        empty pool (the grounding rule still forbids fabrication).

        Three first-class tiers, fetched concurrently:
          - academic: OpenAlex + arXiv (peer-reviewed + preprints, free, no key)
          - current/industry: Serper, aimed at recent developments instructors
            love to teach (e.g. "AI in marketing")
        Phase 3 adds the textbook tier. Each source degrades to [] on failure.
        """
        topic = course_context.course_name

        # Tier 1 — instructor's textbook (retrieved chunks for this course)
        textbook_results: List[SourceDoc] = []
        if self.textbook_index is not None and self.textbook_index.available:
            try:
                textbook_results = self.textbook_index.retrieve(topic, k=4)
            except Exception as e:
                logger.warning(f"Textbook retrieval failed: {e}")

        # If the instructor curated sources in the preview, use exactly those
        # (no re-search). Otherwise discover academic + current sources live.
        if self.curated_sources is not None:
            external = list(self.curated_sources)
            logger.debug(f"Using {len(external)} curated external sources (preview selection)")
            pool = assemble_pool(textbook_results + external)
        else:
            async def _openalex():
                try:
                    return await OpenAlexClient().search(topic, k=4)
                except Exception as e:
                    logger.warning(f"OpenAlex search failed: {e}")
                    return []

            async def _arxiv():
                try:
                    return await ArxivClient().search(topic, k=3)
                except Exception as e:
                    logger.warning(f"arXiv search failed: {e}")
                    return []

            async def _current():
                if not self.include_web:
                    return []  # honor the web-sources toggle (avoids the Serper call/cost)
                # Recent real-world developments & applications — not syllabus boilerplate.
                try:
                    query = f"{topic} latest developments and industry applications"
                    return await self.search_service.search_industry_resources(query, 5)
                except Exception as e:
                    logger.warning(f"Current-context (Serper) search failed: {e}")
                    return []

            openalex, arxiv, serper_results = await asyncio.gather(_openalex(), _arxiv(), _current())
            academic_results = (openalex or []) + (arxiv or [])
            pool = build_pool(
                serper_results=serper_results,
                academic_results=academic_results,
                textbook_results=textbook_results,
            )

        logger.debug(f"Source pool: {len(pool.docs)} docs, strength={pool.strength.value}")
        return pool

    def _grounding_messages(self, topic: str = "") -> list:
        """SystemMessage(s) carrying the binding grounded-or-silent rule + sources.

        Injected by the generator (not the editable prompt template) so a
        customized prompt can never strip the anti-hallucination guarantee.
        """
        pool = self.source_pool or SourcePool()
        subset = pool.for_topic(topic, k=6) if topic else None
        return [SystemMessage(content=pool.grounding_instruction(subset))]
    
    def _get_complexity_instructions(self, program_type: str) -> str:
        """Get complexity instructions based on program hierarchy."""
        if program_type == ProgramType.UNDERGRADUATE.value:
            return """
            COMPLEXITY LEVEL: UNDERGRADUATE
            - Focus on foundational concepts and basic applications
            - Emphasize learning and skill development
            - Use clear, accessible language
            - Include guided practice and scaffolded assignments
            - Assess basic understanding and application
            """
        elif program_type == ProgramType.KELLEY_DIRECT.value:
            return """
            COMPLEXITY LEVEL: GRADUATE (ONLINE) - KELLEY DIRECT
            - Advance beyond undergraduate concepts to strategic thinking
            - Emphasize practical application in professional contexts
            - Include real-world case studies and scenarios
            - Expect independent analysis and synthesis
            - Assess critical thinking and professional application
            """
        else:  # MBA
            return """
            COMPLEXITY LEVEL: GRADUATE (RESIDENTIAL MBA) - HIGHEST
            - Require sophisticated analysis and strategic thinking
            - Emphasize leadership and executive decision-making
            - Include complex case studies and consulting-level projects
            - Expect original insights and innovative solutions
            - Assess executive-level competencies and thought leadership
            """
    
    async def _generate_schedule_metadata(self, course_context: CourseContext) -> List[Dict]:
        """Generate structured schedule metadata for easy parsing."""
        
        complexity_instructions = self._get_complexity_instructions(course_context.program_type)
        
        # MODIFIED: Use PromptManager
        prompt = self.pm.get_prompt(
            'syllabus',
            'schedule_metadata',
            course_name=course_context.course_name,
            complexity_instructions=complexity_instructions,
            weeks=course_context.weeks,
            sessions_per_week=course_context.sessions_per_week,
            duration_per_session=course_context.duration_per_session,
            teaching_style=course_context.teaching_style,
            program_type=course_context.program_type
        )
        
        sys_content = (
            f"You generate structured course schedules for {course_context.course_name}. "
            f"Return only valid JSON."
        )
        # ToC-seeded scheduling: if a textbook was uploaded, base weekly themes on its
        # table of contents so the syllabus follows the actual book.
        if self.textbook_index is not None and self.textbook_index.available:
            titles = self.textbook_index.chapter_titles()
            if titles:
                toc_block = "\n".join(f"- {t}" for t in titles[:40])
                sys_content += (
                    " Base the weekly themes on the following textbook table of contents, "
                    "preserving its order and distributing the chapters across the available weeks:\n"
                    + toc_block
                )
                logger.debug(f"ToC-seeded schedule from {len(titles)} textbook chapters")

        messages = [
            SystemMessage(content=sys_content),
            HumanMessage(content=prompt)
        ]

        response = await self.llm.ainvoke(messages)

        try:
            content = response.content.strip()
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                json_text = content[json_start:json_end].strip()
            else:
                json_text = content
            
            schedule_data = json.loads(json_text)
            
            if isinstance(schedule_data, list) and len(schedule_data) > 0:
                return schedule_data
            else:
                raise ValueError("Invalid schedule structure")
                
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse schedule JSON: {e}")
            return self._generate_fallback_schedule(course_context)
    
    def _generate_fallback_schedule(self, course_context: CourseContext) -> List[Dict]:
        """Generate fallback schedule if JSON parsing fails."""
        logger.debug("Using fallback schedule generation")
        
        base_topics = [
            "Introduction and Fundamentals",
            "Core Concepts and Theory", 
            "Analysis and Application",
            "Strategic Framework",
            "Advanced Concepts",
            "Case Study Analysis",
            "Integration and Synthesis",
            "Contemporary Issues",
            "Practical Applications",
            "Leadership and Ethics",
            "Global Perspectives",
            "Innovation and Change",
            "Future Trends",
            "Comprehensive Review",
            "Final Integration",
            "Assessment and Reflection"
        ]
        
        schedule = []
        for week in range(1, course_context.weeks + 1):
            week_theme = base_topics[min(week-1, len(base_topics)-1)]
            
            sessions = []
            for session_num in range(1, course_context.sessions_per_week + 1):
                session_topic = f"{week_theme} - Part {session_num}"
                sessions.append({
                    "session": f"{week}.{session_num}",
                    "topic": session_topic,
                    "duration": course_context.duration_per_session
                })
            
            schedule.append({
                "week": week,
                "week_theme": f"Week {week}: {week_theme}",
                "sessions": sessions
            })
        
        return schedule
    
    async def _generate_syllabus_sections(self, course_context: CourseContext, 
                                    current_references: str, 
                                    custom_prompt: Optional[str],
                                    schedule_metadata: List[Dict]) -> Dict[str, str]:
        """Generate syllabus sections with custom prompt integration."""
        
        sections = {}
        complexity_instructions = self._get_complexity_instructions(course_context.program_type)
        
        all_slos = get_all_course_slos(course_context)
        slo_text = format_slos_for_prompt(course_context.selected_slos, course_context.custom_slos)
        
        context_suffix = ""
        if custom_prompt:
            context_suffix = f"\n\nADDITIONAL CONTEXT AND REQUIREMENTS:\n{custom_prompt}"
        
        sections["header"] = await self._generate_header_section(course_context)
        sections["introduction"] = await self._generate_introduction_section(course_context, current_references, complexity_instructions, context_suffix)
        sections["learning_outcomes"] = await self._generate_learning_outcomes_section(course_context, all_slos, complexity_instructions, context_suffix)
        sections["course_overview"] = await self._generate_course_overview_section(course_context, complexity_instructions, context_suffix)
        sections["course_format"] = await self._generate_course_format_section(course_context, context_suffix)
        sections["materials"] = await self._generate_materials_section(course_context, current_references, complexity_instructions, context_suffix)
        sections["assessment"] = await self._generate_assessment_section(course_context, complexity_instructions, context_suffix)
        sections["administrative"] = await self._generate_administrative_section(course_context, context_suffix)
        sections["schedule"] = await self._generate_schedule_section(course_context, schedule_metadata, context_suffix)
        
        return sections
    
    async def _generate_header_section(self, course_context: CourseContext) -> str:
        """Generate syllabus header."""
        
        # MODIFIED: Use PromptManager
        prompt = self.pm.get_prompt(
            'syllabus',
            'header',
            course_code=course_context.course_code,
            course_name_upper=course_context.course_name.upper(),
            semester_upper=course_context.semester.upper(),
            professor_name=course_context.professor_name,
            professor_email=course_context.professor_email,
            office_location=course_context.office_location,
            office_hours=course_context.office_hours,
            sessions_per_week=course_context.sessions_per_week,
            duration_per_session=course_context.duration_per_session
        )
        
        messages = [
            SystemMessage(content=f"Create syllabus header for {course_context.course_name}."),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return response.content
    
    async def _generate_introduction_section(self, course_context: CourseContext, 
                                           current_references: str, complexity_instructions: str, context_suffix: str = "") -> str:
        """Generate course introduction with complexity level."""
        
        # MODIFIED: Use PromptManager
        prompt = self.pm.get_prompt(
            'syllabus',
            'introduction',
            course_name=course_context.course_name,
            complexity_instructions=complexity_instructions,
            program_type=course_context.program_type,
            teaching_style=course_context.teaching_style,
            current_references=current_references,
            context_suffix=context_suffix
        )
        
        messages = self._grounding_messages(course_context.course_name) + [
            SystemMessage(content=f"You are a master course designer writing an introduction grounded ONLY in the provided sources for {course_context.course_name}; never fabricate statistics, dates, or company figures."),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return response.content
    
    async def _generate_learning_outcomes_section(self, course_context: CourseContext, 
                                                all_slos: List[Dict], complexity_instructions: str, context_suffix: str = "") -> str:
        """Generate learning outcomes with SLO integration and complexity."""
        
        slo_content = format_slos_for_content(course_context.selected_slos, course_context.custom_slos, course_context.course_name)
        
        # MODIFIED: Use PromptManager
        prompt = self.pm.get_prompt(
            'syllabus',
            'learning_outcomes',
            course_name=course_context.course_name,
            complexity_instructions=complexity_instructions,
            program_type=course_context.program_type,
            teaching_style=course_context.teaching_style,
            slo_content=slo_content,
            context_suffix=context_suffix
        )
        
        messages = self._grounding_messages(course_context.course_name) + [
            SystemMessage(content=f"You are an expert in measurable learning outcomes and backward design for {course_context.course_name}."),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return response.content
    
    async def _generate_course_overview_section(self, course_context: CourseContext, complexity_instructions: str, context_suffix: str = "") -> str:
        """Generate course overview with complexity level."""
        
        # MODIFIED: Use PromptManager
        prompt = self.pm.get_prompt(
            'syllabus',
            'course_overview',
            course_name=course_context.course_name,
            complexity_instructions=complexity_instructions,
            weeks=course_context.weeks,
            sessions_per_week=course_context.sessions_per_week,
            teaching_style=course_context.teaching_style,
            assessment_preferences=', '.join(course_context.assessment_preferences),
            program_type=course_context.program_type,
            context_suffix=context_suffix
        )
        
        messages = self._grounding_messages(course_context.course_name) + [
            SystemMessage(content=f"Design overview for {course_context.course_name} at {course_context.program_type} level."),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return response.content
    
    async def _generate_course_format_section(self, course_context: CourseContext, context_suffix: str = "") -> str:
        """Generate course format section."""
        
        # MODIFIED: Use PromptManager
        prompt = self.pm.get_prompt(
            'syllabus',
            'course_format',
            course_name=course_context.course_name,
            program_type=course_context.program_type,
            teaching_style=course_context.teaching_style,
            context_suffix=context_suffix
        )
        
        messages = [
            SystemMessage(content=f"Create format guidelines for {course_context.course_name}."),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return response.content
    
    async def _generate_materials_section(self, course_context: CourseContext, 
                                        current_references: str, complexity_instructions: str, context_suffix: str = "") -> str:
        """Generate materials with complexity level."""
        
        # MODIFIED: Use PromptManager
        prompt = self.pm.get_prompt(
            'syllabus',
            'materials',
            course_name=course_context.course_name,
            complexity_instructions=complexity_instructions,
            program_type=course_context.program_type,
            current_references=current_references,
            context_suffix=context_suffix
        )
        
        messages = self._grounding_messages(course_context.course_name) + [
            SystemMessage(content=f"Recommend materials for {course_context.course_name} at {course_context.program_type} level."),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return response.content
    
    async def _generate_assessment_section(self, course_context: CourseContext, complexity_instructions: str, context_suffix: str = "") -> str:
        """Generate assessment with complexity level."""
        
        # MODIFIED: Use PromptManager
        prompt = self.pm.get_prompt(
            'syllabus',
            'assessment',
            course_name=course_context.course_name,
            complexity_instructions=complexity_instructions,
            program_type=course_context.program_type,
            assessment_preferences=', '.join(course_context.assessment_preferences),
            teaching_style=course_context.teaching_style,
            weeks=course_context.weeks,
            context_suffix=context_suffix
        )
        
        messages = self._grounding_messages(course_context.course_name) + [
            SystemMessage(content=f"You are an expert in creating transparent, measurable assessment systems for {course_context.course_name}; example prompts are student research tasks, not asserted facts — never fabricate company metrics."),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return response.content
    
    async def _generate_administrative_section(self, course_context: CourseContext, context_suffix: str = "") -> str:
        """Generate administrative section."""
        
        ai_policy_text = get_ai_policy_text(course_context.ai_classroom_use)
        
        # MODIFIED: Use PromptManager
        prompt = self.pm.get_prompt(
            'syllabus',
            'administrative',
            course_name=course_context.course_name,
            program_type=course_context.program_type,
            professor_name=course_context.professor_name,
            professor_email=course_context.professor_email,
            office_location=course_context.office_location,
            office_hours=course_context.office_hours,
            ai_policy_text=ai_policy_text,
            context_suffix=context_suffix
        )
        
        messages = [
            SystemMessage(content=f"Create administrative details for {course_context.course_name}."),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return response.content
    
    async def _generate_schedule_section(self, course_context: CourseContext, 
                                    schedule_metadata: List[Dict],
                                    context_suffix: str = "") -> str:
        """Generate detailed schedule using metadata topics exactly."""
        
        # Build schedule from metadata FIRST - format as text, not JSON
        schedule_lines = []
        
        for week_data in schedule_metadata:
            week_num = week_data['week']
            week_theme = week_data['week_theme']
            schedule_lines.append(f"\nWeek {week_num}: {week_theme}")
            
            for session in week_data['sessions']:
                session_id = session['session']
                topic = session['topic']
                duration = session['duration']
                
                schedule_lines.append(f"* Session {session_id}: {topic} ({duration} min)")
        
        # NOW use PromptManager with FORMATTED text
        prompt = self.pm.get_prompt(
            'syllabus',
            'schedule',
            course_name=course_context.course_name,
            schedule_metadata="\n".join(schedule_lines),  # FORMATTED TEXT
            program_type=course_context.program_type,
            teaching_style=course_context.teaching_style,
            duration_per_session=course_context.duration_per_session,
            weeks=course_context.weeks,
            context_suffix=context_suffix
        )
        
        messages = self._grounding_messages(course_context.course_name) + [
            SystemMessage(content=f"Create detailed weekly schedule for {course_context.course_name} with explicit worked example structure; use sourced-and-cited or clearly-hypothetical numbers, never fabricated real-world data."),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return response.content
    
    def _assemble_syllabus(self, sections: Dict[str, str], course_context: CourseContext) -> str:
        """Assemble final syllabus with appendix and AI policy."""
        
        appendix = get_program_appendix(course_context.program_type)
        ai_policy = get_ai_policy_text(course_context.ai_classroom_use)
        
        return f"""
{sections["header"]}

{sections["introduction"]}

{sections["learning_outcomes"]}

{sections["course_overview"]}

{sections["course_format"]}

{sections["materials"]}

{sections["assessment"]}

{sections["administrative"]}

{sections["schedule"]}

{ai_policy}

{appendix}
""".strip()
    
    def _build_rationale(self, course_context: CourseContext, qa_review: dict) -> str:
        """Build generation rationale."""
        all_slo_count = len(course_context.selected_slos) + len(course_context.custom_slos)
        g = qa_review.get("grounding", {})
        grounding_line = ""
        if g:
            grounding_line = (
                f"Grounding: {g.get('strength', 'n/a')}; "
                f"{g.get('citation_count', 0)} citations from {g.get('sources_available', 0)} sources; "
                f"{len(g.get('orphans_removed', []))} unsourced claims removed; "
                f"SLO coverage {int(g.get('slo_coverage', 0) * 100)}%."
            )
        return f"""
        Syllabus for {course_context.course_name} generated with complexity level: {course_context.program_type}.
        Teaching methodology: {course_context.teaching_style}
        Integrated {all_slo_count} SLOs ({len(course_context.selected_slos)} program + {len(course_context.custom_slos)} custom).
        Structured schedule: {course_context.weeks} weeks x {course_context.sessions_per_week} sessions.
        {grounding_line}

        Quality Score: {qa_review["overall_score"]}/100
        """


class LectureNotesGenerator(_TopicGroundingMixin):
    """Lecture notes generator with structured topic parsing."""
    
    def __init__(self, api_key: str, serper_api_key: str, model_type: str = "gpt-4-turbo"):
        self.llm = ChatOpenAI(api_key=api_key, model=model_type, temperature=0.7)
        self.qa_agent = QualityAssuranceAgent(api_key, model_type)
        self.search_service = SerperSearchService(serper_api_key)
        self.pm = get_prompt_manager()
        self.source_pool = SourcePool()                       # populated per-lecture
        self.textbook_index: Optional[TextbookIndex] = None   # set by the caller if a textbook was uploaded
        self.include_web = True                               # honor the web-sources toggle

    async def generate(self, week_number: int, topic: str, course_context: CourseContext,
                      format_type: LectureFormat, custom_prompt: Optional[str] = None) -> Tuple[GeneratedContent, dict]:
        """Generate lecture content with course context."""

        try:
            logger.debug(f"Starting lecture generation: Week {week_number}, Topic: {topic}")

            # Topic-level grounding: textbook chapter(s) for THIS lecture + academic/current.
            self.source_pool = await self._build_source_pool(topic, course_context)
            current_content = self.source_pool.render_for_prompt()

            components = await self._generate_lecture_components(
                week_number, topic, course_context, current_content, format_type
            )

            final_content = self._assemble_lecture(components, format_type)

            # Citation enforcement: strip fabricated [n], append references.
            final_content, citation_report = resolve_citations(final_content, self.source_pool)
            bibliography = self.source_pool.bibliography_md()
            if bibliography:
                final_content = f"{final_content}\n\n{bibliography}"

            qa_review = await self.qa_agent.review_content(final_content, "lecture_notes", course_context)
            logger.debug(f"Lecture QA score: {qa_review['overall_score']}/100")

            slo_codes = [s.get("code", "") for s in get_all_course_slos(course_context)]
            qa_review["grounding"] = {
                "strength": self.source_pool.strength.value,
                "sources": self.source_pool.sources_for_ui(),
                **citation_report,
                **slo_coverage(final_content, slo_codes),
            }

            generated_content = GeneratedContent(
                content=final_content,
                rationale=self._build_lecture_rationale(format_type, week_number, course_context, qa_review),
                quality_score=qa_review["overall_score"],
                suggestions=qa_review["recommendations"],
                version=1,
                timestamp=datetime.now()
            )

            return generated_content, qa_review

        except Exception as e:
            logger.error(f"Lecture generation failed: {e}")
            raise Exception(f"Lecture generation failed: {e}")

    # _build_source_pool() and _grounding_messages() are provided by _TopicGroundingMixin.
    
    async def _generate_lecture_components(self, week_number: int, topic: str, 
                                         course_context: CourseContext, current_content: str,
                                         format_type: LectureFormat) -> Dict[str, str]:
        """Generate lecture components."""
        
        components = {}
        complexity_instructions = self._get_complexity_instructions(course_context.program_type)
        all_slos = get_all_course_slos(course_context)
        
        components["objectives"] = await self._generate_learning_objectives(topic, course_context, all_slos, complexity_instructions)
        components["introduction"] = await self._generate_lecture_introduction(topic, course_context, current_content, complexity_instructions)
        components["main_content"] = await self._generate_main_content(topic, course_context, current_content, all_slos, complexity_instructions)
        components["activities"] = await self._generate_activities(topic, course_context, all_slos, complexity_instructions)
        components["assessment"] = await self._generate_assessment_activities(topic, course_context, complexity_instructions)
        
        return components
    
    def _get_complexity_instructions(self, program_type: str) -> str:
        """Get complexity instructions for lectures."""
        if program_type == ProgramType.UNDERGRADUATE.value:
            return """
            LECTURE COMPLEXITY: UNDERGRADUATE
            - Explain concepts clearly with examples
            - Use guided practice and step-by-step learning
            - Include interactive elements for engagement
            - Focus on understanding and basic application
            """
        elif program_type == ProgramType.KELLEY_DIRECT.value:
            return """
            LECTURE COMPLEXITY: GRADUATE (KELLEY DIRECT)
            - Advance to strategic and analytical thinking
            - Include professional case studies and scenarios
            - Expect independent analysis and synthesis
            - Focus on practical professional application
            """
        else:  # MBA
            return """
            LECTURE COMPLEXITY: MBA (HIGHEST)
            - Require sophisticated analysis and leadership thinking
            - Include complex executive-level case studies
            - Expect original insights and strategic recommendations
            - Focus on executive decision-making and thought leadership
            """
    
    async def _generate_learning_objectives(self, topic: str, course_context: CourseContext, 
                                          all_slos: List[Dict], complexity_instructions: str) -> str:
        """Generate learning objectives with complexity."""
        
        slo_context = format_slos_for_prompt(course_context.selected_slos, course_context.custom_slos)
        
        # MODIFIED: Use PromptManager
        prompt = self.pm.get_prompt(
            'lecture',
            'objectives',
            course_name=course_context.course_name,
            topic=topic,
            complexity_instructions=complexity_instructions,
            teaching_style=course_context.teaching_style,
            slo_context=slo_context
        )
        
        messages = self._grounding_messages(topic) + [
            SystemMessage(content=f"Create objectives for {course_context.course_name} lecture on {topic}."),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return response.content
    
    async def _generate_lecture_introduction(self, topic: str, course_context: CourseContext, 
                                           current_content: str, complexity_instructions: str) -> str:
        """Generate lecture introduction."""
        
        # MODIFIED: Use PromptManager
        prompt = self.pm.get_prompt(
            'lecture',
            'introduction',
            course_name=course_context.course_name,
            topic=topic,
            complexity_instructions=complexity_instructions,
            program_type=course_context.program_type,
            current_content=current_content
        )
        
        messages = self._grounding_messages(topic) + [
            SystemMessage(content=f"Introduce {topic} for {course_context.course_name}, grounded only in the provided sources; never fabricate statistics or studies."),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return response.content
    
    async def _generate_main_content(self, topic: str, course_context: CourseContext, 
                                   current_content: str, all_slos: List[Dict], complexity_instructions: str) -> str:
        """Generate main content with complexity."""
        
        relevant_slo_codes = [slo["code"] for slo in all_slos[:3]]
        
        # MODIFIED: Use PromptManager
        prompt = self.pm.get_prompt(
            'lecture',
            'main_content',
            course_name=course_context.course_name,
            topic=topic,
            complexity_instructions=complexity_instructions,
            duration_per_session=course_context.duration_per_session,
            teaching_style=course_context.teaching_style,
            program_type=course_context.program_type,
            current_content=current_content,
            relevant_slo_codes=', '.join(relevant_slo_codes)
        )
        
        messages = self._grounding_messages(topic) + [
            SystemMessage(content=f"You are a master educator teaching {topic} in {course_context.course_name}. You MUST include a complete step-by-step worked example and a faded example. Use sourced-and-cited [n] figures or clearly-hypothetical numbers — never fabricated real-world data."),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return response.content
    
    async def _generate_activities(self, topic: str, course_context: CourseContext, 
                                 all_slos: List[Dict], complexity_instructions: str) -> str:
        """Generate activities with complexity."""
        
        # MODIFIED: Use PromptManager
        prompt = self.pm.get_prompt(
            'lecture',
            'activities',
            course_name=course_context.course_name,
            topic=topic,
            complexity_instructions=complexity_instructions,
            teaching_style=course_context.teaching_style
        )
        
        messages = self._grounding_messages(topic) + [
            SystemMessage(content=f"Design activities for {course_context.course_name} on {topic}."),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return response.content
    
    async def _generate_assessment_activities(self, topic: str, course_context: CourseContext, 
                                            complexity_instructions: str) -> str:
        """Generate assessment activities."""
        
        # MODIFIED: Use PromptManager
        prompt = self.pm.get_prompt(
            'lecture',
            'assessment',
            course_name=course_context.course_name,
            topic=topic,
            complexity_instructions=complexity_instructions,
            assessment_preferences=', '.join(course_context.assessment_preferences)
        )
        
        messages = self._grounding_messages(topic) + [
            SystemMessage(content=f"Create assessments for {course_context.course_name} on {topic}."),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return response.content
    
    def _assemble_lecture(self, components: Dict[str, str], format_type: LectureFormat) -> str:
        """Assemble lecture components."""
        
        if format_type == LectureFormat.AI_SCRIPT:
            return self._assemble_ai_script(components)
        else:
            return self._assemble_lecture_notes(components)
    
    def _assemble_lecture_notes(self, components: Dict[str, str]) -> str:
        """Assemble traditional lecture notes."""
        
        return f"""
# Lecture Notes

## Learning Objectives
{components["objectives"]}

## Introduction (10-15 minutes)
{components["introduction"]}

## Main Content (45-50 minutes)
{components["main_content"]}

## Interactive Activities (15-20 minutes)
{components["activities"]}

## Assessment & Wrap-up (10 minutes)
{components["assessment"]}

---
*Total Duration: 75-90 minutes*
"""
    
    def _assemble_ai_script(self, components: Dict[str, str]) -> str:
        """Assemble AI teaching script."""
        
        return f"""
# AI Teaching Script

## Session Setup
**Learning Objectives:**
{components["objectives"]}

## Phase 1: Introduction (10-15 minutes)
**AI Instructions:** Begin session with engaging introduction
{components["introduction"]}

## Phase 2: Content Delivery (45-50 minutes)
**AI Instructions:** Present main content with interactive elements
{components["main_content"]}

## Phase 3: Interactive Learning (15-20 minutes)
**AI Instructions:** Facilitate activities and discussions
{components["activities"]}

## Phase 4: Assessment & Closure (10 minutes)
**AI Instructions:** Conduct assessment and wrap up session
{components["assessment"]}

---
*AI Script Duration: 75-90 minutes*
"""
    
    def _build_lecture_rationale(self, format_type: LectureFormat, week_number: int, 
                               course_context: CourseContext, qa_review: dict) -> str:
        """Build lecture rationale."""
        content_type = format_type.value.replace("Generate as ", "")
        all_slo_count = len(course_context.selected_slos) + len(course_context.custom_slos)
        g = qa_review.get("grounding", {})
        grounding_line = ""
        if g:
            grounding_line = (
                f"Grounding: {g.get('strength', 'n/a')}; "
                f"{g.get('citation_count', 0)} citations from {g.get('sources_available', 0)} sources; "
                f"{len(g.get('orphans_removed', []))} unsourced claims removed."
            )

        return f"""
        {content_type} for {course_context.course_name} Week {week_number} at {course_context.program_type} complexity level.
        Teaching methodology: {course_context.teaching_style}
        Integrated {all_slo_count} SLOs with pedagogical connections.
        {grounding_line}
        Duration: {course_context.duration_per_session} minutes with clear progression.

        Quality Score: {qa_review["overall_score"]}/100
        """


class AssignmentGenerator(_TopicGroundingMixin):
    """Assignment generator with complexity hierarchy."""

    def __init__(self, api_key: str, serper_api_key: str, model_type: str = "gpt-4-turbo"):
        self.llm = ChatOpenAI(api_key=api_key, model=model_type, temperature=0.7)
        self.qa_agent = QualityAssuranceAgent(api_key, model_type)
        self.search_service = SerperSearchService(serper_api_key)
        self.pm = get_prompt_manager()
        self.source_pool = SourcePool()
        self.textbook_index: Optional[TextbookIndex] = None
        self.include_web = True
    
    async def generate(self, week_number: int, topic: str, course_context: CourseContext,
                      custom_prompt: Optional[str] = None) -> Tuple[GeneratedContent, dict]:
        """Generate assignment with complexity level."""
        
        try:
            logger.debug(f"Starting assignment generation: Week {week_number}, Topic: {topic}")

            self.source_pool = await self._build_source_pool(topic, course_context)
            current_examples = self.source_pool.render_for_prompt()

            components = await self._generate_assignment_components(
                week_number, topic, course_context, current_examples
            )

            final_content = self._assemble_assignment(components)

            # Citation enforcement: strip fabricated [n], append references.
            final_content, citation_report = resolve_citations(final_content, self.source_pool)
            bibliography = self.source_pool.bibliography_md()
            if bibliography:
                final_content = f"{final_content}\n\n{bibliography}"

            qa_review = await self.qa_agent.review_content(final_content, "assignment", course_context)
            logger.debug(f"Assignment QA score: {qa_review['overall_score']}/100")

            slo_codes = [s.get("code", "") for s in get_all_course_slos(course_context)]
            qa_review["grounding"] = {
                "strength": self.source_pool.strength.value,
                "sources": self.source_pool.sources_for_ui(),
                **citation_report,
                **slo_coverage(final_content, slo_codes),
            }

            generated_content = GeneratedContent(
                content=final_content,
                rationale=self._build_assignment_rationale(course_context, qa_review),
                quality_score=qa_review["overall_score"],
                suggestions=qa_review["recommendations"],
                version=1,
                timestamp=datetime.now()
            )
            
            return generated_content, qa_review
            
        except Exception as e:
            logger.error(f"Assignment generation failed: {e}")
            raise Exception(f"Assignment generation failed: {e}")
    
    def _get_complexity_instructions(self, program_type: str) -> str:
        """Get complexity instructions for assignments."""
        if program_type == ProgramType.UNDERGRADUATE.value:
            return """
            ASSIGNMENT COMPLEXITY: UNDERGRADUATE
            - Focus on understanding and application of concepts
            - Provide clear guidelines and structured tasks
            - Include guided analysis with specific questions
            - Assess comprehension and basic critical thinking
            """
        elif program_type == ProgramType.KELLEY_DIRECT.value:
            return """
            ASSIGNMENT COMPLEXITY: GRADUATE (KELLEY DIRECT)
            - Require strategic analysis and professional application
            - Include real-world business scenarios and cases
            - Expect independent research and synthesis
            - Assess strategic thinking and professional judgment
            """
        else:  # MBA
            return """
            ASSIGNMENT COMPLEXITY: MBA (HIGHEST)
            - Require sophisticated analysis and executive-level thinking
            - Include complex multi-faceted business challenges
            - Expect original insights and innovative solutions
            - Assess leadership competencies and strategic vision
            """
    
    async def _generate_assignment_components(self, week_number: int, topic: str,
                                            course_context: CourseContext, current_examples: str) -> Dict[str, str]:
        """Generate assignment components with complexity."""
        
        components = {}
        complexity_instructions = self._get_complexity_instructions(course_context.program_type)
        all_slos = get_all_course_slos(course_context)
        
        components["overview"] = await self._generate_assignment_overview(topic, course_context, all_slos, complexity_instructions)
        components["instructions"] = await self._generate_detailed_instructions(topic, course_context, current_examples, all_slos, complexity_instructions)
        components["requirements"] = await self._generate_requirements(topic, course_context, complexity_instructions)
        components["grading"] = await self._generate_grading_criteria(topic, course_context, all_slos, complexity_instructions)
        components["resources"] = await self._generate_resources(topic, course_context, current_examples)
        
        return components
    
    async def _generate_assignment_overview(self, topic: str, course_context: CourseContext, 
                                          all_slos: List[Dict], complexity_instructions: str) -> str:
        """Generate assignment overview with complexity."""
        
        slo_context = format_slos_for_prompt(course_context.selected_slos, course_context.custom_slos)
        
        # MODIFIED: Use PromptManager - using assignment_content prompt for main generation
        prompt = self.pm.get_prompt(
            'assignment',
            'assignment_content',
            course_name=course_context.course_name,
            complexity_instructions=complexity_instructions,
            week=0,  # Overview doesn't have specific week
            topic=topic,
            assignment_type="Overview",
            weeks_to_complete=1,
            slo_context=slo_context,
            teaching_style=course_context.teaching_style,
            context_suffix=""
        )
        
        messages = self._grounding_messages(topic) + [
            SystemMessage(content=f"Create assignment for {course_context.course_name} on {topic} with SLO integration; frame company scenarios as student research tasks, never fabricate figures."),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return response.content
    
    async def _generate_detailed_instructions(self, topic: str, course_context: CourseContext, 
                                            current_examples: str, all_slos: List[Dict], complexity_instructions: str) -> str:
        """Generate detailed instructions with complexity."""
        
        prompt = f"""
        Create detailed instructions for {course_context.course_name} assignment: {topic}
        
        {complexity_instructions}
        
        Course: {course_context.course_name}
        Teaching Style: {course_context.teaching_style}
        Program: {course_context.program_type}
        Current Examples: {current_examples}
        """
        
        messages = self._grounding_messages(topic) + [
            SystemMessage(content=f"Write detailed step-by-step assignment instructions for {course_context.course_name} on {topic}; cite real figures [n] from sources or use clearly-hypothetical numbers."),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return response.content
    
    async def _generate_requirements(self, topic: str, course_context: CourseContext, complexity_instructions: str) -> str:
        """Generate requirements with complexity."""
        
        prompt = f"""
        Create requirements for {course_context.course_name} assignment: {topic}
        
        {complexity_instructions}
        
        Assessment Methods: {', '.join(course_context.assessment_preferences)}
        Program: {course_context.program_type}
        """
        
        messages = self._grounding_messages(topic) + [
            SystemMessage(content=f"Set requirements for {course_context.course_name} assignment."),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return response.content
    
    async def _generate_grading_criteria(self, topic: str, course_context: CourseContext, 
                                       all_slos: List[Dict], complexity_instructions: str) -> str:
        """Generate grading criteria with SLO assessment."""
        
        prompt = f"""
        Create grading criteria for {course_context.course_name} assignment: {topic}
        
        {complexity_instructions}
        
        Course: {course_context.course_name}
        Teaching Style: {course_context.teaching_style}
        """
        
        messages = self._grounding_messages(topic) + [
            SystemMessage(content=f"Create grading criteria for {course_context.course_name} assignment."),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return response.content
    
    async def _generate_resources(self, topic: str, course_context: CourseContext, current_examples: str) -> str:
        """Generate resources for assignment."""
        
        prompt = f"""
        Create resources for {course_context.course_name} assignment: {topic}
        
        Course: {course_context.course_name}
        Topic: {topic}
        Current Examples: {current_examples}
        """
        
        messages = self._grounding_messages(topic) + [
            SystemMessage(content=f"Recommend resources for {course_context.course_name} assignment; do not invent citations — use the provided sources [n]."),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return response.content
    
    def _assemble_assignment(self, components: Dict[str, str]) -> str:
        """Assemble assignment components."""
        
        return f"""
# Assignment Instructions

## Overview
{components["overview"]}

## Detailed Instructions
{components["instructions"]}

## Requirements
{components["requirements"]}

## Grading Criteria
{components["grading"]}

## Resources and Support
{components["resources"]}

---
*Please review all sections carefully before beginning your work.*
"""
    
    def _build_assignment_rationale(self, course_context: CourseContext, qa_review: dict) -> str:
        """Build assignment rationale."""
        all_slo_count = len(course_context.selected_slos) + len(course_context.custom_slos)
        g = qa_review.get("grounding", {})
        grounding_line = ""
        if g:
            grounding_line = (
                f"Grounding: {g.get('strength', 'n/a')}; "
                f"{g.get('citation_count', 0)} citations from {g.get('sources_available', 0)} sources; "
                f"{len(g.get('orphans_removed', []))} unsourced claims removed."
            )
        return f"""
        Assignment for {course_context.course_name} at {course_context.program_type} complexity level.
        Teaching methodology: {course_context.teaching_style}
        Assessment alignment: {', '.join(course_context.assessment_preferences)}
        Integrated {all_slo_count} SLOs with Learning Objective connections.
        {grounding_line}

        Quality Score: {qa_review["overall_score"]}/100
        """


class GradingRubricGenerator:
    """Grading rubric generator with SLO assessment and complexity hierarchy."""
    
    def __init__(self, api_key: str, model_type: str = "gpt-4-turbo"):
        self.llm = ChatOpenAI(api_key=api_key, model=model_type, temperature=0.5)
        self.qa_agent = QualityAssuranceAgent(api_key, model_type)
        self.pm = get_prompt_manager()
    
    async def generate(self, assignment_content: str, course_context: CourseContext,
                      custom_prompt: Optional[str] = None) -> Tuple[GeneratedContent, dict]:
        """Generate grading rubric with complexity level."""
        
        try:
            logger.debug("Starting rubric generation")
            
            key_criteria = await self._analyze_assignment_criteria(assignment_content, course_context)
            
            components = await self._generate_rubric_components(key_criteria, course_context)
            
            final_content = self._assemble_rubric(components)
            
            qa_review = await self.qa_agent.review_content(final_content, "grading_rubric", course_context)
            logger.debug(f"Rubric QA score: {qa_review['overall_score']}/100")
            
            generated_content = GeneratedContent(
                content=final_content,
                rationale=self._build_rubric_rationale(course_context, qa_review),
                quality_score=qa_review["overall_score"],
                suggestions=qa_review["recommendations"],
                version=1,
                timestamp=datetime.now()
            )
            
            return generated_content, qa_review
            
        except Exception as e:
            logger.error(f"Rubric generation failed: {e}")
            raise Exception(f"Rubric generation failed: {e}")
    
    def _get_complexity_instructions(self, program_type: str) -> str:
        """Get complexity instructions for rubrics."""
        if program_type == ProgramType.UNDERGRADUATE.value:
            return """
            RUBRIC COMPLEXITY: UNDERGRADUATE
            - Focus on fundamental understanding and application
            - Clear performance levels with specific examples
            - Emphasize learning progress and improvement
            - Assess basic analysis and communication skills
            """
        elif program_type == ProgramType.KELLEY_DIRECT.value:
            return """
            RUBRIC COMPLEXITY: GRADUATE (KELLEY DIRECT)
            - Emphasize strategic thinking and professional application
            - Include business scenario evaluation criteria
            - Assess independent analysis and synthesis
            - Focus on professional competency development
            """
        else:  # MBA
            return """
            RUBRIC COMPLEXITY: MBA (HIGHEST)
            - Require sophisticated analysis and leadership assessment
            - Include executive-level decision-making criteria
            - Assess innovation, strategic vision, and thought leadership
            - Focus on transformational impact and influence
            """
    
    async def _analyze_assignment_criteria(self, assignment_content: str, course_context: CourseContext) -> List[str]:
        """Analyze assignment for grading criteria."""
        
        slo_context = format_slos_for_prompt(course_context.selected_slos, course_context.custom_slos)
        complexity_instructions = self._get_complexity_instructions(course_context.program_type)
        
        prompt = f"""
        Analyze this {course_context.course_name} assignment and identify 4-6 key grading criteria:
        
        {complexity_instructions}
        
        Assignment Content: {assignment_content[:1500]}...
        
        Available SLOs: {slo_context}
        
        Return numbered list of criteria for evaluation.
        """
        
        messages = [
            SystemMessage(content=f"Analyze assignment for {course_context.course_name}."),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        
        criteria_lines = [line.strip() for line in response.content.split('\n') 
                         if line.strip() and any(char.isdigit() for char in line)]
        return criteria_lines[:6]
    
    async def _generate_rubric_components(self, criteria: List[str], course_context: CourseContext) -> Dict[str, str]:
        """Generate rubric components with complexity."""
        
        components = {}
        complexity_instructions = self._get_complexity_instructions(course_context.program_type)
        
        components["header"] = await self._generate_rubric_header(course_context, complexity_instructions)
        
        for i, criterion in enumerate(criteria, 1):
            components[f"criterion_{i}"] = await self._generate_detailed_criterion(criterion, course_context, complexity_instructions)
        
        components["scoring_guide"] = await self._generate_scoring_guide(course_context, complexity_instructions)
        
        return components
    
    async def _generate_rubric_header(self, course_context: CourseContext, complexity_instructions: str) -> str:
        """Generate rubric header with complexity level."""
        
        prompt = f"""
        Create professional rubric header for {course_context.course_name} assignment.
        
        {complexity_instructions}
        
        Course: {course_context.course_name}
        Teaching Style: {course_context.teaching_style}
        """
        
        messages = [
            SystemMessage(content=f"Create rubric header for {course_context.course_name}."),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return response.content
    
    async def _generate_detailed_criterion(self, criterion: str, course_context: CourseContext, complexity_instructions: str) -> str:
        """Generate detailed criterion with SLO assessment."""
        
        # MODIFIED: Use PromptManager
        prompt = self.pm.get_prompt(
            'rubric',
            'rubric_main',
            course_name=course_context.course_name,
            week=0,
            topic=criterion,
            assignment_type="General",
            grading_scale="100-point",
            total_points=100,
            feedback_style="Constructive",
            include_examples="true",
            include_self_assessment="true",
            program_type=course_context.program_type,
            context_suffix=""
        )
        
        messages = [
            SystemMessage(content=f"Create observable, measurable rubric criteria for {course_context.course_name}."),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return response.content
    
    async def _generate_scoring_guide(self, course_context: CourseContext, complexity_instructions: str) -> str:
        """Generate scoring guide with SLO assessment guidance."""
        
        prompt = f"""
        Create scoring guide for {course_context.course_name} assignment rubric.
        
        {complexity_instructions}
        
        Course: {course_context.course_name}
        Teaching Style: {course_context.teaching_style}
        """
        
        messages = [
            SystemMessage(content=f"Create scoring guidance for {course_context.course_name} rubric."),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return response.content
    
    def _assemble_rubric(self, components: Dict[str, str]) -> str:
        """Assemble rubric components."""
        
        rubric_content = f"{components['header']}\n\n"
        
        for key, value in components.items():
            if key.startswith("criterion_"):
                rubric_content += f"{value}\n\n"
        
        rubric_content += f"{components['scoring_guide']}\n"
        
        return rubric_content.strip()
    
    def _build_rubric_rationale(self, course_context: CourseContext, qa_review: dict) -> str:
        """Build rubric rationale."""
        all_slo_count = len(course_context.selected_slos) + len(course_context.custom_slos)
        return f"""
        Rubric for {course_context.course_name} at {course_context.program_type} complexity level.
        Teaching philosophy: {course_context.teaching_style}
        Integrated {all_slo_count} SLOs with assessment indicators.
        
        Quality Score: {qa_review["overall_score"]}/100
        """