
"""
UI Components 
Reusable Streamlit components with improved error handling and progress feedback.
"""

import html
import streamlit as st
from typing import Dict, Any, List, Tuple
from datetime import datetime

from config import QA_PASS_THRESHOLD, QA_EXCELLENT_THRESHOLD

def render_quality_review(qa_review: Dict[str, Any]) -> None:
    """Render comprehensive quality assurance review results."""
    st.subheader("Quality Assurance Review")
    
    score = qa_review.get('overall_score', 0)
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if score >= QA_EXCELLENT_THRESHOLD:
            st.metric("Quality Score", f"{score}/100", delta="Excellent")
            st.success("Excellent Quality")
        elif score >= QA_PASS_THRESHOLD:
            st.metric("Quality Score", f"{score}/100", delta="Very Good")
            st.success("Passed QA Review")
        elif score >= 80:
            st.metric("Quality Score", f"{score}/100", delta="Good")
            st.info("Good Quality")
        elif score >= 70:
            st.metric("Quality Score", f"{score}/100", delta="Satisfactory")
            st.warning("Satisfactory Quality")
        else:
            st.metric("Quality Score", f"{score}/100", delta="Needs Work")
            st.error("Below Standards")
    
    with col2:
        criterion_scores = qa_review.get('criterion_scores', {})
        if criterion_scores:
            avg_criterion = sum(criterion_scores.values()) / len(criterion_scores)
            st.metric("Criteria Average", f"{avg_criterion:.1f}/25")
            
            st.markdown("**Detailed Scores:**")
            for criterion, score in criterion_scores.items():
                progress_value = score / 25
                st.write(f"**{criterion.title()}**: {score}/25")
                st.progress(progress_value)
    
    with col3:
        passed_qa = qa_review.get('passed_qa', False)
        if passed_qa:
            st.success(f"✅ Passed QA Review (≥{QA_PASS_THRESHOLD}%)")
            if score < QA_EXCELLENT_THRESHOLD:
                st.info("Consider implementing recommendations for excellence")
        else:
            st.error(f"❌ Failed QA Review - Revision Recommended (<{QA_PASS_THRESHOLD}%)")
            st.warning("Review suggestions below and retry generation")
    
    col1, col2 = st.columns(2)
    
    with col1:
        strengths = qa_review.get('strengths', [])
        if strengths:
            with st.expander("✅ Strengths", expanded=True):
                for i, strength in enumerate(strengths, 1):
                    st.write(f"{i}. {strength}")
    
    with col2:
        improvements = qa_review.get('improvements', [])
        if improvements:
            with st.expander("🔧 Areas for Improvement", expanded=True):
                for i, improvement in enumerate(improvements, 1):
                    st.write(f"{i}. {improvement}")
    
    recommendations = qa_review.get('recommendations', [])
    if recommendations:
        with st.expander("💡 Actionable Recommendations"):
            st.markdown("**Specific actions you can take to improve quality:**")
            for i, rec in enumerate(recommendations, 1):
                st.write(f"{i}. {rec}")
    
    rationale = qa_review.get('rationale', '')
    if rationale and len(rationale) > 50:
        with st.expander("📊 Detailed QA Analysis"):
            st.markdown(rationale)
    
    if score < QA_PASS_THRESHOLD:
        st.markdown("---")
        st.error("**Quality Improvement Required**")
        improvement_suggestions = [
            "Select additional SLOs that better align with course content",
            "Try a different teaching style approach",
            "Provide more detailed custom instructions",
            "Upload reference materials for better context",
            "Switch to a more powerful AI model (GPT-4o)",
            "Simplify the topic or break it into smaller components"
        ]
        
        st.markdown("**Suggested Actions:**")
        for suggestion in improvement_suggestions:
            st.write(f"• {suggestion}")

def render_live_editor(content: str, content_type: str, content_id: str) -> str:
    """Render enhanced live preview and edit interface."""
    st.subheader(f"Live Editor - {content_type.title()}")
    
    edit_tab, preview_tab = st.tabs(["✏️ Edit Content", "👁️ Live Preview"])
    
    with edit_tab:
        st.markdown("**Edit the generated content:**")
        edited_content = st.text_area(
            "Content Editor",
            value=content,
            height=400,
            key=f"editor_{content_id}",
            help="Make any adjustments to the generated content"
        )
        
        word_count = len(edited_content.split())
        char_count = len(edited_content)
        st.caption(f"Words: {word_count} | Characters: {char_count}")
    
    with preview_tab:
        st.markdown("**Live Preview:**")
        with st.container():
            st.markdown(edited_content)
    
    return edited_content

def render_export_buttons(content: str, title: str, metadata: Dict[str, str], 
                         filename_prefix: str) -> None:
    """Render enhanced PDF and Word export buttons."""
    from export_manager import ExportManager
    
    col1, col2, col3 = st.columns([2, 2, 2]) 
    
    with col1:
        if st.button("📄 Download PDF", use_container_width=True, key=f"pdf_btn_{filename_prefix}"):
            try:
                with st.spinner("Creating PDF..."):
                    pdf_buffer = ExportManager.create_pdf(content, title, metadata)
                    file_ext = ExportManager.get_file_extension('pdf')
                    mime_type = ExportManager.get_mime_type('pdf')
                    
                    st.download_button(
                        label=f"⬇️ Download {file_ext.upper()}",
                        data=pdf_buffer,
                        file_name=f"{filename_prefix}.{file_ext}",
                        mime=mime_type,
                        key=f"pdf_download_{filename_prefix}"
                    )
                    st.success("PDF ready for download!")
            except Exception as e:
                st.error(f"PDF export failed: {e}")
                st.info("Try the Word export or copy the text manually")
    
    with col2:
        if st.button("📝 Word", use_container_width=True, key=f"word_btn_{filename_prefix}"):
            try:
                with st.spinner("Creating Word document..."):
                    word_buffer = ExportManager.create_word_doc(content, title, metadata)
                    file_ext = ExportManager.get_file_extension('word')
                    mime_type = ExportManager.get_mime_type('word')
                    
                    st.download_button(
                        label=f"⬇️ Download {file_ext.upper()}",
                        data=word_buffer,
                        file_name=f"{filename_prefix}.{file_ext}",
                        mime=mime_type,
                        key=f"word_download_{filename_prefix}"
                    )
                    st.success("Word document ready for download!")
            except Exception as e:
                st.error(f"Word export failed: {e}")
                st.info("Try the PDF export or copy the text manually")
    
    with col3:
        if st.button("📋 Copy", use_container_width=True, key=f"copy_btn_{filename_prefix}"):
            st.text_area("Copy this content:", value=content, height=100, key=f"copy_area_{filename_prefix}")
            st.info("Content displayed above - use Ctrl+A, Ctrl+C to copy")

def render_progress_tracker(generated_content: Dict[str, Any]) -> None:
    """Render enhanced progress tracking sidebar component."""
    st.subheader("📊 Progress Tracker")
    
    progress_steps = [
        ("Generate Syllabus", "syllabus"),
        ("Lecture Notes", "lecture_notes"), 
        ("Assignment Generation", "assignments"),
        ("Assignment Grader", "grading_rubric")
    ]
    
    completed_count = 0
    total_steps = len(progress_steps)
    
    for step_name, step_key in progress_steps:
        if step_key in generated_content:
            completed_count += 1
            qa_score = generated_content[step_key].get("qa_review", {}).get("overall_score", 0)
            
            if qa_score >= QA_EXCELLENT_THRESHOLD:
                icon = "⭐"
                status = "Excellent"
            elif qa_score >= QA_PASS_THRESHOLD:
                icon = "✅"
                status = "Completed"
            else:
                icon = "⚠️"
                status = "Needs Review"
            
            st.write(f"{icon} {step_name} - {status}")
            if qa_score > 0:
                st.caption(f"Quality Score: {qa_score}/100")
        else:
            st.write(f"⏳ {step_name}")
    
    progress_percentage = completed_count / total_steps
    st.progress(progress_percentage)
    st.caption(f"Overall Progress: {completed_count}/{total_steps} steps completed")

def render_dependency_warning(missing_deps: List[str]) -> None:
    """Render enhanced dependency warning component."""
    if missing_deps:
        with st.expander("⚠️ Dependency Information", expanded=False):
            st.warning("Some optional dependencies are missing:")
            for dep in missing_deps:
                st.write(f"• {dep}")
            
            st.info("**Impact:** File uploads and exports may be affected")
            st.markdown("**To install:** `pip install -r requirements.txt`")
            
            if st.button("🔄 Refresh Dependencies", key="refresh_deps"):
                st.rerun()

def render_api_configuration() -> Tuple[str, str, str]:
    """Render enhanced API configuration sidebar."""
    st.header("⚙️ Configuration")
    
    st.subheader("🤖 OpenAI Configuration")
    api_key = st.text_input(
        "OpenAI API Key *", 
        type="password", 
        value=st.session_state.get('api_key', ''),
        help="Required for AI content generation"
    )
    
    if api_key and not api_key.startswith('sk-'):
        st.warning("⚠️ OpenAI API keys typically start with 'sk-'")
    
    from config import ModelType
    model_options = {
        ModelType.GPT_4O.value: "GPT-4o (Balanced, Recommended)",
        ModelType.GPT_4O_MINI.value: "GPT-4o Mini (Fast, Cost-effective)", 
        ModelType.GPT_4_TURBO.value: "GPT-4 Turbo (High Quality)",
        ModelType.CLAUDE_SONNET.value: "Claude Sonnet 3.5 (Anthropic)",
        ModelType.GEMINI_PRO.value: "Gemini Pro (Google)"
    }
    
    model_type = st.selectbox(
        "AI Model *",
        options=list(model_options.keys()),
        format_func=lambda x: model_options[x],
        index=0,
        help="Choose AI model for content generation"
    )
    
    st.markdown("---")
    
    st.subheader("🔍 Serper API (Required)")
    st.info("**Serper API is mandatory for:**\n• Current academic references\n• Industry examples\n• Up-to-date case studies\n• Credible source integration")
    
    serper_api_key = st.text_input(
        "Serper API Key *", 
        type="password", 
        value=st.session_state.get('serper_api_key', ''),
        help="Required for current references and industry examples"
    )
    
    if not serper_api_key:
        st.error("❌ Serper API key required for course generation")
        st.markdown("**Get your free API key:** [serper.dev](https://serper.dev)")
        st.markdown("**Free tier:** 2,500 searches/month")
    elif len(serper_api_key) < 10:
        st.warning("⚠️ Serper API key seems too short")
    
    st.markdown("---")
    
    if st.button("💾 Save API Keys", use_container_width=True, type="primary"):
        if api_key and serper_api_key:
            st.session_state.api_key = api_key
            st.session_state.serper_api_key = serper_api_key  
            st.session_state.model_type = model_type
            st.success("✅ API keys saved successfully!")
            st.rerun()
        else:
            st.error("Please enter both API keys before saving.")

    if api_key and serper_api_key:
        st.success("✅ All APIs configured")
    elif api_key:
        st.warning("⚠️ Missing Serper API key")
    elif serper_api_key:
        st.warning("⚠️ Missing OpenAI API key")
    else:
        st.error("❌ Both API keys required")
    
    return api_key, serper_api_key, model_type

def render_grounding_panel(grounding: Dict[str, Any]) -> None:
    """Render the source-grounding summary for a generated artifact (read-only).

    `grounding` is the qa_review['grounding'] dict produced by the generator:
    strength, sources[], citation_count, orphans_removed[], slo_coverage.
    """
    if not grounding:
        return

    strength = grounding.get("strength", "")
    sources = grounding.get("sources", []) or []
    cited = grounding.get("citation_count", 0)
    orphans = len(grounding.get("orphans_removed", []) or [])
    slo_cov = int(grounding.get("slo_coverage", 0) * 100)

    if strength.startswith("Strong"):
        st.success(f"🔎 Grounding: **{strength}**")
    elif strength.startswith("Medium"):
        st.info(f"🔎 Grounding: **{strength}**")
    else:
        st.warning(f"🔎 Grounding: **{strength}**")

    n_academic = sum(1 for s in sources if s.get("tier") == 2)
    n_current = sum(1 for s in sources if s.get("tier") == 3)
    n_textbook = sum(1 for s in sources if s.get("tier") == 1)

    c1, c2, c3 = st.columns(3)
    c1.metric("Sources", len(sources))
    c2.metric("Citations used", cited)
    c3.metric("SLO coverage", f"{slo_cov}%")

    breakdown = []
    if n_textbook:
        breakdown.append(f"📘 {n_textbook} textbook")
    if n_academic:
        breakdown.append(f"🎓 {n_academic} research")
    if n_current:
        breakdown.append(f"🌐 {n_current} current/industry")
    if breakdown:
        st.caption("Source mix: " + " · ".join(breakdown))
    if orphans:
        st.caption(f"🧹 {orphans} unsourced/fabricated citation(s) removed automatically.")

    if sources:
        with st.expander(f"📚 Sources ({len(sources)})", expanded=False):
            for tier in (1, 2, 3):
                tier_docs = [s for s in sources if s.get("tier") == tier]
                if not tier_docs:
                    continue
                st.markdown(f"**{tier_docs[0].get('tier_label', 'Sources')}**")
                rows = []
                for s in tier_docs:
                    title = html.escape(s.get("title", "Untitled"))
                    label = html.escape(s.get("label", ""))
                    url = s.get("url", "")
                    if url:
                        safe_url = html.escape(url, quote=True)
                        # open in a new tab so the instructor doesn't lose their work
                        link = (f'<a href="{safe_url}" target="_blank" '
                                f'rel="noopener noreferrer">{title}</a>')
                    else:
                        link = title
                    rows.append(f"<li>[{s['id']}] {link} — <em>{label}</em></li>")
                st.markdown("<ul>" + "".join(rows) + "</ul>", unsafe_allow_html=True)
    else:
        st.caption("No external sources were available; content was kept qualitative (no fabricated facts).")


def render_candidate_sources(candidates: List[Any], has_textbook: bool) -> List[Any]:
    """Render curatable source candidates with checkboxes; return the selected ones.

    `candidates` is a list of grounding.SourceDoc (tiers 2/3). Checkbox state is
    keyed in session_state so selections persist across reruns. Returns the
    SourceDoc objects the instructor kept selected.
    """
    from grounding.models import TIER_LABEL

    selected: List[Any] = []
    if candidates:
        st.markdown("**Select sources to ground generation** *(uncheck any to exclude)*")
        for tier in (2, 3):
            tier_docs = [(i, c) for i, c in enumerate(candidates) if getattr(c, "tier", None) == tier]
            if not tier_docs:
                continue
            st.caption(TIER_LABEL.get(tier, "Sources"))
            for i, c in tier_docs:
                title = c.title if len(c.title) <= 90 else c.title[:90] + "…"
                key = f"src_sel_{i}"
                checked = st.checkbox(
                    f"{title} — {c.citation_label()}",
                    value=st.session_state.get(key, True),
                    key=key,
                )
                if checked:
                    selected.append(c)

    # Projected grounding strength (mirrors grounding.source_pool.assemble_pool logic)
    has_external = len(selected) > 0
    if has_textbook:
        label = "Strong (textbook-grounded)"
    elif has_external:
        label = "Medium (external sources cited)"
    else:
        label = "Light (no external sources — generic)"

    detail = f"{len(selected)} external source(s) selected" + (" · textbook indexed" if has_textbook else "")
    if has_textbook or has_external:
        st.info(f"🔎 Projected grounding: **{label}** · {detail}")
    else:
        st.warning(f"🔎 Projected grounding: **{label}** · {detail}")
    return selected


def render_file_upload_section() -> Tuple[str, str]:
    """Render enhanced file upload section."""
    st.markdown("**Upload Reference Materials (Optional):**")
    st.markdown("*Upload syllabi, course materials, or other documents (PDF, DOCX, TXT, MD):*")
    
    uploaded_file = st.file_uploader(
        "Choose file to upload",
        type=['txt', 'md', 'pdf', 'docx'],
        help="Upload reference materials to improve generation quality"
    )
    
    file_description = ""
    uploaded_context = ""
    st.session_state.uploaded_raw_text = ""  # raw extracted text for textbook indexing

    if uploaded_file:
        file_size = uploaded_file.size
        if file_size > 10 * 1024 * 1024:
            st.error("❌ File too large. Please upload files smaller than 10MB.")
            return "", ""
        
        file_description = st.text_area(
            "File Description (Required) *:",
            placeholder="Describe what this file contains and how it should inform the generation (e.g., 'Sample syllabus from similar course', 'University policy requirements', etc.)",
            height=75,
            help="This description helps the AI understand how to use your uploaded content"
        )
        
        if file_description and file_description.strip():
            try:
                from utils import process_uploaded_file
                
                with st.spinner("Processing uploaded file..."):
                    content = process_uploaded_file(uploaded_file)
                
                if content and not content.startswith("Error") and not content.startswith("Unsupported"):
                    uploaded_context = f"UPLOADED FILE DESCRIPTION: {file_description}\n\nFILE CONTENT:\n{content}"
                    st.session_state.uploaded_raw_text = content  # for textbook RAG indexing
                    st.success(f"✅ Successfully processed {uploaded_file.name}")
                    
                    if st.checkbox("Show uploaded content preview"):
                        st.markdown(f"**File Description:** {file_description}")
                        
                        word_count = len(content.split())
                        char_count = len(content)
                        st.caption(f"Processed: {word_count} words, {char_count} characters")
                        
                        preview_length = 1000
                        preview_content = content[:preview_length] + "..." if len(content) > preview_length else content
                        st.text_area("Content preview:", value=preview_content, height=200, disabled=True)
                else:
                    st.error(f"❌ {content}")
            except Exception as e:
                st.error(f"Error processing file: {e}")
                st.info("Try a different file format or check the file isn't corrupted")
        elif uploaded_file:
            st.warning("⚠️ Please provide a description of the uploaded file to proceed.")
    
    return file_description, uploaded_context

def validate_and_show_errors(fields: Dict[str, Any], tab_name: str, 
                           additional_validations: List[Tuple[bool, str]] = None) -> bool:
    """Enhanced validation with better error messaging."""
    from utils import validate_required_fields
    
    is_valid, errors = validate_required_fields(fields, tab_name)
    
    if additional_validations:
        for validation_result, error_message in additional_validations:
            if not validation_result:
                errors.append(f"• {error_message}")
                is_valid = False
    
    if is_valid:
        st.success("✅ All required fields completed")
    else:
        error_count = len(errors)
        st.error(f"❌ {error_count} field(s) missing/invalid")
        
        if errors:
            st.error(f"**{tab_name} Validation Errors:**\n" + "\n".join(errors))
            
            if "api_key" in str(errors).lower():
                st.info("💡 **Tip:** API keys are found in your OpenAI and Serper dashboards")
            if "slo" in str(errors).lower():
                st.info("💡 **Tip:** Select at least one program-specific SLO to proceed")
            if "description" in str(errors).lower():
                st.info("💡 **Tip:** File descriptions help the AI understand how to use your content")
    
    return is_valid

def render_generation_button(button_text: str, is_valid: bool, generation_function, 
                           *args, **kwargs) -> bool:
    """Render generation button with simple synchronous handling."""
    button_col, status_col = st.columns([2, 1])
    
    with button_col:
        button_clicked = st.button(button_text, type="primary", disabled=not is_valid, use_container_width=True)
    
    with status_col:
        if not is_valid:
            st.warning("⚠️ Complete required fields")
    
    if button_clicked and is_valid:
        try:
            st.info("🤖 Starting AI generation...")
            
            generation_function()
            
            st.success("✅ Generation completed successfully!")
            return True
                
        except Exception as e:
            st.error(f"❌ Generation failed: {str(e)}")
            
            error_msg = str(e).lower()
            if "serper" in error_msg:
                st.warning("🔍 **Serper API Issue:** Check your API key and try again")
                st.info("Get a free key at: https://serper.dev")
            elif "openai" in error_msg or "api" in error_msg:
                st.warning("🔑 **OpenAI API Issue:** Check your API key and try again")
            elif "timeout" in error_msg:
                st.warning("⏱️ **Timeout:** Try again with a simpler topic or different model")
            else:
                st.info("💡 **Suggestions:** Try different settings, simpler content, or switch AI models")
            
            return False
    
    return False
