"""
Prompt Manager - Handles custom prompt storage, versioning, and retrieval
"""

import streamlit as st
from datetime import datetime
from typing import Dict, Optional, Tuple
import json
import logging

from prompts import (
    get_default_prompt,
    get_all_prompts_for_category,
    get_prompt_categories,
    validate_prompt
)

logger = logging.getLogger(__name__)

class PromptManager:
    """Manages custom and default prompts with versioning support."""
    
    def __init__(self):
        """Initialize prompt manager."""
        self._ensure_session_state()
    
    def _ensure_session_state(self):
        """Ensure session state has required prompt management keys."""
        if 'custom_prompts' not in st.session_state:
            st.session_state.custom_prompts = {}  # {category: {prompt_name: custom_text}}
        
        if 'prompt_versions' not in st.session_state:
            st.session_state.prompt_versions = []  # List of saved versions
        
        if 'active_prompt_version' not in st.session_state:
            st.session_state.active_prompt_version = None
    
    def get_prompt(self, category: str, prompt_name: str, **kwargs) -> str:
        """
        Get prompt (custom if exists, otherwise default) with variables filled in.
        
        Args:
            category: Category (syllabus, lecture, assignment, rubric)
            prompt_name: Name of the specific prompt
            **kwargs: Variables to fill in the prompt template
        
        Returns:
            Formatted prompt string
        """
        try:
            # Check for custom prompt first
            if (category in st.session_state.custom_prompts and 
                prompt_name in st.session_state.custom_prompts[category]):
                template = st.session_state.custom_prompts[category][prompt_name]
                logger.debug(f"Using custom prompt: {category}.{prompt_name}")
            else:
                # Fall back to default
                template = get_default_prompt(category, prompt_name)
                logger.debug(f"Using default prompt: {category}.{prompt_name}")
            
            # Fill in variables
            try:
                formatted = template.format(**kwargs)
                return formatted
            except KeyError as e:
                logger.warning(f"Missing variable {e} in prompt {category}.{prompt_name}, returning template")
                return template  # Return template if variables missing
                
        except Exception as e:
            logger.error(f"Error getting prompt {category}.{prompt_name}: {e}")
            # Always have a fallback
            return get_default_prompt(category, prompt_name)
    
    def set_custom_prompt(self, category: str, prompt_name: str, custom_text: str) -> bool:
        """
        Set a custom prompt.
        
        Returns:
            True if set successfully, False otherwise
        """
        try:
            # Validate
            is_valid, warnings = validate_prompt(custom_text)
            if not is_valid:
                logger.error(f"Invalid prompt: {warnings}")
                return False
            
            # Log warnings but allow
            for warning in warnings:
                logger.warning(warning)
            
            # Initialize category if needed
            if category not in st.session_state.custom_prompts:
                st.session_state.custom_prompts[category] = {}
            
            # Set custom prompt
            st.session_state.custom_prompts[category][prompt_name] = custom_text
            logger.info(f"Set custom prompt: {category}.{prompt_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting custom prompt: {e}")
            return False
    
    def reset_prompt(self, category: str, prompt_name: str):
        """Reset a prompt to default."""
        try:
            if (category in st.session_state.custom_prompts and 
                prompt_name in st.session_state.custom_prompts[category]):
                del st.session_state.custom_prompts[category][prompt_name]
                logger.info(f"Reset prompt to default: {category}.{prompt_name}")
        except Exception as e:
            logger.error(f"Error resetting prompt: {e}")
    
    def reset_all_prompts(self):
        """Reset all prompts to defaults."""
        st.session_state.custom_prompts = {}
        logger.info("Reset all prompts to defaults")
    
    def is_custom(self, category: str, prompt_name: str) -> bool:
        """Check if a prompt has been customized."""
        return (category in st.session_state.custom_prompts and 
                prompt_name in st.session_state.custom_prompts[category])
    
    def get_custom_count(self, category: str = None) -> int:
        """Get count of custom prompts (optionally for a specific category)."""
        if category:
            return len(st.session_state.custom_prompts.get(category, {}))
        else:
            return sum(len(prompts) for prompts in st.session_state.custom_prompts.values())
    
    def save_current_as_version(self, version_name: str) -> bool:
        """
        Save current custom prompts as a named version.
        
        Args:
            version_name: Name for this version
        
        Returns:
            True if saved successfully
        """
        try:
            version = {
                'name': version_name,
                'timestamp': datetime.now().isoformat(),
                'prompts': json.loads(json.dumps(st.session_state.custom_prompts))  # Deep copy
            }
            
            st.session_state.prompt_versions.append(version)
            logger.info(f"Saved prompt version: {version_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving prompt version: {e}")
            return False
    
    def load_version(self, version_index: int) -> bool:
        """
        Load a saved prompt version.
        
        Args:
            version_index: Index in prompt_versions list
        
        Returns:
            True if loaded successfully
        """
        try:
            if 0 <= version_index < len(st.session_state.prompt_versions):
                version = st.session_state.prompt_versions[version_index]
                st.session_state.custom_prompts = json.loads(json.dumps(version['prompts']))  # Deep copy
                st.session_state.active_prompt_version = version_index
                logger.info(f"Loaded prompt version: {version['name']}")
                return True
            else:
                logger.error(f"Invalid version index: {version_index}")
                return False
                
        except Exception as e:
            logger.error(f"Error loading prompt version: {e}")
            return False
    
    def delete_version(self, version_index: int) -> bool:
        """Delete a saved version."""
        try:
            if 0 <= version_index < len(st.session_state.prompt_versions):
                version_name = st.session_state.prompt_versions[version_index]['name']
                del st.session_state.prompt_versions[version_index]
                
                # Clear active version if it was deleted
                if st.session_state.active_prompt_version == version_index:
                    st.session_state.active_prompt_version = None
                
                logger.info(f"Deleted prompt version: {version_name}")
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"Error deleting prompt version: {e}")
            return False
    
    def get_versions(self) -> list:
        """Get list of saved versions with metadata."""
        return [
            {
                'index': i,
                'name': v['name'],
                'timestamp': v['timestamp'],
                'prompt_count': sum(len(prompts) for prompts in v['prompts'].values())
            }
            for i, v in enumerate(st.session_state.prompt_versions)
        ]
    
    def export_prompts(self) -> str:
        """Export current custom prompts as JSON string."""
        try:
            export_data = {
                'exported_at': datetime.now().isoformat(),
                'custom_prompts': st.session_state.custom_prompts,
                'versions': st.session_state.prompt_versions
            }
            return json.dumps(export_data, indent=2)
        except Exception as e:
            logger.error(f"Error exporting prompts: {e}")
            return "{}"
    
    def import_prompts(self, json_data: str) -> bool:
        """
        Import custom prompts from JSON string.
        
        Args:
            json_data: JSON string with exported prompt data
        
        Returns:
            True if imported successfully
        """
        try:
            data = json.loads(json_data)
            
            if 'custom_prompts' in data:
                st.session_state.custom_prompts = data['custom_prompts']
            
            if 'versions' in data:
                st.session_state.prompt_versions = data['versions']
            
            logger.info("Imported prompts successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error importing prompts: {e}")
            return False
    
    def get_prompt_template(self, category: str, prompt_name: str) -> str:
        """Get the template (not formatted) for editing."""
        if self.is_custom(category, prompt_name):
            return st.session_state.custom_prompts[category][prompt_name]
        else:
            return get_default_prompt(category, prompt_name)
    
    def get_available_prompts(self, category: str) -> Dict[str, dict]:
        """
        Get all available prompts for a category with metadata.
        
        Returns:
            Dict of {prompt_name: {is_custom: bool, preview: str}}
        """
        try:
            defaults = get_all_prompts_for_category(category)
            result = {}
            
            for prompt_name in defaults.keys():
                is_custom = self.is_custom(category, prompt_name)
                template = self.get_prompt_template(category, prompt_name)
                
                # Get first 100 chars as preview
                preview = template[:100].replace('\n', ' ').strip()
                if len(template) > 100:
                    preview += "..."
                
                result[prompt_name] = {
                    'is_custom': is_custom,
                    'preview': preview,
                    'length': len(template)
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting available prompts: {e}")
            return {}


# Global instance
_prompt_manager = None

def get_prompt_manager() -> PromptManager:
    """Get global prompt manager instance.

    The instance is a module-level singleton that outlives individual Streamlit
    sessions, but session_state is per-session — so re-ensure the required keys
    on every fetch (not just on first construction), otherwise a fresh session
    raises "st.session_state has no attribute custom_prompts".
    """
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptManager()
    else:
        _prompt_manager._ensure_session_state()
    return _prompt_manager