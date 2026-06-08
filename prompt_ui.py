"""
Prompt Editor UI Components
"""

import streamlit as st
from datetime import datetime
import logging

from prompt_manager import get_prompt_manager
from prompts import get_prompt_categories

logger = logging.getLogger(__name__)

def render_prompt_editor(category: str, tab_title: str):
    """
    Render prompt editor section for a specific category.
    
    Args:
        category: Prompt category (syllabus, lecture, assignment, rubric)
        tab_title: Display title for the tab
    """
    pm = get_prompt_manager()
    
    with st.expander("🔧 Advanced: Customize Prompts", expanded=False):
        st.markdown(f"**Customize AI prompts for {tab_title}**")
        st.caption("Edit prompts to change how content is generated. All variables in {{curly braces}} will be filled automatically.")
        
        # Get available prompts for this category
        available_prompts = pm.get_available_prompts(category)
        
        if not available_prompts:
            st.info(f"No prompts available for {category}")
            return
        
        # Show summary
        custom_count = pm.get_custom_count(category)
        if custom_count > 0:
            st.info(f"✏️ {custom_count} custom prompt(s) active in this section")
        
        # Prompt selection
        prompt_names = list(available_prompts.keys())
        friendly_names = {
            'schedule_metadata': 'Course Schedule Generation',
            'header': 'Syllabus Header',
            'introduction': 'Course Introduction',
            'learning_outcomes': 'Learning Outcomes',
            'course_overview': 'Course Overview',
            'course_format': 'Course Format',
            'materials': 'Required Materials',
            'assessment': 'Assessment Plan',
            'administrative': 'Administrative Policies',
            'schedule': 'Detailed Schedule',
            'objectives': 'Lecture Objectives',
            'main_content': 'Main Content',
            'activities': 'Interactive Activities',
            'assignment_content': 'Assignment Details',
            'rubric_criteria': 'Rubric Criteria',
            'rubric_main': 'Main Rubric'
        }
        
        selected_prompt = st.selectbox(
            "Select Prompt to Edit",
            options=prompt_names,
            format_func=lambda x: friendly_names.get(x, x.replace('_', ' ').title())
        )
        
        if selected_prompt:
            prompt_info = available_prompts[selected_prompt]
            
            # Show status
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                if prompt_info['is_custom']:
                    st.success("✏️ Custom")
                else:
                    st.info("📝 Default")
            
            with col2:
                if st.button("👁️ Preview", key=f"preview_{category}_{selected_prompt}"):
                    st.session_state[f'show_preview_{category}_{selected_prompt}'] = True
            
            with col3:
                if prompt_info['is_custom']:
                    if st.button("🔄 Reset", key=f"reset_{category}_{selected_prompt}"):
                        pm.reset_prompt(category, selected_prompt)
                        st.success("Reset to default!")
                        st.rerun()
            
            # Preview modal
            if st.session_state.get(f'show_preview_{category}_{selected_prompt}', False):
                with st.container():
                    st.markdown("**Prompt Preview:**")
                    template = pm.get_prompt_template(category, selected_prompt)
                    st.code(template, language="markdown")
                    if st.button("Close Preview", key=f"close_preview_{category}_{selected_prompt}"):
                        st.session_state[f'show_preview_{category}_{selected_prompt}'] = False
                        st.rerun()
            
            # Editor
            st.markdown("---")
            st.markdown("**Edit Prompt:**")
            
            current_template = pm.get_prompt_template(category, selected_prompt)
            
            edited_prompt = st.text_area(
                "Prompt Content",
                value=current_template,
                height=300,
                key=f"edit_{category}_{selected_prompt}",
                help="Variables in {curly braces} will be replaced with actual values during generation"
            )
            
            # Save button
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("💾 Save Changes", key=f"save_{category}_{selected_prompt}", type="primary"):
                    if edited_prompt.strip() != current_template:
                        success = pm.set_custom_prompt(category, selected_prompt, edited_prompt)
                        if success:
                            st.success("Prompt saved!")
                            st.rerun()
                        else:
                            st.error("Failed to save prompt. Check format.")
                    else:
                        st.info("No changes to save")
            
            with col2:
                st.caption("Changes apply immediately to new generations")
        
        # Bulk actions
        st.markdown("---")
        st.markdown("**Bulk Actions**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if custom_count > 0:
                if st.button(f"🔄 Reset All {tab_title} Prompts", key=f"reset_all_{category}"):
                    if category in st.session_state.custom_prompts:
                        st.session_state.custom_prompts[category] = {}
                        st.success(f"Reset all {tab_title} prompts to defaults!")
                        st.rerun()
        
        with col2:
            # Versioning in the main prompt management section
            pass


def render_prompt_version_manager():
    """Render prompt versioning UI in sidebar."""
    pm = get_prompt_manager()
    
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 📚 Prompt Versions")
        
        custom_count = pm.get_custom_count()
        
        if custom_count == 0:
            st.caption("No custom prompts yet")
            return
        
        st.caption(f"{custom_count} custom prompt(s) active")
        
        # Save current as version
        with st.expander("💾 Save Current Set"):
            version_name = st.text_input(
                "Version Name",
                placeholder=f"v{len(pm.get_versions()) + 1}",
                key="new_version_name"
            )
            
            if st.button("Save Version", key="save_version"):
                if version_name.strip():
                    success = pm.save_current_as_version(version_name.strip())
                    if success:
                        st.success(f"Saved as '{version_name}'!")
                        st.rerun()
                    else:
                        st.error("Failed to save version")
                else:
                    st.warning("Please enter a version name")
        
        # Load versions
        versions = pm.get_versions()
        
        if versions:
            with st.expander(f"📖 Load Version ({len(versions)})"):
                for v in versions:
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.caption(f"**{v['name']}**")
                        st.caption(f"{v['prompt_count']} prompts • {v['timestamp'][:10]}")
                    
                    with col2:
                        if st.button("Load", key=f"load_v_{v['index']}"):
                            pm.load_version(v['index'])
                            st.success(f"Loaded '{v['name']}'!")
                            st.rerun()
                    
                    with col3:
                        if st.button("🗑️", key=f"del_v_{v['index']}"):
                            pm.delete_version(v['index'])
                            st.success("Deleted!")
                            st.rerun()
        
        # Export/Import
        with st.expander("📤 Export/Import"):
            # Export
            if st.button("Export All Prompts"):
                export_data = pm.export_prompts()
                st.download_button(
                    label="Download JSON",
                    data=export_data,
                    file_name=f"prompts_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            
            # Import
            uploaded_file = st.file_uploader("Import Prompts", type=['json'], key="import_prompts")
            if uploaded_file is not None:
                try:
                    import_data = uploaded_file.read().decode('utf-8')
                    success = pm.import_prompts(import_data)
                    if success:
                        st.success("Prompts imported!")
                        st.rerun()
                    else:
                        st.error("Failed to import")
                except Exception as e:
                    st.error(f"Import error: {e}")
        
        # Reset all
        if custom_count > 0:
            st.markdown("---")
            if st.button("🔄 Reset All Prompts", key="reset_all_prompts_global"):
                pm.reset_all_prompts()
                st.success("All prompts reset to defaults!")
                st.rerun()


def render_prompt_help():
    """Render help section for prompt editing."""
    with st.expander("ℹ️ Prompt Editing Guide"):
        st.markdown("""
        ### How to Edit Prompts
        
        **Variables** (automatically filled):
        - `{course_name}` - Course name
        - `{program_type}` - Program type (Undergraduate, MBA, etc.)
        - `{weeks}` - Number of weeks
        - `{teaching_style}` - Teaching methodology
        - And many more...
        
        **Tips**:
        - Keep variable names unchanged in {curly braces}
        - Add your own instructions before/after existing content
        - Be specific about what you want generated
        - Test with "Generate" to see results
        
        **Safety**:
        - Always keep required variables
        - Use "Reset" to restore defaults
        - Save versions before major changes
        
        **Examples of Good Edits**:
        - "Focus more on practical applications..."
        - "Use industry examples from finance sector..."
        - "Make tone more formal/casual..."
        - "Include more step-by-step instructions..."
        """)