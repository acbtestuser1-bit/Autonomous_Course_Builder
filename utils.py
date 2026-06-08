"""
Utility Functions - Fixed with JSON-based topic extraction
"""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple
import docx
import reportlab

# Check for optional dependencies
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

try:
    import docx2txt
    DOCX2TXT_AVAILABLE = True
except ImportError:
    DOCX2TXT_AVAILABLE = False

logger = logging.getLogger(__name__)

# ============= Topic Extraction - FIXED with JSON parsing =============

def extract_syllabus_topics(syllabus_content: str, total_weeks: int, sessions_per_week: int = 2) -> List[Dict[str, Any]]:
    """
    FIXED: Extract topics using structured metadata from syllabus generator.
    
    Args:
        syllabus_content: Generated syllabus with schedule_metadata
        total_weeks: Total number of weeks in the course
        sessions_per_week: Number of sessions per week
        
    Returns:
        List of dictionaries with week numbers and topics for each session
    """
    logger.debug(f"Extracting topics from syllabus: {total_weeks} weeks, {sessions_per_week} sessions/week")
    
    # Check if this is a GeneratedContent object with schedule_metadata
    if hasattr(syllabus_content, 'schedule_metadata'):
        logger.debug("Found structured schedule metadata")
        return _extract_from_metadata(syllabus_content.schedule_metadata, total_weeks, sessions_per_week)
    
    # Fallback: try to parse from text content
    logger.debug("No metadata found, attempting text parsing")
    parsed_topics = _parse_schedule_from_text(syllabus_content, total_weeks, sessions_per_week)
    
    if parsed_topics:
        logger.debug(f"Successfully parsed {len(parsed_topics)} topics from text")
        return parsed_topics
    
    # Final fallback: generate structured topics
    logger.debug("Text parsing failed, generating fallback topics")
    return _generate_fallback_topics(total_weeks, sessions_per_week)

def _extract_from_metadata(schedule_metadata: List[Dict], total_weeks: int, sessions_per_week: int) -> List[Dict[str, Any]]:
    """Extract topics from structured schedule metadata."""
    
    topics = []
    
    for week_data in schedule_metadata:
        week_num = week_data.get('week', 0)
        if week_num <= total_weeks:
            sessions = week_data.get('sessions', [])
            
            for session_data in sessions:
                session_id = session_data.get('session', '')
                topic = session_data.get('topic', '')
                
                if session_id and topic:
                    # Parse session format "1.1" -> week=1, module=1
                    try:
                        week_part, module_part = session_id.split('.')
                        week = int(week_part)
                        module = int(module_part)
                        
                        topics.append({
                            "week": week,
                            "module": module,
                            "topic": topic,
                            "session": session_id
                        })
                        
                    except (ValueError, IndexError):
                        logger.warning(f"Invalid session format: {session_id}")
                        continue
    
    # Sort by week and module
    topics = sorted(topics, key=lambda x: (x["week"], x["module"]))
    logger.debug(f"Extracted {len(topics)} topics from metadata")
    
    return topics[:total_weeks * sessions_per_week]

def _parse_schedule_from_text(syllabus_content: str, total_weeks: int, sessions_per_week: int) -> List[Dict[str, Any]]:
    """Parse topics from syllabus text content as fallback."""
    
    topics = []
    
    # Look for session patterns like "Session 1.1:" or "Week 1, Session 1:"
    session_patterns = [
        r"session\s+(\d+)\.(\d+)[\s:]+([^\n\r]+)",  # "Session 1.1: Topic"
        r"week\s+(\d+),?\s+session\s+(\d+)[\s:]+([^\n\r]+)",  # "Week 1, Session 1: Topic"
        r"(\d+)\.(\d+)[\s:]+([^\n\r]{10,})"  # "1.1: Topic"
    ]
    
    for pattern in session_patterns:
        matches = re.findall(pattern, syllabus_content, re.IGNORECASE)
        for match in matches:
            try:
                if len(match) == 3:
                    week = int(match[0])
                    module = int(match[1])
                    topic = clean_topic_text(match[2])
                    
                    if week <= total_weeks and module <= sessions_per_week and len(topic) > 5:
                        topics.append({
                            "week": week,
                            "module": module,
                            "topic": topic,
                            "session": f"{week}.{module}"
                        })
                        
            except (ValueError, IndexError):
                continue
    
    if topics:
        topics = sorted(topics, key=lambda x: (x["week"], x["module"]))
        return topics[:total_weeks * sessions_per_week]
    
    return []

def _generate_fallback_topics(total_weeks: int, sessions_per_week: int) -> List[Dict[str, Any]]:
    """Generate fallback topics when parsing fails."""
    
    logger.debug("Generating fallback topics")
    
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
    
    topics = []
    
    for week in range(1, total_weeks + 1):
        week_theme = base_topics[min(week-1, len(base_topics)-1)]
        
        # Generate sessions for this week
        for session_num in range(1, sessions_per_week + 1):
            if sessions_per_week == 1:
                session_topic = week_theme
            elif sessions_per_week == 2:
                session_topic = f"{week_theme} - {'Introduction' if session_num == 1 else 'Application'}"
            elif sessions_per_week == 3:
                session_labels = ["Introduction", "Analysis", "Practice"]
                session_topic = f"{week_theme} - {session_labels[session_num-1]}"
            else:
                session_topic = f"{week_theme} - Part {session_num}"
            
            topics.append({
                "week": week,
                "module": session_num,
                "topic": session_topic,
                "session": f"{week}.{session_num}"
            })
    
    logger.debug(f"Generated {len(topics)} fallback topics")
    return topics

def clean_topic_text(topic: str) -> str:
    """Clean and normalize topic text."""
    # Remove common prefixes and suffixes
    topic = re.sub(r'^(topic|lecture|class|session|module|week|unit)\s*:?\s*', '', topic, flags=re.IGNORECASE)
    topic = re.sub(r'\s*(reading|assignment|due|quiz|exam|test)\s*,', '', topic, flags=re.IGNORECASE)
    
    # Clean up punctuation and whitespace
    topic = topic.strip().rstrip('.').rstrip(',').rstrip(';')
    topic = re.sub(r'\s+', ' ', topic)
    
    # Remove parenthetical content
    topic = re.sub(r'\([^)]*\)', '', topic).strip()
    
    # Capitalize appropriately
    if len(topic) > 0:
        topic = topic[0].upper() + topic[1:]
    
    return topic

# ============= Validation =============

def validate_required_fields(fields: Dict[str, Any], tab_name: str) -> Tuple[bool, List[str]]:
    """Validate required fields with detailed error messages."""
    errors = []
    
    for field_name, field_value in fields.items():
        if not field_value or (isinstance(field_value, list) and len(field_value) == 0):
            errors.append(f"• {field_name.replace('_', ' ').title()} is required")
        elif isinstance(field_value, str) and not field_value.strip():
            errors.append(f"• {field_name.replace('_', ' ').title()} cannot be empty")
    
    return len(errors) == 0, errors

# ============= Content Formatting =============

def format_slos_for_prompt(selected_slos: List[Dict], custom_slos: List) -> str:
    """Format Student Learning Outcomes for AI prompt inclusion."""
    formatted = []
    
    # Format program-specific SLOs
    if selected_slos:
        formatted.append("**Program-Specific Learning Outcomes:**")
        for slo in selected_slos:
            formatted.append(f"- {slo.get('code', 'N/A')}: {slo.get('description', 'No description')}")
    
    # Format custom SLOs
    if custom_slos:
        formatted.append("\n**Custom Learning Outcomes:**")
        for custom_slo in custom_slos:
            formatted.append(f"- {custom_slo.title}: {custom_slo.content}")
    
    if not formatted:
        return "No specific learning outcomes defined - please ensure appropriate learning objectives are included."
    
    formatted.append("\n**Integration Requirement:** All course content must clearly demonstrate how it helps students achieve these learning outcomes.")
    
    return "\n".join(formatted)

def format_slos_for_content(selected_slos: List[Dict], custom_slos: List, course_name: str = "") -> str:
    """Format Student Learning Outcomes for inclusion in generated content."""
    formatted = []
    
    # Format program-specific SLOs
    if selected_slos:
        formatted.append("## Student Learning Outcomes")
        formatted.append("\nUpon successful completion of this course, students will be able to:\n")
        for i, slo in enumerate(selected_slos, 1):
            formatted.append(f"{i}. **{slo.get('code', 'N/A')}**: {slo.get('description', 'No description')}")
    
    # Format custom SLOs
    if custom_slos:
        if not selected_slos:
            formatted.append("## Student Learning Outcomes")
            formatted.append("\nUpon successful completion of this course, students will be able to:\n")
        
        start_num = len(selected_slos) + 1 if selected_slos else 1
        for i, custom_slo in enumerate(custom_slos, start_num):
            formatted.append(f"{i}. **{custom_slo.title}**: {custom_slo.content}")
    
    if not formatted:
        return "\n## Student Learning Outcomes\n\nLearning outcomes will be defined based on course requirements.\n"
    
    return "\n".join(formatted) + "\n"

# ============= File Processing =============

def process_uploaded_file(uploaded_file) -> str:
    """Extract text content from uploaded files."""
    try:
        file_extension = uploaded_file.name.split('.')[-1].lower()
        
        if file_extension == 'pdf':
            # Prefer pdfplumber (better layout/multi-column handling), fall back to PyPDF2.
            if PDFPLUMBER_AVAILABLE:
                try:
                    text_content = ""
                    with pdfplumber.open(uploaded_file) as pdf:
                        for page in pdf.pages:
                            text_content += (page.extract_text() or "") + "\n"
                    if text_content.strip():
                        return text_content
                    logger.warning("pdfplumber extracted no text; trying PyPDF2")
                except Exception as e:
                    logger.warning(f"pdfplumber failed ({e}); falling back to PyPDF2")
                # pdfplumber consumes the stream — reset before PyPDF2 retry
                try:
                    uploaded_file.seek(0)
                except Exception:
                    pass

            if not PDF_AVAILABLE:
                return "PDF processing unavailable. Please install pdfplumber or PyPDF2."

            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            text_content = ""
            for page in pdf_reader.pages:
                text_content += (page.extract_text() or "") + "\n"
            return text_content
            
        elif file_extension == 'docx':
            if not DOCX2TXT_AVAILABLE:
                return "DOCX processing unavailable. Please install docx2txt: pip install docx2txt"
            
            text_content = docx2txt.process(uploaded_file)
            return text_content
            
        elif file_extension in ['txt', 'md']:
            text_content = str(uploaded_file.read(), "utf-8")
            return text_content
            
        else:
            return f"Unsupported file type: {file_extension}. Please upload PDF, DOCX, TXT, or MD files."
            
    except Exception as e:
        logger.error(f"Error processing uploaded file: {e}")
        return f"Error processing file: {str(e)}"

# ============= Dependency Checking =============

def check_dependencies() -> Dict[str, bool]:
    """Check which optional dependencies are available."""
    dependencies = {
        'pdf_processing': PDF_AVAILABLE,
        'docx_processing': DOCX2TXT_AVAILABLE,
    }
    
    # Check document generation dependencies
    try:
        
        dependencies['pdf_generation'] = True
    except ImportError:
        dependencies['pdf_generation'] = False
    
    try:
        
        dependencies['word_generation'] = True
    except ImportError:
        dependencies['word_generation'] = False
    
    return dependencies

def get_missing_dependencies() -> List[str]:
    """Get list of missing dependency descriptions."""
    deps = check_dependencies()
    missing = []
    
    if not deps['pdf_processing']:
        missing.append("PyPDF2 (PDF file reading) - pip install PyPDF2")
    if not deps['docx_processing']:
        missing.append("docx2txt (DOCX file reading) - pip install docx2txt")
    if not deps['pdf_generation']:
        missing.append("ReportLab (PDF generation) - pip install reportlab")
    if not deps['word_generation']:
        missing.append("python-docx (Word generation) - pip install python-docx")
    
    return missing
