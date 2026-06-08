"""
Main Streamlit Application - Updated with single suggestion system and 3 max versions
"""
from typing import List, Dict, Any, Optional
import streamlit as st
import logging
import json
import asyncio
from datetime import datetime
from dataclasses import asdict
from qa_agent import QualityAssuranceAgent
import streamlit as st

# Logging setup
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('course_builder.log')
    ]
)
logger = logging.getLogger(__name__)

# Bump this whenever deploying so Render logs prove which build is live.
APP_BUILD = "2026-06-08-relevance-fix-4"
logger.info(f"=== ACB module import — build {APP_BUILD} ===")

from config import (
    CourseContext, CustomSLO, TeachingStyle, AssessmentStyle, 
    LectureFormat, ProgramType, ModelType, AIClassroomUse, 
    SuggestionGranularity,
    get_program_slos, get_ai_policy_text, 
    DEFAULT_ASSESSMENTS, auto_assign_bloom_levels
)

from utils import extract_syllabus_topics, get_missing_dependencies
from serper_service import SerperSearchService
from generators import SyllabusGenerator, LectureNotesGenerator, AssignmentGenerator, GradingRubricGenerator
from content_manager import ContentManager
from ui_components import (
    render_quality_review, render_live_editor, render_export_buttons,
    render_progress_tracker, render_dependency_warning, render_api_configuration,
    render_file_upload_section, validate_and_show_errors, render_generation_button,
    render_grounding_panel, render_candidate_sources
)
from prompt_ui import render_prompt_editor, render_prompt_version_manager
from prompt_manager import get_prompt_manager

def run_async(coro):
    """Run an async coroutine from Streamlit's (sync) script thread.

    Runs the coroutine in a dedicated worker thread with its own fresh event
    loop. This avoids nest_asyncio, which breaks sniffio/anyio detection on
    newer httpx/openai versions ("unknown async library, or not in async
    context") and was failing both generation and source search.
    """
    import threading

    box = {}

    def _runner():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            box["value"] = loop.run_until_complete(coro)
        except BaseException as e:  # propagate to caller thread
            box["error"] = e
        finally:
            try:
                loop.close()
            finally:
                asyncio.set_event_loop(None)

    t = threading.Thread(target=_runner, daemon=True)
    t.start()
    t.join()

    if "error" in box:
        raise box["error"]
    return box.get("value")

def init_session_state():
    """Initialize session state variables."""
    logger.info("Initializing session state")
    defaults = {
        'course_context': None,
        'content_manager': ContentManager(),
        'generated_content': {},
        'custom_slos': [],
        'api_key': "",
        'serper_api_key': "",
        'model_type': ModelType.GPT_4_TURBO.value,
        'show_rationale': True,
        'uploaded_context': "",
        'uploaded_raw_text': "",
        'textbook_index': None,
        'textbook_index_hash': None,
        'candidate_sources': [],
        'selected_sources': [],
        'generation_errors': {},
        'ai_classroom_use': AIClassroomUse.CONDITIONAL.value,
        'syllabus_topics': [],
        'actionable_suggestions': "",
        'suggestion_granularity': SuggestionGranularity.MEDIUM_LEVEL.value,
        'edited_suggestions': "",
        'regeneration_count': 0,
        'suggestion_history': [],
        'base_custom_instructions': "",
        'current_custom_instructions': "",  # Track current instructions separately
        'applied_suggestions_cumulative': "",
        'uploaded_file_description': "",  # Track file description separately
        'syllabus_versions': [],
        # Prompt management (PromptManager is a module-level singleton whose
        # __init__ only runs once, so these MUST be initialized per session here
        # or a fresh session raises "st.session_state has no attribute custom_prompts").
        'custom_prompts': {},
        'prompt_versions': [],
        'active_prompt_version': None,
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
            logger.debug(f"Set session state {key}")

    logger.info(
        f"init_session_state done (build {APP_BUILD}) — "
        f"custom_prompts present: {'custom_prompts' in st.session_state}"
    )

def render_header():
    """Render application header."""
    st.title("🎓 Autonomous Course Builder")


def render_sidebar():
    """Render sidebar with configuration and progress tracking."""
    with st.sidebar:
        # API Configuration
        api_key, serper_api_key, model_type = render_api_configuration()
        
        # Update session state
        st.session_state.api_key = api_key
        st.session_state.serper_api_key = serper_api_key
        st.session_state.model_type = model_type
        
        st.markdown("---")
        
        # Progress Tracker
        render_progress_tracker(st.session_state.generated_content)
        render_prompt_version_manager()

        # Show generation errors if any
        if st.session_state.generation_errors:
            with st.expander("⚠️ **Generation Issues**", expanded=False):
                for content_type, error in st.session_state.generation_errors.items():
                    st.error(f"**{content_type}**: {error}")
        
        # Reset functionality
        if st.button("🔄 Reset All", help="Clear all data and start fresh"):
            logger.info("Resetting all session data")
            for key in list(st.session_state.keys()):
                if key not in ['api_key', 'serper_api_key', 'model_type']:
                    del st.session_state[key]
            init_session_state()
            st.rerun()

def render_syllabus_tab():
    """Render syllabus generation tab."""
    render_prompt_editor('syllabus', 'Syllabus')
    logger.debug("Rendering syllabus tab")
    st.header("📄 Generate Syllabus")
    st.markdown("*Start by setting up your course information and learning outcomes*")
    
    # Course Information Section
    st.subheader("**Course Information** (Required)")
    col1, col2 = st.columns(2)
    
    with col1:
        course_code = st.text_input("Course Code *", value="BUS-X 100")
        course_name = st.text_input("Course Name *", value="Introduction to Business")
        program_type = st.selectbox("Program Type *", options=[pt.value for pt in ProgramType], index=0)
        sessions_per_week = st.number_input("Sessions per Week *", min_value=1, max_value=7, value=2)

    with col2:
        semester = st.text_input("Semester *", value="Spring 2026")
        weeks = st.selectbox("Course Duration *", options=[7, 12, 16], index=2)
        duration_per_session = st.number_input("Duration per Session (minutes) *", min_value=30, max_value=240, value=75, step=15)
    
    # Professor Information Section
    st.subheader("**Professor Information** (Required)")
    col1, col2 = st.columns(2)
    
    with col1:
        professor_name = st.text_input("Professor Name *", value="Prof. Rowan Brightling")
        professor_email = st.text_input("Email *", value="rbrightling@iu.edu")
    
    with col2:
        office_location = st.text_input("Office Location *", value="Hodge Hall")
        office_hours = st.text_input("Office Hours *", value="Tuesdays 2 PM-4 PM, Thursdays 10 AM-12 PM")
    
    # AI Classroom Use Policy Section
    st.subheader("**AI Classroom Use Policy** (Required)")
    ai_classroom_use = st.selectbox(
        "AI Classroom Use *", 
        options=[ai.value for ai in AIClassroomUse],
        index=1,
        help="Select the AI policy for your classroom"
    )
    
    # Show preview of selected policy
    if ai_classroom_use:
        policy_text = get_ai_policy_text(ai_classroom_use)
        if policy_text:
            with st.container():
                st.markdown(f"**📋 Preview: {ai_classroom_use} Policy**")
                with st.expander("View Policy Details", expanded=False):
                    preview_text = policy_text[:500] + "..." if len(policy_text) > 500 else policy_text
                    st.markdown(f"<div style='font-size: 0.85em;'>{preview_text}</div>", unsafe_allow_html=True)
                    
    # Learning Outcomes Section
    st.markdown("---")
    st.subheader("📋 Student Learning Outcomes")
    
    # Standard SLOs selection
    st.markdown("**Select Program-Specific SLOs** (Required)")
    st.markdown(f"*All {program_type} SLOs (selection required):*")
    
    # Get program-specific SLOs
    program_slos = get_program_slos(program_type) if program_type else get_program_slos(ProgramType.UNDERGRADUATE.value)
    logger.debug(f"Available SLOs: {len(program_slos)} for {program_type}")
    
    selected_slos = []
    for slo in program_slos:
        if st.checkbox(f"**{slo['code']}**: {slo['description']}", key=f"slo_{slo['code']}"):
            selected_slos.append(slo)
    
    logger.debug(f"Selected SLOs: {len(selected_slos)}")
    
    # Custom SLOs addition
    st.markdown("---")
    st.subheader("➕ **Add Custom SLOs**")
    
    col1, col2 = st.columns(2)
    with col1:
        custom_code = st.text_input("Custom SLO Code", placeholder="e.g., KD-3.2")
    with col2:
        custom_description = st.text_area("Custom SLO Description", placeholder="Students will be able to...")

    if st.button("➕ Add Custom SLO") and custom_code and custom_description:
        new_slo = CustomSLO(custom_code, custom_description)
        st.session_state.custom_slos.append(new_slo)
        logger.info(f"Added custom SLO: {custom_code}")
        st.success(f"✅ Added: {custom_code}")
        st.rerun()
            
    # Display custom SLOs
    if st.session_state.custom_slos:
        st.markdown("**Added Custom SLOs:**")
        for i, slo in enumerate(st.session_state.custom_slos):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"• **{slo.title}**: {slo.content}")
            with col2:
                if st.button("🗑️", key=f"del_slo_{i}", help="Delete this SLO"):
                    st.session_state.custom_slos.pop(i)
                    logger.info(f"Deleted custom SLO: {slo.title}")
                    st.rerun()

    # Pedagogical Preferences Section
    st.markdown("---")
    st.subheader("🎯 Pedagogical Preferences")
    
    col1, col2 = st.columns(2)
    
    with col1:
        teaching_style = st.selectbox("Teaching Style *", options=[ts.value for ts in TeachingStyle])
    
    with col2:
        assessment_prefs = st.multiselect(
            "Assessment Preferences *", 
            options=[am.value for am in AssessmentStyle], 
            default=DEFAULT_ASSESSMENTS
        )

    # AI Suggestion Granularity Section
    st.markdown("---")
    st.subheader("🔍 AI Suggestion Settings")
    
    from config import SuggestionGranularity
    suggestion_granularity = st.selectbox(
        "Suggestion Granularity *",
        options=[sg.value for sg in SuggestionGranularity],
        index=1,  # Default to Medium-level
        help="Control the level of detail for AI-generated improvement suggestions"
    )
    st.session_state.suggestion_granularity = suggestion_granularity

    # File Upload and Custom Instructions
    st.markdown("---")
    st.subheader("📁 Additional Customization")
    
    custom_instructions = st.text_area(
        "Custom Instructions (Optional):",
        placeholder="e.g., Include specific university policies, emphasize group work, etc.",
        height=100,
        key="custom_instructions_input"
    )
    
    # File upload section
    file_description, uploaded_context = render_file_upload_section()
    st.session_state.uploaded_context = uploaded_context
    st.session_state.uploaded_file_description = file_description

    # ---- Course Materials & Sources: textbook indexing + source preview/curation ----
    st.markdown("---")
    st.subheader("📚 Course Materials & Sources")

    # Build/cache a textbook index from any uploaded material so we can show feedback now.
    raw_text = st.session_state.get("uploaded_raw_text", "") or ""
    if raw_text.strip():
        content_hash = hash(raw_text)
        if st.session_state.get("textbook_index_hash") != content_hash:
            from grounding.textbook import build_textbook_index
            st.session_state.textbook_index = build_textbook_index(raw_text)
            st.session_state.textbook_index_hash = content_hash
        tb = st.session_state.get("textbook_index")
        if tb and tb.available:
            st.success(f"📘 Textbook indexed: {len(tb.chunks)} sections · {len(tb.toc)} chapters detected")
        else:
            st.warning("📘 Couldn't index this file for retrieval (it may be scanned/image-only); it will still be used as context.")
    else:
        st.session_state.textbook_index = None
        st.session_state.textbook_index_hash = None

    has_textbook = bool(st.session_state.get("textbook_index"))

    include_web = st.checkbox(
        "🌐 Include current/industry web sources (uses Serper)",
        value=st.session_state.get("include_web_sources", True),
        key="include_web_sources",
        help="Academic sources (OpenAlex, arXiv) are always free; web search has a small per-call cost.",
    )

    if st.button("🔎 Find / preview sources", help="Search sources for this course so you can curate them before generating"):
        if not course_name.strip():
            st.warning("Enter a Course Name first.")
        else:
            from grounding import fetch_candidate_sources
            with st.spinner("Finding sources..."):
                cands = run_async(fetch_candidate_sources(
                    course_name, include_web, st.session_state.get("serper_api_key", "")
                ))
            st.session_state.candidate_sources = cands or []
            # reset checkbox selections so the new set defaults to all-selected
            for k in [k for k in list(st.session_state.keys()) if k.startswith("src_sel_")]:
                del st.session_state[k]
            st.success(f"Found {len(st.session_state.candidate_sources)} source(s). Curate below.")

    candidate_sources = st.session_state.get("candidate_sources", []) or []
    st.session_state.selected_sources = render_candidate_sources(candidate_sources, has_textbook)

    # Validation and Generation
    st.markdown("---")
    
    # Auto-assign Bloom levels
    bloom_levels = auto_assign_bloom_levels(teaching_style) if teaching_style else []
    
    required_fields = {
        "course_code": course_code,
        "course_name": course_name,
        "program_type": program_type,
        "semester": semester,
        "professor_name": professor_name,
        "professor_email": professor_email,
        "office_location": office_location,
        "office_hours": office_hours,
        "teaching_style": teaching_style,
        "assessment_preferences": assessment_prefs,
        "selected_slos": selected_slos or st.session_state.custom_slos,
        "ai_classroom_use": ai_classroom_use,
        "api_key": st.session_state.api_key,
        "serper_api_key": st.session_state.serper_api_key
    }
    
    # Additional validations
    additional_validations = []
    if uploaded_context and not file_description.strip():
        additional_validations.append((False, "File description required when file is uploaded"))
    
    is_valid = validate_and_show_errors(required_fields, "Syllabus Setup", additional_validations)
    
    def generate_syllabus():
        """Generate syllabus with enhanced error handling and actionable suggestions."""
        logger.info("Starting syllabus generation")
        
        try:
            # Create course context
            course_context = CourseContext(
                course_code=course_code,
                course_name=course_name,
                program_type=program_type,
                semester=semester,
                weeks=weeks,
                professor_name=professor_name,
                professor_email=professor_email,
                office_location=office_location,
                office_hours=office_hours,
                selected_slos=selected_slos,
                custom_slos=st.session_state.custom_slos,
                teaching_style=teaching_style,
                assessment_preferences=assessment_prefs,
                bloom_levels=bloom_levels,
                ai_classroom_use=ai_classroom_use,
                sessions_per_week=sessions_per_week,
                duration_per_session=duration_per_session
            )
            
            logger.info(f"Course context created: {course_context.course_name}, {course_context.sessions_per_week} sessions/week")
            st.session_state.course_context = course_context
            
            # Store current instructions on first generation or when changed
            current_instructions = custom_instructions.strip()
            if st.session_state.regeneration_count == 0:
                st.session_state.base_custom_instructions = current_instructions
                st.session_state.current_custom_instructions = current_instructions
            else:
                # Track if instructions changed
                st.session_state.current_custom_instructions = current_instructions
            
            # Build cumulative prompt with proper priority
            final_custom_prompt = None
            context_parts = []
            
            # Always start with base instructions if they exist
            if st.session_state.base_custom_instructions:
                context_parts.append(f"ORIGINAL PROFESSOR INSTRUCTIONS:\n{st.session_state.base_custom_instructions}")
            
            # Add uploaded reference material. Capped: a full textbook is grounded via
            # retrieval (TextbookIndex), so only a short excerpt goes into the prompt here.
            if uploaded_context:
                context_parts.append(f"UPLOADED REFERENCE MATERIAL:\n{uploaded_context[:4000]}")
            
            # Add accumulated improvements with strong constraints
            if st.session_state.applied_suggestions_cumulative and st.session_state.regeneration_count > 0:
                context_parts.append(f"""PREVIOUSLY APPLIED IMPROVEMENTS (MANDATORY - DO NOT REGRESS):
{st.session_state.applied_suggestions_cumulative}

CRITICAL REQUIREMENTS:
1. Maintain ALL improvements listed above
2. Build upon them, never contradict or remove
3. Apply new suggestions while preserving previous enhancements
4. If any conflict arises, prioritize maintaining previous improvements""")
            
            # Add any new instructions from current regeneration
            if st.session_state.regeneration_count > 0 and current_instructions != st.session_state.base_custom_instructions:
                context_parts.append(f"ADDITIONAL INSTRUCTIONS:\n{current_instructions}")
            
            if context_parts:
                final_custom_prompt = "\n\n---\n\n".join(context_parts)
            
            logger.debug("Calling syllabus generator")
            
            # Generate syllabus
            generator = SyllabusGenerator(
                st.session_state.api_key,
                st.session_state.serper_api_key,
                st.session_state.model_type
            )

            # Textbook index is built in the Materials & Sources panel above.
            generator.textbook_index = st.session_state.get("textbook_index")
            generator.include_web = st.session_state.get("include_web_sources", True)

            # If the instructor previewed & curated sources, use exactly that selection
            # (otherwise the generator discovers sources live).
            if st.session_state.get("candidate_sources"):
                generator.curated_sources = st.session_state.get("selected_sources", [])
            
            # Create status container that works with async
            with st.status("🚀 Generating syllabus...", expanded=True) as status:
                content, qa_review = run_async(generator.generate(
                    course_context, 
                    custom_prompt=final_custom_prompt,  # Use ONLY cumulative prompt
                    status_container=status
                ))
                status.update(label="✅ Syllabus generation complete!", state="complete")
            
            # Extract topics from generated content
            logger.debug("Extracting topics from generated syllabus")
            extracted_topics = extract_syllabus_topics(content, course_context.weeks, course_context.sessions_per_week)
            st.session_state.syllabus_topics = extracted_topics
            logger.debug(f"Topics extracted: {len(extracted_topics)} topics for {course_context.weeks} weeks")
            
            # Generate actionable suggestions
            logger.debug("Generating actionable suggestions")
            qa_agent = QualityAssuranceAgent(st.session_state.api_key, st.session_state.model_type)
            
            # Pass previous suggestions as context for constraint
            previous_suggestions = st.session_state.applied_suggestions_cumulative if st.session_state.regeneration_count > 0 else ""
            
            actionable_suggestions = run_async(qa_agent.generate_actionable_suggestions(
                content.content,
                "syllabus",
                course_context,
                st.session_state.suggestion_granularity,
                previous_suggestions=previous_suggestions
            ))
            
            # Track suggestion history
            current_version = st.session_state.regeneration_count + 1
            suggestion_entry = {
                'version': current_version,
                'original_suggestions': actionable_suggestions,
                'edited_suggestions': actionable_suggestions,
                'applied': False,
                'timestamp': datetime.now()
            }
            st.session_state.suggestion_history.append(suggestion_entry)
            
            st.session_state.actionable_suggestions = actionable_suggestions
            st.session_state.edited_suggestions = actionable_suggestions
            
            content_id = st.session_state.content_manager.save_content("syllabus", content)
            st.session_state.generated_content["syllabus"] = {
                "content": content,
                "qa_review": qa_review,
                "content_id": content_id,
                "topics": extracted_topics,
                "actionable_suggestions": actionable_suggestions
            }
            st.session_state.syllabus_versions.append({
                "version": st.session_state.regeneration_count + 1,
                "content": content.content,  # Store actual text
                "timestamp": datetime.now(),
                "suggestions_applied": st.session_state.edited_suggestions,
                "qa_score": qa_review.get('overall_score', 0)
            })
            logger.info(f"Syllabus generated successfully. QA Score: {qa_review.get('overall_score', 'N/A')}")
            
            # Clear any previous errors
            if "syllabus" in st.session_state.generation_errors:
                del st.session_state.generation_errors["syllabus"]
            
        except Exception as e:
            logger.error(f"Syllabus generation failed: {e}", exc_info=True)
            error_msg = str(e)
            st.session_state.generation_errors["syllabus"] = error_msg
            st.error(f"Syllabus generation failed: {error_msg}")
    
    if render_generation_button("🚀 **Generate Syllabus**", is_valid, generate_syllabus):
        st.success("Syllabus generated successfully!")
        st.info("Content is grounded in cited sources — see the Grounding panel below.")
        st.balloons()
    
    # Display Generated Syllabus
    if "syllabus" in st.session_state.generated_content:
        st.markdown("---")
        syllabus_data = st.session_state.generated_content["syllabus"]
        course_context = st.session_state.course_context
        
        st.subheader(f"📄 Generated Syllabus: {course_context.course_code}")
        st.caption(f"{course_context.course_name} | {course_context.semester}")
        
        # Quality Review Section
        qa_review = syllabus_data["qa_review"]
        score = qa_review.get('overall_score', 0)
        
        col1, col2 = st.columns(2)
        with col1:
            if score >= 90:
                st.success(f"**Excellent Quality**: {score}/100")
            elif score >= 80:
                st.success(f"**Good Quality**: {score}/100")
            else:
                st.warning(f"**Quality**: {score}/100")
        
        with col2:
            if qa_review.get('passed_qa', False):
                st.success("✅ Passed QA")
            else:
                st.warning("⚠️ Review Suggested")
        
        # Grounding & sources panel
        render_grounding_panel(qa_review.get('grounding', {}))

        # Show rationale
        rationale = qa_review.get('rationale', '')
        if rationale and st.session_state.show_rationale:
            with st.expander("📊 **Assessment Rationale**"):
                st.markdown(rationale)

        # Live Editor
        edited_content = render_live_editor(
            syllabus_data["content"].content,
            "Syllabus",
            syllabus_data["content_id"]
        )
        
        # Version History and Suggestions Section
        st.markdown("---")
        st.subheader("💡 AI Suggestions & Version History")
        
        # Check version limit FIRST
        from config import MAX_SYLLABUS_VERSIONS
        version_count = len(st.session_state.suggestion_history) if st.session_state.suggestion_history else 0
        can_regenerate = version_count < MAX_SYLLABUS_VERSIONS
        
        # Show version status
        if st.session_state.suggestion_history:
            st.info(f"**Current:** Version {version_count} of {MAX_SYLLABUS_VERSIONS}")
            
            # Create version tabs
            tab_labels = [f"Version {i+1}" for i in range(version_count)]
            if version_count > 1:
                tab_labels.append("📊 Compare")
            
            version_tabs = st.tabs(tab_labels)
            
            # Display each version
            for idx in range(version_count):
                with version_tabs[idx]:
                    version_data = st.session_state.suggestion_history[idx]
                    
                    col1, col2, col3 = st.columns([2, 2, 1])
                    with col1:
                        st.caption(f"**Generated:** {version_data['timestamp'].strftime('%Y-%m-%d %H:%M')}")
                    with col2:
                        if version_data['applied']:
                            st.success("✅ Applied")
                        else:
                            st.info("⏳ Current Version")
                    with col3:
                        st.caption(f"**V{idx+1}**")
                    
                    # Show suggestions
                    st.markdown("### Improvement Suggestions")
                    
                    is_latest = (idx == version_count - 1)
                    can_edit = is_latest and can_regenerate
                    
                    if can_edit:
                        st.info("💡 Edit these suggestions to guide the next version")
                        edited_suggestions = st.text_area(
                            "Edit suggestions for next regeneration:",
                            value=version_data['edited_suggestions'],
                            height=300,
                            key=f"suggestions_v{idx}",
                            help="Modify or add specific improvements you want in the next version"
                        )
                        # Update in session state immediately
                        st.session_state.suggestion_history[idx]['edited_suggestions'] = edited_suggestions
                        st.session_state.edited_suggestions = edited_suggestions
                    else:
                        st.text_area(
                            "Applied suggestions:" if version_data['applied'] else "Suggestions:",
                            value=version_data['edited_suggestions'],
                            height=300,
                            disabled=True,
                            key=f"suggestions_readonly_v{idx}"
                        )
            
            # Comparison tab
            if version_count > 1:
                with version_tabs[-1]:
                    st.markdown("### Version Comparison")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"#### Version 1")
                        st.markdown(f"<div style='font-size: 0.85em; max-height: 500px; overflow-y: auto; border: 1px solid #ddd; padding: 10px;'>{st.session_state.suggestion_history[0]['edited_suggestions']}</div>", unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown(f"#### Version {version_count}")
                        st.markdown(f"<div style='font-size: 0.85em; max-height: 500px; overflow-y: auto; border: 1px solid #ddd; padding: 10px;'>{st.session_state.suggestion_history[-1]['edited_suggestions']}</div>", unsafe_allow_html=True)
        
        # Current granularity display
        st.caption(f"**Suggestion Detail Level:** {st.session_state.suggestion_granularity}")
        
        # Regenerate and Export buttons
        col1, col2, col3 = st.columns([2, 2, 2])
        
        with col1:
            if can_regenerate:
                button_label = f"🔄 Generate Version {version_count + 1}"
                button_help = f"Create improved version based on your edited suggestions ({version_count}/{MAX_SYLLABUS_VERSIONS})"
            else:
                button_label = "🔒 Max Versions Reached"
                button_help = f"You've reached the maximum of {MAX_SYLLABUS_VERSIONS} versions. Approve a version or start fresh."
            
            if st.button(button_label, use_container_width=True, type="secondary", disabled=not can_regenerate, help=button_help, key="syllabus_regen"):
                # Validation
                if not st.session_state.edited_suggestions.strip():
                    st.warning("Please add or edit suggestions before regenerating.")
                    st.stop()
                elif len(st.session_state.edited_suggestions.strip()) < 50:
                    st.warning("Suggestions seem too short. Please provide more detailed guidance (at least 50 characters).")
                    st.stop()
                
                # Mark current version as applied
                if st.session_state.suggestion_history:
                    current_idx = len(st.session_state.suggestion_history) - 1
                    st.session_state.suggestion_history[current_idx]['applied'] = True
                    
                    # Accumulate suggestions with version tracking
                    applied = st.session_state.suggestion_history[current_idx]['edited_suggestions']
                    if st.session_state.applied_suggestions_cumulative:
                        st.session_state.applied_suggestions_cumulative += f"\n\n---VERSION {current_idx + 1} IMPROVEMENTS (LOCKED IN)---\n{applied}"
                    else:
                        st.session_state.applied_suggestions_cumulative = f"VERSION 1 IMPROVEMENTS (LOCKED IN):\n{applied}"
                
                # Increment counter BEFORE generation
                st.session_state.regeneration_count += 1
                
                # Generate with accumulated context
                with st.spinner(f"Generating improved Version {version_count + 1}..."):
                    generate_syllabus()
                
                st.success(f"✅ Version {version_count + 1} generated successfully!")
                st.balloons()
                st.rerun()
            
            # Show version limit info if max reached
            if not can_regenerate:
                st.error(f"⚠️ Maximum versions reached ({MAX_SYLLABUS_VERSIONS})")
                st.info("To create more versions, approve the current syllabus or reset and start fresh.")
        
        with col2:
            metadata = {
                "Course": f"{course_context.course_code} - {course_context.course_name}",
                "Program": course_context.program_type,
                "Semester": course_context.semester,
                "Weeks": course_context.weeks,
                "Generated": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            render_export_buttons(
                edited_content, 
                f"Syllabus - {course_context.course_code}", 
                metadata,
                f"{course_context.course_code}_syllabus"
            )
        
        with col3:
            if st.button("✅ **Approve & Continue**", use_container_width=True, type="primary", key="syllabus_approve"):
                st.session_state.content_manager.approve_content(
                    syllabus_data["content_id"], 
                    "Approved by professor"
                )
                logger.info("Syllabus approved by professor")
                st.success("✅ Syllabus approved! Proceed to Lecture Notes tab.")
        
        # Show regeneration count
        if st.session_state.regeneration_count > 0:
            st.info(f"**Regenerations:** {st.session_state.regeneration_count}")
        
        # Topic extraction verification
        st.markdown("---")
        with st.expander("📋 **Extracted Topics for Lecture Generation**", expanded=False):
            if syllabus_data.get("topics"):
                st.success(f"✅ {len(syllabus_data['topics'])} topics extracted successfully")
                for topic in syllabus_data['topics'][:5]:
                    st.write(f"- Week {topic['week']}.{topic['module']}: {topic['topic']}")
                if len(syllabus_data['topics']) > 5:
                    st.write(f"... and {len(syllabus_data['topics']) - 5} more")
            else:
                st.warning("No topics extracted. This may cause issues in lecture generation.")

def render_lecture_notes_tab():
    """Render lecture notes generation tab with structured topic selection."""
    render_prompt_editor('lecture', 'Lecture Notes')
    st.header("📝 Lecture Notes Generation")
    
    if not st.session_state.course_context:
        st.warning("Please complete the syllabus setup first.")
        return
    
    if not st.session_state.api_key or not st.session_state.serper_api_key:
        st.error("Please provide both OpenAI and Serper API keys in the sidebar.")
        return
    
    course_context = st.session_state.course_context
    st.markdown(f"*Course: {course_context.course_code} - {course_context.course_name}*")
    
    # Get topics from syllabus
    available_topics = st.session_state.syllabus_topics
    
    if not available_topics:
        st.warning("No topics found from syllabus. Please generate syllabus first or check topic extraction.")
        return
    
    logger.debug(f"Available topics for lecture generation: {len(available_topics)}")
    
    # Lecture Selection
    st.subheader("🎯 Select Lecture to Generate")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Create dropdown options from extracted topics
        topic_options = []
        for topic in available_topics:
            display_text = f"Week {topic['week']}.{topic['module']}: {topic['topic'][:50]}..."
            topic_options.append((topic, display_text))
        
        if topic_options:
            selected_option = st.selectbox(
                "Select Session *", 
                options=[opt[1] for opt in topic_options]
            )
            
            # Find the corresponding topic data
            selected_index = next(i for i, opt in enumerate(topic_options) if opt[1] == selected_option)
            selected_topic_data = topic_options[selected_index][0]
            
            week_number = selected_topic_data['week']
            module_number = selected_topic_data['module']
            topic_text = selected_topic_data['topic']
            session_id = selected_topic_data['session']
            
            logger.debug(f"Selected topic: Week {week_number}.{module_number} - {topic_text}")
        else:
            st.error("No valid topics found for lecture generation")
            return
    
    with col2:
        lecture_format = st.selectbox("Generation Format *", options=[lf.value for lf in LectureFormat])
        
        # Show session information
        st.info(f"**Session:** {session_id}")
        st.info(f"**Duration:** {course_context.duration_per_session} minutes")
    
    with col3:
        st.write(f"**Course:** {course_context.course_name}")
        st.write(f"**Program:** {course_context.program_type}")
        st.write(f"**Available Sessions:** {len(available_topics)}")
        st.write(f"**Expected Total:** {course_context.weeks * course_context.sessions_per_week}")
    
    # Custom Prompt Option
    with st.expander("🎯 **Customize Generation (Optional)**"):
        custom_prompt = st.text_area("Custom Instructions:", placeholder="Add specific requirements...", height=100)
    
    # Validation
    required_fields = {
        "topic_text": topic_text,
        "lecture_format": lecture_format,
        "api_key": st.session_state.api_key,
        "serper_api_key": st.session_state.serper_api_key
    }
    
    is_valid = validate_and_show_errors(required_fields, "Lecture Generation")
    
    def generate_lecture():
        """Generate lecture content with direct data passing."""
        logger.info(f"Starting lecture generation: Week {week_number}.{module_number} - {topic_text}")
        
        try:
            generator = LectureNotesGenerator(
                st.session_state.api_key,
                st.session_state.serper_api_key,
                st.session_state.model_type
            )
            # Reuse the textbook indexed on the Syllabus tab + the web-sources toggle,
            # so lectures are grounded in the same materials (per-topic retrieval).
            generator.textbook_index = st.session_state.get("textbook_index")
            generator.include_web = st.session_state.get("include_web_sources", True)

            format_enum = LectureFormat.AI_SCRIPT if lecture_format == "Generate as AI Script" else LectureFormat.NOTES
            
            logger.debug("Calling lecture generator")
            content, qa_review = run_async(generator.generate(
                week_number, topic_text, course_context, 
                format_enum, custom_prompt
            ))
            
            content_id = st.session_state.content_manager.save_content("lecture_notes", content)
            st.session_state.generated_content["lecture_notes"] = {
                "content": content,
                "qa_review": qa_review,
                "content_id": content_id,
                "week": week_number,
                "module": module_number,
                "session_id": session_id,
                "topic": topic_text,
                "format": lecture_format
            }
            
            logger.info(f"Lecture generated successfully. QA Score: {qa_review.get('overall_score', 'N/A')}")
            
            # Clear any previous errors
            if "lecture_notes" in st.session_state.generation_errors:
                del st.session_state.generation_errors["lecture_notes"]
            
        except Exception as e:
            logger.error(f"Lecture generation failed: {e}", exc_info=True)
            error_msg = str(e)
            st.session_state.generation_errors["lecture_notes"] = error_msg
            st.error(f"Lecture generation failed: {error_msg}")
    
    if render_generation_button("🚀 **Generate Complete Lecture**", is_valid, generate_lecture):
        st.success(f"Complete {lecture_format} generated for {session_id}!")
        st.info("Current references and industry examples have been included!")
        st.balloons()
    
    # Display Generated Content
    if "lecture_notes" in st.session_state.generated_content:
        st.markdown("---")
        lecture_data = st.session_state.generated_content["lecture_notes"]
        
        st.subheader(f"📝 {lecture_data['session_id']} Lecture: {lecture_data['topic']}")
        st.caption(f"Format: {lecture_data['format']} | Duration: {course_context.duration_per_session} minutes")
        
        # Simplified Quality Review
        qa_review = lecture_data["qa_review"]
        score = qa_review.get('overall_score', 0)
        
        col1, col2 = st.columns(2)
        with col1:
            if score >= 90:
                st.success(f"**Excellent Quality**: {score}/100")
            elif score >= 80:
                st.success(f"**Good Quality**: {score}/100")
            else:
                st.warning(f"**Quality**: {score}/100")
        
        with col2:
            if qa_review.get('passed_qa', False):
                st.success("✅ Passed QA")
            else:
                st.warning("⚠️ Review Suggested")
        
        # Show rationale
        rationale = qa_review.get('rationale', '')
        if rationale and st.session_state.show_rationale:
            with st.expander("📊 **Assessment Rationale**"):
                st.markdown(rationale)
        
        # Live Editor
        edited_content = render_live_editor(
            lecture_data["content"].content, 
            f"Lecture {lecture_data['session_id']} Notes", 
            lecture_data["content_id"]
        )
        
        # Update content if edited
        if edited_content != lecture_data["content"].content:
            lecture_data["content"].content = edited_content
            logger.debug("Lecture content updated by user")

        # Export and Approval
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            metadata = {
                "Course": f"{course_context.course_code} - {course_context.course_name}",
                "Lecture": lecture_data['session_id'],
                "Topic": lecture_data['topic'],
                "Format": lecture_data['format'],
                "Duration": f"{course_context.duration_per_session} minutes",
                "Generated": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            render_export_buttons(
                edited_content, 
                f"Lecture {lecture_data['session_id']} Notes", 
                metadata,
                f"{course_context.course_code}_lecture_{lecture_data['session_id']}"
            )
        
        with col3:
            if st.button("✅ **Approve & Continue**", use_container_width=True, type="primary", key="lecture_approve_btn"):
                st.session_state.content_manager.approve_content(lecture_data["content_id"], "Approved by professor")
                logger.info("Lecture notes approved by professor")
                st.success("Lecture notes approved! You can now proceed to Assignment Generation.")


def render_assignment_tab():
    """Render assignment generation tab with direct data passing."""
    render_prompt_editor('assignment', 'Assignment') 
    logger.debug("Rendering assignment tab")
    st.header("📝 Assignment Generation")
    
    if not st.session_state.course_context:
        st.warning("Please complete the syllabus setup first.")
        return
    
    if not st.session_state.api_key or not st.session_state.serper_api_key:
        st.error("Please provide both OpenAI and Serper API keys in the sidebar.")
        return
    
    course_context = st.session_state.course_context
    st.markdown(f"*Course: {course_context.course_code} - {course_context.course_name}*")
    
    # Assignment Setup
    col1, col2 = st.columns(2)
    
    with col1:
        assignment_week = st.selectbox("Assignment Week *", options=list(range(1, course_context.weeks + 1)))
        assignment_topic = st.text_input("Assignment Topic *", placeholder="e.g., Strategic Analysis of Fortune 500 Company")
    
    with col2:
        # Show context from previous content
        if "lecture_notes" in st.session_state.generated_content:
            lecture_info = st.session_state.generated_content['lecture_notes']
            st.info(f"📝 **Lecture Context Available**\n{lecture_info['session_id']}: {lecture_info['topic']}")
        
        if "syllabus" in st.session_state.generated_content:
            st.info("📄 **Syllabus Context Available**\nCourse structure and SLOs integrated")
    
    # Custom Prompt
    st.subheader("🎯 **Customize Assignment (Optional)**")
    assignment_custom_prompt = st.text_area("Specific Requirements:", placeholder="Add specific requirements...", height=100)
    
    # Validation
    required_fields = {
        "assignment_week": assignment_week,
        "assignment_topic": assignment_topic,
        "api_key": st.session_state.api_key,
        "serper_api_key": st.session_state.serper_api_key
    }
    
    is_valid = validate_and_show_errors(required_fields, "Assignment Generation")
    
    def generate_assignment():
        """Generate assignment with direct data passing."""
        logger.info(f"Starting assignment generation for Week {assignment_week}: {assignment_topic}")
        
        try:
            generator = AssignmentGenerator(
                st.session_state.api_key,
                st.session_state.serper_api_key,
                st.session_state.model_type
            )
            generator.textbook_index = st.session_state.get("textbook_index")
            generator.include_web = st.session_state.get("include_web_sources", True)

            logger.debug("Calling assignment generator")
            content, qa_review = run_async(generator.generate(
                assignment_week, assignment_topic, course_context,
                assignment_custom_prompt or None
            ))
            
            content_id = st.session_state.content_manager.save_content("assignment", content)
            st.session_state.generated_content["assignments"] = {
                "content": content,
                "qa_review": qa_review,
                "content_id": content_id,
                "week": assignment_week,
                "topic": assignment_topic
            }
            
            logger.info(f"Assignment generated successfully. QA Score: {qa_review.get('overall_score', 'N/A')}")
            
            if "assignment" in st.session_state.generation_errors:
                del st.session_state.generation_errors["assignment"]
            
        except Exception as e:
            logger.error(f"Assignment generation failed: {e}", exc_info=True)
            error_msg = str(e)
            st.session_state.generation_errors["assignment"] = error_msg
            st.error(f"Assignment generation failed: {error_msg}")
    
    if render_generation_button("🚀 **Generate Assignment**", is_valid, generate_assignment):
        st.success(f"Assignment generated for Week {assignment_week}!")
        st.info("Current industry examples and case studies have been included!")
        st.balloons()
    
    # Display Generated Assignment
    if "assignments" in st.session_state.generated_content:
        logger.debug("Displaying generated assignment")
        st.markdown("---")
        assignment_data = st.session_state.generated_content["assignments"]
        
        st.subheader(f"📝 Week {assignment_data['week']} Assignment: {assignment_data['topic']}")
        
        # Simplified Quality Review
        qa_review = assignment_data["qa_review"]
        score = qa_review.get('overall_score', 0)
        
        col1, col2 = st.columns(2)
        with col1:
            if score >= 90:
                st.success(f"**Excellent Quality**: {score}/100")
            elif score >= 80:
                st.success(f"**Good Quality**: {score}/100")
            else:
                st.warning(f"**Quality**: {score}/100")
        
        with col2:
            if qa_review.get('passed_qa', False):
                st.success("✅ Passed QA")
            else:
                st.warning("⚠️ Review Suggested")
        
        # Show rationale
        rationale = qa_review.get('rationale', '')
        if rationale and st.session_state.show_rationale:
            with st.expander("📊 **Assessment Rationale**"):
                st.markdown(rationale)
        
        # Live Editor
        edited_content = render_live_editor(
            assignment_data["content"].content, 
            f"Assignment (Week {assignment_data['week']})", 
            assignment_data["content_id"]
        )
        
        # Update content if edited
        if edited_content != assignment_data["content"].content:
            assignment_data["content"].content = edited_content
            logger.debug("Assignment content updated by user")
        
        # Export and Approval
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            metadata = {
                "Course": f"{course_context.course_code} - {course_context.course_name}",
                "Assignment Week": f"Week {assignment_data['week']}",
                "Topic": assignment_data['topic'],
                "Generated": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            render_export_buttons(
                edited_content, 
                f"Week {assignment_data['week']} Assignment", 
                metadata,
                f"{course_context.course_code}_week{assignment_data['week']}_assignment"
            )
        
        with col3:
            if st.button("✅ **Approve & Continue**", use_container_width=True, type="primary", key="assignment_approve"):
                st.session_state.content_manager.approve_content(assignment_data["content_id"], "Approved by professor")
                logger.info("Assignment approved by professor")
                st.success("Assignment approved! You can now proceed to Assignment Grader.")

def render_grader_tab():
    """Render grading rubric generation tab with direct data passing."""
    render_prompt_editor('rubric', 'Grading Rubric')
    logger.debug("Rendering grader tab")
    st.header("📊 Assignment Grader & Rubric")
    
    if not st.session_state.course_context:
        st.warning("Please complete the syllabus setup first.")
        return
    
    if "assignments" not in st.session_state.generated_content:
        st.warning("Please generate an assignment first.")
        return
    
    if not st.session_state.api_key:
        st.error("Please provide OpenAI API key in the sidebar.")
        return
    
    assignment_data = st.session_state.generated_content["assignments"]
    course_context = st.session_state.course_context
    
    logger.info(f"Grader tab loaded for assignment: Week {assignment_data['week']} - {assignment_data['topic']}")
    st.markdown(f"*Creating grading rubric for: Week {assignment_data['week']} - {assignment_data['topic']}*")
    
    # Rubric Configuration
    with st.expander("⚙️ **Rubric Configuration**", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            grading_scale = st.selectbox("Grading Scale", options=["4-Point Scale (A-F)", "100-Point Scale", "Pass/Fail", "Custom"])
            feedback_style = st.selectbox("Feedback Style", options=["Constructive & Growth-Focused", "Direct & Specific", "Encouraging & Supportive", "Analytical & Detailed"])
        
        with col2:
            include_examples = st.checkbox("Include Performance Examples", value=True)
            include_self_assessment = st.checkbox("Include Self-Assessment Version", value=True)
    
    # Custom Rubric Instructions
    with st.expander("🎯 **Custom Rubric Instructions (Optional)**"):
        rubric_custom_prompt = st.text_area("Specific Rubric Requirements:", placeholder="Add specific criteria...", height=100)
    
    def generate_rubric():
        """Generate grading rubric with direct data passing."""
        logger.info(f"Starting rubric generation for assignment: {assignment_data['topic']}")
        
        try:
            generator = GradingRubricGenerator(st.session_state.api_key, st.session_state.model_type)
            
            logger.debug("Calling rubric generator")
            content, qa_review = run_async(generator.generate(
                assignment_data["content"].content,
                course_context,
                rubric_custom_prompt or None
            ))
            
            content_id = st.session_state.content_manager.save_content("grading_rubric", content)
            st.session_state.generated_content["grading_rubric"] = {
                "content": content,
                "qa_review": qa_review,
                "content_id": content_id,
                "assignment_week": assignment_data['week'],
                "assignment_topic": assignment_data['topic'],
                "config": {
                    "grading_scale": grading_scale,
                    "feedback_style": feedback_style,
                    "include_examples": include_examples,
                    "include_self_assessment": include_self_assessment
                }
            }
            
            logger.info(f"Rubric generated successfully. QA Score: {qa_review.get('overall_score', 'N/A')}")
            
            if "grading_rubric" in st.session_state.generation_errors:
                del st.session_state.generation_errors["grading_rubric"]
            
        except Exception as e:
            logger.error(f"Rubric generation failed: {e}", exc_info=True)
            error_msg = str(e)
            st.session_state.generation_errors["grading_rubric"] = error_msg
            st.error(f"Rubric generation failed: {error_msg}")
    
    if render_generation_button("🚀 **Generate Grading Rubric**", True, generate_rubric):
        st.success("Grading rubric generated!")
        st.balloons()
    
    # Display Generated Rubric
    if "grading_rubric" in st.session_state.generated_content:
        logger.debug("Displaying generated grading rubric")
        st.markdown("---")
        rubric_data = st.session_state.generated_content["grading_rubric"]
        
        st.subheader(f"📊 Grading Rubric: {rubric_data['assignment_topic']}")
        st.caption(f"Assignment Week: {rubric_data['assignment_week']} | Scale: {rubric_data['config']['grading_scale']}")
        
        # Simplified Quality Review
        qa_review = rubric_data["qa_review"]
        score = qa_review.get('overall_score', 0)
        
        col1, col2 = st.columns(2)
        with col1:
            if score >= 90:
                st.success(f"**Excellent Quality**: {score}/100")
            elif score >= 80:
                st.success(f"**Good Quality**: {score}/100")
            else:
                st.warning(f"**Quality**: {score}/100")
        
        with col2:
            if qa_review.get('passed_qa', False):
                st.success("✅ Passed QA")
            else:
                st.warning("⚠️ Review Suggested")
        
        # Show rationale
        rationale = qa_review.get('rationale', '')
        if rationale and st.session_state.show_rationale:
            with st.expander("📊 **Assessment Rationale**"):
                st.markdown(rationale)
        
        # Live Editor
        edited_content = render_live_editor(
            rubric_data["content"].content, 
            f"Grading Rubric (Week {rubric_data['assignment_week']})", 
            rubric_data["content_id"]
        )
        
        # Update content if edited
        if edited_content != rubric_data["content"].content:
            rubric_data["content"].content = edited_content
            logger.debug("Rubric content updated by user")
        
        # Final Export and Completion
        st.markdown("---")
        st.subheader("🎉 Course Complete!")
        st.success("Congratulations! You have successfully created a complete course package with AI assistance.")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📦 **Download Complete Course Package**", use_container_width=True, type="primary"):
                logger.info("Creating complete course package download")
                # Create comprehensive package
                all_content = {
                    "course_info": asdict(course_context),
                    "syllabus": st.session_state.generated_content.get("syllabus", {}).get("content", {}).content if "syllabus" in st.session_state.generated_content else "",
                    "lecture_notes": st.session_state.generated_content.get("lecture_notes", {}).get("content", {}).content if "lecture_notes" in st.session_state.generated_content else "",
                    "assignment": st.session_state.generated_content.get("assignments", {}).get("content", {}).content if "assignments" in st.session_state.generated_content else "",
                    "grading_rubric": edited_content,
                    "generation_date": datetime.now().isoformat(),
                    "quality_scores": {
                        content_type: data.get("qa_review", {}).get("overall_score", 0)
                        for content_type, data in st.session_state.generated_content.items()
                    }
                }
                
                package_json = json.dumps(all_content, indent=2, default=str)
                
                st.download_button(
                    label="Download Complete Package (JSON)",
                    data=package_json,
                    file_name=f"{course_context.course_code}_complete_course.json",
                    mime="application/json"
                )
        
        with col2:
            metadata = {
                "Course": f"{course_context.course_code} - {course_context.course_name}",
                "Assignment": f"Week {rubric_data['assignment_week']} - {rubric_data['assignment_topic']}",
                "Grading Scale": rubric_data['config']['grading_scale'],
                "Generated": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            render_export_buttons(
                edited_content, 
                f"Grading Rubric - Week {rubric_data['assignment_week']}", 
                metadata,
                f"{course_context.course_code}_week{rubric_data['assignment_week']}_rubric"
            )
        
        with col3:
            if st.button("Final Approval", use_container_width=True, type="primary"):
                st.session_state.content_manager.approve_content(rubric_data["content_id"], "Final approval - Course creation complete")
                logger.info("Final course approval completed")
                st.success("Course creation completed successfully!")
                st.balloons()

def main():
    """Main application function with enhanced error handling."""
    logger.info("Starting Autonomous Course Builder application")
    
    st.set_page_config(
        page_title="Autonomous Course Builder",
        page_icon="🎓",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    try:
        logger.info(f"ACB main() run — build {APP_BUILD}")
        init_session_state()
        # Defensive belt-and-suspenders: prove (and fix) any missing prompt keys.
        for k, v in (('custom_prompts', {}), ('prompt_versions', []), ('active_prompt_version', None)):
            if k not in st.session_state:
                st.session_state[k] = v
                logger.warning(f"DEFENSIVE: session key '{k}' was missing after init — set it now")
        render_header()
        
        # Dependency warning
        missing_deps = get_missing_dependencies()
        render_dependency_warning(missing_deps)
        
        # Sidebar
        render_sidebar()
        
        # Main tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "Generate Syllabus", 
            "Lecture Notes", 
            "Assignment Generation", 
            "Assignment Grader"
        ])
        
        with tab1:
            render_syllabus_tab()
        
        with tab2:
            render_lecture_notes_tab()
        
        with tab3:
            render_assignment_tab()
        
        with tab4:
            render_grader_tab()
        
        # Footer
        st.markdown("---")
        st.markdown(
            """
            <div style='text-align: center; color: #666; font-size: 0.8em; margin-top: 2rem;'>
                Autonomous Course Builder
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        logger.debug("Application rendered successfully")
        
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        st.error(f"Application error: {e}")
        st.info("Please refresh the page and try again. If the problem persists, check your API keys and dependencies.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"Application startup error: {e}", exc_info=True)
        print(f"CRITICAL ERROR: {e}")
        st.error(f"Application error: {e}")
        st.info("Please refresh the page and try again. If the problem persists, check your API keys and dependencies.")


