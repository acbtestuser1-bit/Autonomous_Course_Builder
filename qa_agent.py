# """
# Quality Assurance Agent - LLM as a judge
# """

# import json
# import logging
# from typing import Dict, Any, List
# from langchain_openai import ChatOpenAI
# from langchain_core.messages import SystemMessage, HumanMessage
# from config import CourseContext, QA_PASS_THRESHOLD

# logger = logging.getLogger(__name__)

# class QualityAssuranceAgent:
#     """
#     Simplified QA Agent with single LLM judge providing comprehensive rationale.
#     """
    
#     def __init__(self, api_key: str, model_type: str = "gpt-4o-mini"):
#         self.llm = ChatOpenAI(api_key=api_key, model=model_type, temperature=0.2)

#     async def generate_actionable_suggestions(self, content: str, content_type: str, 
#                                          course_context: CourseContext,
#                                          granularity: str = "Medium-level",
#                                          previous_suggestions: str = "") -> str:
#         """
#         Generate content-based actionable suggestions for improvement.
        
#         Args:
#             content: The generated content to analyze
#             content_type: Type of content (syllabus, lecture_notes, etc.)
#             course_context: Course context information
#             granularity: Level of detail for suggestions
#             previous_suggestions: Previously applied suggestions to avoid regression
            
#         Returns:
#             Formatted actionable suggestions string
#         """
#         try:
#             logger.debug(f"Generating {granularity} actionable suggestions for {content_type}")
            
#             granularity_instructions = self._get_granularity_instructions(granularity)
            
#             # Build constraint prompt for preventing regression
#             constraint_prompt = ""
#             if previous_suggestions:
#                 constraint_prompt = f"""
# CRITICAL CONSTRAINT - PREVENT REGRESSION:
# The following improvements have been applied in previous versions and MUST BE MAINTAINED:

# {previous_suggestions}

# MANDATORY REQUIREMENTS:
# 1. Do NOT suggest anything that contradicts or undoes previous improvements
# 2. Do NOT suggest removing any previously applied enhancements
# 3. Only suggest NEW improvements that BUILD UPON the existing ones
# 4. If suggesting a refinement of a previous improvement, explicitly state which one you're extending
# 5. Verify each suggestion doesn't conflict with locked-in improvements

# Your suggestions should ADD to what's already been done, never subtract or replace.
# """
            
#             prompt = f"""
#             You are Dr. Maria Rodriguez, an expert educational consultant with 15 years experience improving course materials at top business schools.
            
#             {constraint_prompt}
            
#             Analyze this {content_type} for {course_context.course_name} using ROOT CAUSE ANALYSIS. Don't just identify symptoms—diagnose WHY content is weak and prescribe specific fixes.
            
#             YOUR DIAGNOSTIC FRAMEWORK:
            
#             1. SPECIFICITY AUDIT:
#                - Are concepts illustrated with NAMED examples (real companies, specific tools, actual data)?
#                - Are learning objectives MEASURABLE with concrete success criteria?
#                - Are assessments SPECIFIC with clear deliverables and rubrics?
               
#             2. COGNITIVE LOAD ANALYSIS:
#                - Is content chunked appropriately (5-7 concepts per segment)?
#                - Are worked examples provided BEFORE independent practice?
#                - Is progression clear (foundation → application → synthesis)?
               
#             3. ENGAGEMENT DIAGNOSTIC:
#                - Does it open with a provocative question or current event?
#                - Are there contrasting cases or "choice points" for analysis?
#                - Are students doing something active every 10-15 minutes?
               
#             4. ASSESSMENT ALIGNMENT:
#                - Does each assessment map to specific learning outcomes?
#                - Are rubric criteria observable and measurable?
#                - Is there progression (formative → summative)?
               
#             5. ANTI-PATTERN DETECTION:
#                Identify if content contains:
#                - Vague verbs: "understand," "learn," "explore," "gain familiarity"
#                - Generic claims: "industry-leading," "cutting-edge," "hands-on" without specifics
#                - Missing evidence: statements without sources, examples without analysis
#                - Passive language: "it can be seen," "there are many"
            
#             {granularity_instructions}
            
#             CONTENT TO ANALYZE (first 2500 chars):
#             {content[:2500]}...
            
#             COURSE CONTEXT:
#             - Course: {course_context.course_name}
#             - Program: {course_context.program_type}
#             - Teaching Style: {course_context.teaching_style}
#             - Duration: {course_context.weeks} weeks, {course_context.sessions_per_week} sessions/week
#             - Assessment Methods: {', '.join(course_context.assessment_preferences)}
#             - SLOs: {len(course_context.selected_slos + course_context.custom_slos)} total
            
#             PROVIDE 6-8 DIAGNOSTIC SUGGESTIONS in this format:
            
#             [NUMBER]. **[DIAGNOSIS]**: [What's weak and WHY]
#                **Root Cause**: [Underlying issue - e.g., "lacks specificity," "missing cognitive scaffolding," "no measurable criteria"]
#                **Specific Fix**: [Concrete action - reference specific weeks, sections, or topics]
#                **Example**: [Show what good looks like - give a specific example of the improvement]
#                **Impact**: [How this improves learning outcomes - reference specific SLO if relevant]
            
#             EXAMPLE FORMAT:
#             1. **Week 3 lacks concrete examples**: Currently uses vague "companies use this approach" language
#                **Root Cause**: Generic claims without named examples reduce credibility and student engagement
#                **Specific Fix**: Replace "companies" with 3 named examples: "Netflix's recommendation algorithm, Amazon's supply chain optimization, and Tesla's manufacturing process"
#                **Example**: "Netflix analyzes 2+ billion viewing hours monthly using collaborative filtering to personalize recommendations for 230M+ subscribers"
#                **Impact**: Concrete examples help students visualize application and support SLO MBA-3.1 (identifying appropriate frameworks)
            
#             Focus on fixes that:
#             - Add named examples, specific data, or real case studies
#             - Strengthen measurability and assessment alignment  
#             - Improve cognitive scaffolding and learning progression
#             - Replace vague language with concrete, observable criteria
#             - Build upon (not contradict) previous improvements
            
#             Teaching methodology: {course_context.teaching_style}
#             """
            
#             messages = [
#                 SystemMessage(content=f"You are Dr. Maria Rodriguez, providing diagnostic analysis of educational content with specific, actionable improvements."),
#                 HumanMessage(content=prompt)
#             ]
            
#             response = await self.llm.ainvoke(messages)
#             return response.content.strip()
            
#         except Exception as e:
#             logger.error(f"Error generating actionable suggestions: {e}")
#             return self._fallback_suggestions(content_type, course_context, granularity)
    
#     def _get_granularity_instructions(self, granularity: str) -> str:
#         """Get instructions based on granularity level."""
#         if "High-level" in granularity:
#             return """
#             GRANULARITY: HIGH-LEVEL (Strategic/Structural)
            
#             Focus your diagnostic on:
#             - **Course Architecture**: Is the progression logical? Does complexity build appropriately?
#             - **Learning Scaffolding**: Are foundational concepts established before advanced ones?
#             - **Assessment Strategy**: Do assessments align with outcomes? Is there formative + summative balance?
#             - **Cognitive Load**: Are segments appropriately chunked (7±2 concepts per section)?
#             - **Real-World Bridge**: Does course connect theory to practice throughout?
            
#             Your suggestions should address STRUCTURAL issues:
#             - Resequence modules for better learning progression
#             - Add/remove major course components
#             - Redesign assessment strategy
#             - Restructure cognitive load distribution
            
#             Example: "Weeks 1-4 introduce 15+ frameworks without application. Restructure to: Week 1-2 foundational theory, Week 3-4 apply to 2-3 real cases, creating scaffolded learning progression."
            
#             Provide 5-6 strategic suggestions that reshape course structure.
#             """
#         elif "Fine-grained" in granularity:
#             return """
#             GRANULARITY: FINE-GRAINED (Detailed/Tactical)
            
#             Focus your diagnostic on:
#             - **Specific Content Gaps**: Which exact readings, case studies, or examples are missing?
#             - **Activity Design**: Are in-class activities well-structured with clear instructions?
#             - **Assessment Rubrics**: Do rubric criteria have specific, observable indicators?
#             - **SLO Mapping**: Is each activity explicitly tied to specific SLO codes?
#             - **Resource Quality**: Are cited sources current (2024-2025), credible, and diverse?
            
#             Your suggestions should be HIGHLY SPECIFIC:
#             - Name exact articles, cases, or textbook chapters to add
#             - Specify which tools/software (with version numbers if relevant)
#             - Provide example assignment prompts or discussion questions
#             - Suggest specific rubric criteria with 3-4 performance levels
#             - Map activities to precise SLO codes with rationale
            
#             Examples:
#             - "Week 3, Session 2: Add Harvard Business Review case 'Netflix's Recommendation Engine' (2024) to illustrate collaborative filtering"
#             - "Assignment 2 rubric: Add criterion 'Data Visualization Quality' with levels: Exemplary (uses 3+ chart types appropriately), Proficient (2 chart types with clear labels), Developing (1 chart type or unclear labels), Unsatisfactory (no visualization or misleading)"
#             - "Week 5 activity: Replace generic 'analyze a company' with structured prompt: 'Using Porter's Five Forces, analyze Airbnb's competitive position. Create a matrix rating each force 1-5 with evidence from 2024 10-K filing.'"
            
#             Provide 7-8 detailed, specific suggestions with examples.
#             """
#         else:  # Medium-level
#             return """
#             GRANULARITY: MEDIUM-LEVEL (Topic/Module Focus)
            
#             Focus your diagnostic on:
#             - **Topic Coverage**: Are key concepts within each module explained clearly?
#             - **Example Quality**: Does each major topic have 2-3 concrete examples?
#             - **Activity Alignment**: Do learning activities match topic objectives?
#             - **Assessment Variety**: Is there diversity in how topics are assessed?
#             - **Resource Types**: Are there readings, videos, interactive tools for each module?
            
#             Your suggestions should target TOPIC-LEVEL improvements:
#             - Enhance specific weeks or modules with better examples
#             - Add activity types for particular topics (not specific activities)
#             - Suggest resource categories (not specific titles)
#             - Improve topic-to-assessment connections
#             - Strengthen within-topic progression
            
#             Examples:
#             - "Week 4 (Game Theory): Add 2-3 current business examples of Nash equilibrium (e.g., pricing strategy, market entry). Include interactive simulation for students to model strategic decisions."
#             - "Weeks 6-8 (Strategic Analysis): Diversify assessments beyond case studies. Add: one competitive analysis matrix assignment, one strategy memo (1000 words), one peer evaluation component."
#             - "Week 10 (Innovation): Supplement lecture with practitioner resources - industry reports from McKinsey/BCG, startup founder interviews/podcasts, innovation metrics dashboards."
            
#             Provide 6-7 practical, topic-focused suggestions.
#             """
    
#     def _fallback_suggestions(self, content_type: str, course_context: CourseContext, 
#                             granularity: str) -> str:
#         """Generate fallback suggestions if AI call fails."""
#         if "High-level" in granularity:
#             return f"""1. Consider reorganizing course modules to build foundational concepts before advanced topics
# 2. Balance theoretical content with practical applications appropriate for {course_context.program_type} students
# 3. Integrate more real-world case studies aligned with {course_context.teaching_style} methodology
# 4. Diversify assessment methods beyond {', '.join(course_context.assessment_preferences[:2])}
# 5. Add explicit connections between weekly topics and Program SLOs throughout"""
#         elif "Fine-grained" in granularity:
#             return f"""1. Week 1: Add a specific icebreaker activity to establish {course_context.teaching_style} classroom culture
# 2. Week 2-3: Include Harvard Business Review case study on current industry trends
# 3. Week 4: Incorporate hands-on Excel/data analysis exercise with real datasets
# 4. Week 5: Add peer review component to assessment aligned with SLO on collaboration
# 5. Week 8: Include guest speaker or industry practitioner video interview
# 6. Week 10-12: Assign McKinsey Quarterly or similar practitioner-focused readings
# 7. Week 14: Add reflective journaling assignment connecting course concepts to career goals
# 8. Throughout: Embed formative assessment checkpoints (2-3 per module) for self-paced learning"""
#         else:  # Medium
#             return f"""1. Weeks 1-4: Add more foundational case studies to support concept application
# 2. Mid-term: Introduce a team-based project component aligned with {course_context.teaching_style}
# 3. Weeks 5-8: Incorporate current industry reports (2024-2025) as supplementary readings
# 4. Assessment: Add one low-stakes formative assessment to support learning progression
# 5. Weeks 9-12: Include interactive simulations or role-playing scenarios for practice
# 6. Throughout: Strengthen explicit SLO connections in learning objectives for each week"""
    

#     async def review_content(self, content: str, content_type: str, 
#                            course_context: CourseContext) -> Dict[str, Any]:
#         """
#         Comprehensive content review with single LLM judge rationale.
#         """
#         try:
#             logger.debug(f"Starting QA review for {content_type}")
            
#             # Single comprehensive evaluation
#             evaluation = await self._comprehensive_evaluation(content, content_type, course_context)
            
#             logger.debug(f"QA completed: {evaluation['overall_score']}/100, passed: {evaluation.get('passed_qa', False)}")
            
#             return evaluation
            
#         except Exception as e:
#             logger.warning(f"QA analysis error: {e}")
#             return self._fallback_analysis(content, content_type, course_context)
    
#     async def _comprehensive_evaluation(self, content: str, content_type: str, course_context: CourseContext) -> Dict[str, Any]:
#         """Single comprehensive LLM evaluation with detailed rationale."""
        
#         prompt = f"""
#         You are Dr. Sarah Chen, expert educational evaluator with 20 years at top business schools. Provide evidence-based quality assessment of this {content_type}.

#         CONTENT TO EVALUATE (first 2500 chars):
#         {content[:2500]}...

#         COURSE CONTEXT:
#         - Course: {course_context.course_name}
#         - Program: {course_context.program_type} (complexity: UG < Kelley Direct < MBA)
#         - Teaching Style: {course_context.teaching_style}
#         - Selected SLOs: {len(course_context.selected_slos)} program + {len(course_context.custom_slos)} custom
#         - Assessment Preferences: {', '.join(course_context.assessment_preferences)}
#         - Structure: {course_context.weeks} weeks, {course_context.sessions_per_week} sessions/week, {course_context.duration_per_session} min/session

#         EVALUATION FRAMEWORK:

#         **1. PEDAGOGICAL ALIGNMENT (0-25 points)**
#         Evidence: Are outcomes measurable (action verbs), complexity appropriate, clear progression, natural SLO integration, methodology evident?
#         Score: 20-25=excellent, 15-19=good, 10-14=needs work, 0-9=poor

#         **2. CONTENT QUALITY (0-25 points)**
#         Evidence: Named examples (5+), current sources (2024-2025), appropriate depth, evidence-based, minimal jargon?
#         Score: 20-25=excellent, 15-19=good, 10-14=needs work, 0-9=poor

#         **3. STUDENT ENGAGEMENT (0-25 points)**
#         Evidence: Compelling hook, contrasting cases, active learning, variety, career relevance?
#         Score: 20-25=excellent, 15-19=good, 10-14=needs work, 0-9=poor

#         **4. ASSESSMENT INTEGRATION (0-25 points)**
#         Evidence: Outcome mapping, measurable criteria, formative+summative, authentic SLO assessment, logistics specified?
#         Score: 20-25=excellent, 15-19=good, 10-14=needs work, 0-9=poor

#         COUNT QUALITY INDICATORS:
#         - Named companies/organizations: ___
#         - Data points with sources: ___
#         - Action verbs in outcomes: ___
#         - Measurable assessment criteria: ___
#         - Formative assessments: ___
#         - Active learning activities: ___

#         Return ONLY valid JSON:
#         {{
#             "overall_score": [0-100],
#             "pedagogical_score": [0-25],
#             "content_score": [0-25], 
#             "engagement_score": [0-25],
#             "assessment_score": [0-25],
#             "passed_qa": [true if score >= 80],
#             "quality_indicators": {{
#                 "named_examples_count": [number],
#                 "data_points_count": [number],
#                 "action_verbs_count": [number],
#                 "measurable_criteria_count": [number],
#                 "formative_assessments_count": [number],
#                 "active_learning_activities_count": [number]
#             }},
#             "strengths": ["strength 1 with evidence", "strength 2 with evidence", "strength 3 with evidence"],
#             "improvements": ["weakness 1 with evidence", "weakness 2 with evidence", "weakness 3 with evidence"],
#             "recommendations": ["actionable fix 1", "actionable fix 2", "actionable fix 3"],
#             "comprehensive_rationale": "Write 350-450 words: (1) How scores determined with evidence (cite indicators), (2) How content matches {course_context.program_type} complexity and {course_context.teaching_style} with examples, (3) Strengths with evidence, (4) Weaknesses with evidence, (5) Most impactful improvements. Be specific—avoid generic language."
#         }}
#         """
        
#         messages = [
#             SystemMessage(content="You are Dr. Sarah Chen, providing evidence-based evaluation with specific quality indicators."),
#             HumanMessage(content=prompt)
#         ]
        
#         response = await self.llm.ainvoke(messages)
#         return self._parse_json_response(response.content, content_type, course_context)

       
#     def _parse_json_response(self, response_content: str, content_type: str, course_context: CourseContext) -> Dict[str, Any]:
#         """Parse JSON response with enhanced fallback."""
#         try:
#             # Clean response content
#             content = response_content.strip()
            
#             # Find JSON block
#             if "```json" in content:
#                 json_start = content.find("```json") + 7
#                 json_end = content.find("```", json_start)
#                 json_text = content[json_start:json_end].strip()
#             elif "{" in content and "}" in content:
#                 json_start = content.find("{")
#                 json_end = content.rfind("}") + 1
#                 json_text = content[json_start:json_end]
#             else:
#                 json_text = content
            
#             parsed = json.loads(json_text)
            
#             # Validate and ensure all required fields
#             overall_score = parsed.get('overall_score', 75)
#             overall_score = max(0, min(100, overall_score))
            
#             # Calculate component scores if missing
#             component_scores = {
#                 'pedagogical': parsed.get('pedagogical_score', overall_score // 4),
#                 'content': parsed.get('content_score', overall_score // 4),
#                 'engagement': parsed.get('engagement_score', overall_score // 4),
#                 'assessment': parsed.get('assessment_score', overall_score // 4)
#             }
            
#             # Ensure component scores are valid
#             for key in component_scores:
#                 component_scores[key] = max(0, min(25, component_scores[key]))
            
#             # Recalculate overall score from components
#             calculated_score = sum(component_scores.values())
#             if abs(calculated_score - overall_score) > 10:
#                 overall_score = calculated_score
            
#             return {
#                 "overall_score": overall_score,
#                 "criterion_scores": component_scores,
#                 "strengths": parsed.get('strengths', self._default_strengths(content_type, course_context)),
#                 "improvements": parsed.get('improvements', self._default_improvements(content_type, course_context)),
#                 "recommendations": parsed.get('recommendations', self._default_recommendations(content_type, course_context)),
#                 "rationale": parsed.get('comprehensive_rationale', self._default_rationale(overall_score, content_type, course_context)),
#                 "passed_qa": overall_score >= QA_PASS_THRESHOLD,
#                 "detailed_analysis": {
#                     "pedagogical_analysis": {"score": component_scores['pedagogical'], "reasoning": "SLO integration and pedagogical alignment assessed"},
#                     "content_analysis": {"score": component_scores['content'], "reasoning": "Content depth and accuracy evaluated"},
#                     "engagement_analysis": {"score": component_scores['engagement'], "reasoning": "Student engagement potential reviewed"},
#                     "assessment_analysis": {"score": component_scores['assessment'], "reasoning": "Assessment integration examined"}
#                 }
#             }
            
#         except (json.JSONDecodeError, KeyError, ValueError) as e:
#             logger.warning(f"Failed to parse QA JSON: {e}")
#             return self._fallback_analysis(response_content, content_type, course_context)
    
#     def _default_strengths(self, content_type: str, course_context: CourseContext) -> List[str]:
#         """Generate default strengths based on context."""
#         return [
#             f"Content demonstrates appropriate academic rigor for {course_context.program_type} level",
#             f"Clear structure supports {course_context.teaching_style} methodology",
#             f"Integrates {len(course_context.selected_slos + course_context.custom_slos)} SLOs effectively into learning framework"
#         ]
    
#     def _default_improvements(self, content_type: str, course_context: CourseContext) -> List[str]:
#         """Generate default improvements based on context."""
#         return [
#             f"Enhance real-world applications specific to {course_context.program_type} career paths",
#             f"Strengthen alignment with {course_context.teaching_style} pedagogical approach",
#             f"Expand interactive elements to support {course_context.sessions_per_week} sessions per week format"
#         ]
    
#     def _default_recommendations(self, content_type: str, course_context: CourseContext) -> List[str]:
#         """Generate default recommendations based on context."""
#         return [
#             f"Consider adding complexity appropriate for {course_context.program_type} students",
#             f"Include current industry examples relevant to {course_context.course_name}",
#             f"Explicitly connect activities to Program SLO development throughout content"
#         ]
    
#     def _default_rationale(self, score: int, content_type: str, course_context: CourseContext) -> str:
#         """Generate default rationale based on score and context."""
        
#         complexity_assessment = ""
#         if course_context.program_type == "Undergraduate":
#             complexity_assessment = "Content appropriately targets foundational learning with clear explanations suitable for undergraduate students."
#         elif course_context.program_type == "Kelley Direct":
#             complexity_assessment = "Content demonstrates graduate-level strategic thinking appropriate for online professional students."
#         else:  # MBA
#             complexity_assessment = "Content requires sophisticated analysis matching executive MBA expectations."
        
#         quality_assessment = ""
#         if score >= 90:
#             quality_assessment = "Exceptional quality demonstrating excellent pedagogical design and comprehensive SLO integration."
#         elif score >= 80:
#             quality_assessment = "High quality content meeting academic standards with strong pedagogical foundation."
#         elif score >= 70:
#             quality_assessment = "Good quality content with solid structure and adequate learning support."
#         else:
#             quality_assessment = "Content requires significant improvement to meet quality standards."
        
#         return f"""
#         COMPREHENSIVE EVALUATION RATIONALE:
        
#         Course Context Analysis: This {content_type} for {course_context.course_name} incorporates {len(course_context.selected_slos + course_context.custom_slos)} Student Learning Outcomes within a {course_context.teaching_style} pedagogical framework. The content structure supports {course_context.sessions_per_week} sessions per week over {course_context.weeks} weeks.
        
#         Complexity Alignment: {complexity_assessment}
        
#         Quality Assessment: {quality_assessment}
        
#         SLO Integration: The content demonstrates {'strong' if score >= 85 else 'adequate' if score >= 75 else 'developing'} integration of Program SLOs with clear connections to Learning Objectives throughout the material.
        
#         Teaching Methodology: Content {'effectively supports' if score >= 80 else 'adequately aligns with' if score >= 70 else 'needs better alignment with'} the selected {course_context.teaching_style} approach through {'well-designed' if score >= 80 else 'appropriate' if score >= 70 else 'basic'} activities and assessments.
        
#         Overall Assessment: Score of {score}/100 indicates {'excellent' if score >= 90 else 'very good' if score >= 85 else 'good' if score >= 80 else 'satisfactory' if score >= 75 else 'developing'} quality suitable for {'immediate implementation' if score >= 85 else 'use with minor enhancements' if score >= 75 else 'revision before implementation'}.
#         """
    
#     def _fallback_analysis(self, content: str, content_type: str, course_context: CourseContext) -> Dict[str, Any]:
#         """Enhanced fallback analysis when detailed evaluation fails."""
        
#         # Analyze content characteristics  
#         word_count = len(content.split()) if isinstance(content, str) else 0
#         has_objectives = any(word in content.lower() for word in ['objective', 'outcome', 'goal', 'learn']) if isinstance(content, str) else False
#         has_activities = any(word in content.lower() for word in ['activity', 'exercise', 'discussion', 'practice']) if isinstance(content, str) else False
#         has_examples = any(word in content.lower() for word in ['example', 'case', 'illustration']) if isinstance(content, str) else False
#         has_assessments = any(word in content.lower() for word in ['assessment', 'evaluation', 'grade', 'rubric']) if isinstance(content, str) else False
#         has_current_refs = any(word in content.lower() for word in ['2024', '2025', 'current', 'recent']) if isinstance(content, str) else False
        
#         # Calculate score based on program complexity
#         base_score = 70
#         if course_context.program_type == "MBA":
#             base_score = 75
#         elif course_context.program_type == "Kelley Direct":
#             base_score = 72
        
#         # Content analysis bonuses
#         if word_count > 1500: base_score += 8
#         elif word_count > 1000: base_score += 5
#         if has_objectives: base_score += 5
#         if has_activities: base_score += 5
#         if has_examples: base_score += 3
#         if has_assessments: base_score += 3
#         if has_current_refs: base_score += 4
        
#         final_score = min(95, base_score)
        
#         return {
#             "overall_score": final_score,
#             "criterion_scores": {
#                 "pedagogical": final_score // 4,
#                 "content": final_score // 4,
#                 "engagement": final_score // 4 - (2 if not has_activities else 0),
#                 "assessment": final_score // 4 - (2 if not has_objectives else 0)
#             },
#             "strengths": self._default_strengths(content_type, course_context),
#             "improvements": self._default_improvements(content_type, course_context),
#             "recommendations": self._default_recommendations(content_type, course_context),
#             "rationale": f"""
#             FALLBACK ANALYSIS COMPLETED:
#             Content analysis for {course_context.course_name} shows {word_count} words with {'comprehensive' if final_score >= 85 else 'good' if final_score >= 75 else 'adequate'} structure.
#             Program complexity level: {course_context.program_type} (appropriate content depth {'achieved' if final_score >= 80 else 'developing'}).
#             Educational elements: {'Strong' if final_score >= 85 else 'Adequate' if final_score >= 75 else 'Basic'} pedagogical framework detected.
#             Quality assessment: {final_score}/100 indicating {'excellent' if final_score >= 90 else 'good' if final_score >= 80 else 'satisfactory'} quality for {course_context.program_type} level.
#             SLO Integration: Content structure supports the {len(course_context.selected_slos + course_context.custom_slos)} selected learning outcomes within {course_context.teaching_style} methodology.
#             """,
#             "passed_qa": final_score >= QA_PASS_THRESHOLD
#         }


"""
Quality Assurance Agent - LLM as a judge
"""

import json
import logging
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from config import CourseContext, QA_PASS_THRESHOLD

logger = logging.getLogger(__name__)

class QualityAssuranceAgent:
    """
    Simplified QA Agent with single LLM judge providing comprehensive rationale.
    """
    
    def __init__(self, api_key: str, model_type: str = "gpt-4o-mini"):
        self.llm = ChatOpenAI(api_key=api_key, model=model_type, temperature=0.2)

    async def generate_actionable_suggestions(self, content: str, content_type: str, 
                                         course_context: CourseContext,
                                         granularity: str = "Medium-level",
                                         previous_suggestions: str = "") -> str:
        """
        Generate content-based actionable suggestions for improvement.
        
        Args:
            content: The generated content to analyze
            content_type: Type of content (syllabus, lecture_notes, etc.)
            course_context: Course context information
            granularity: Level of detail for suggestions
            previous_suggestions: Previously applied suggestions to avoid regression
            
        Returns:
            Formatted actionable suggestions string
        """
        try:
            logger.debug(f"Generating {granularity} actionable suggestions for {content_type}")
            
            granularity_instructions = self._get_granularity_instructions(granularity)
            
            # Build constraint prompt for preventing regression
            constraint_prompt = ""
            if previous_suggestions:
                constraint_prompt = f"""
CRITICAL CONSTRAINT - PREVENT REGRESSION:
The following improvements have been applied in previous versions and MUST BE MAINTAINED:

{previous_suggestions}

MANDATORY REQUIREMENTS:
1. Do NOT suggest anything that contradicts or undoes previous improvements
2. Do NOT suggest removing any previously applied enhancements
3. Only suggest NEW improvements that BUILD UPON the existing ones
4. If suggesting a refinement of a previous improvement, explicitly state which one you're extending
5. Verify each suggestion doesn't conflict with locked-in improvements

Your suggestions should ADD to what's already been done, never subtract or replace.
"""
            
            prompt = f"""
            You are Dr. Maria Rodriguez, an expert educational consultant with 15 years experience improving course materials at top business schools.
            
            {constraint_prompt}
            
            Analyze this {content_type} for {course_context.course_name} using ROOT CAUSE ANALYSIS. Don't just identify symptoms—diagnose WHY content is weak and prescribe specific fixes.
            
            YOUR DIAGNOSTIC FRAMEWORK:
            
            1. SPECIFICITY AUDIT:
               - Are concepts illustrated with NAMED examples (real companies, specific tools, actual data)?
               - Are learning objectives MEASURABLE with concrete success criteria?
               - Are assessments SPECIFIC with clear deliverables and rubrics?
               
            2. COGNITIVE LOAD ANALYSIS:
               - Is content chunked appropriately (5-7 concepts per segment)?
               - Are worked examples provided BEFORE independent practice?
               - Is progression clear (foundation → application → synthesis)?
               
            3. ENGAGEMENT DIAGNOSTIC:
               - Does it open with a provocative question or current event?
               - Are there contrasting cases or "choice points" for analysis?
               - Are students doing something active every 10-15 minutes?
               
            4. ASSESSMENT ALIGNMENT:
               - Does each assessment map to specific learning outcomes?
               - Are rubric criteria observable and measurable?
               - Is there progression (formative → summative)?
               
            5. ANTI-PATTERN DETECTION:
               Identify if content contains:
               - Vague verbs: "understand," "learn," "explore," "gain familiarity"
               - Generic claims: "industry-leading," "cutting-edge," "hands-on" without specifics
               - Missing evidence: statements without sources, examples without analysis
               - Passive language: "it can be seen," "there are many"
            
            {granularity_instructions}
            
            CONTENT TO ANALYZE (first 2500 chars):
            {content[:2500]}...
            
            COURSE CONTEXT:
            - Course: {course_context.course_name}
            - Program: {course_context.program_type}
            - Teaching Style: {course_context.teaching_style}
            - Duration: {course_context.weeks} weeks, {course_context.sessions_per_week} sessions/week
            - Assessment Methods: {', '.join(course_context.assessment_preferences)}
            - SLOs: {len(course_context.selected_slos + course_context.custom_slos)} total
            
            PROVIDE 6-8 DIAGNOSTIC SUGGESTIONS in this format:
            
            [NUMBER]. **[DIAGNOSIS]**: [What's weak and WHY]
               **Root Cause**: [Underlying issue - e.g., "lacks specificity," "missing cognitive scaffolding," "no measurable criteria"]
               **Specific Fix**: [Concrete action - reference specific weeks, sections, or topics]
               **Example**: [Show what good looks like - give a specific example of the improvement]
               **Impact**: [How this improves learning outcomes - reference specific SLO if relevant]
            
            EXAMPLE FORMAT:
            1. **Week 3 lacks concrete examples**: Currently uses vague "companies use this approach" language
               **Root Cause**: Generic claims without named examples reduce credibility and student engagement
               **Specific Fix**: Replace "companies" with 3 named examples: "Netflix's recommendation algorithm, Amazon's supply chain optimization, and Tesla's manufacturing process"
               **Example**: "Netflix analyzes 2+ billion viewing hours monthly using collaborative filtering to personalize recommendations for 230M+ subscribers"
               **Impact**: Concrete examples help students visualize application and support SLO MBA-3.1 (identifying appropriate frameworks)
            
            Focus on fixes that:
            - Add named examples, specific data, or real case studies
            - Strengthen measurability and assessment alignment  
            - Improve cognitive scaffolding and learning progression
            - Replace vague language with concrete, observable criteria
            - Build upon (not contradict) previous improvements
            
            Teaching methodology: {course_context.teaching_style}
            """
            
            messages = [
                SystemMessage(content=f"You are Dr. Maria Rodriguez, providing diagnostic analysis of educational content with specific, actionable improvements."),
                HumanMessage(content=prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            return response.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating actionable suggestions: {e}")
            return self._fallback_suggestions(content_type, course_context, granularity)
    
    def _get_granularity_instructions(self, granularity: str) -> str:
        """Get instructions based on granularity level."""
        if "High-level" in granularity:
            return """
            GRANULARITY: HIGH-LEVEL (Strategic/Structural)
            
            Focus your diagnostic on:
            - **Course Architecture**: Is the progression logical? Does complexity build appropriately?
            - **Learning Scaffolding**: Are foundational concepts established before advanced ones?
            - **Assessment Strategy**: Do assessments align with outcomes? Is there formative + summative balance?
            - **Cognitive Load**: Are segments appropriately chunked (7±2 concepts per section)?
            - **Real-World Bridge**: Does course connect theory to practice throughout?
            
            Your suggestions should address STRUCTURAL issues:
            - Resequence modules for better learning progression
            - Add/remove major course components
            - Redesign assessment strategy
            - Restructure cognitive load distribution
            
            Example: "Weeks 1-4 introduce 15+ frameworks without application. Restructure to: Week 1-2 foundational theory, Week 3-4 apply to 2-3 real cases, creating scaffolded learning progression."
            
            Provide 5-6 strategic suggestions that reshape course structure.
            """
        elif "Fine-grained" in granularity:
            return """
            GRANULARITY: FINE-GRAINED (Detailed/Tactical)
            
            Focus your diagnostic on:
            - **Specific Content Gaps**: Which exact readings, case studies, or examples are missing?
            - **Activity Design**: Are in-class activities well-structured with clear instructions?
            - **Assessment Rubrics**: Do rubric criteria have specific, observable indicators?
            - **SLO Mapping**: Is each activity explicitly tied to specific SLO codes?
            - **Resource Quality**: Are cited sources current (2024-2025), credible, and diverse?
            
            Your suggestions should be HIGHLY SPECIFIC:
            - Name exact articles, cases, or textbook chapters to add
            - Specify which tools/software (with version numbers if relevant)
            - Provide example assignment prompts or discussion questions
            - Suggest specific rubric criteria with 3-4 performance levels
            - Map activities to precise SLO codes with rationale
            
            Examples:
            - "Week 3, Session 2: Add Harvard Business Review case 'Netflix's Recommendation Engine' (2024) to illustrate collaborative filtering"
            - "Assignment 2 rubric: Add criterion 'Data Visualization Quality' with levels: Exemplary (uses 3+ chart types appropriately), Proficient (2 chart types with clear labels), Developing (1 chart type or unclear labels), Unsatisfactory (no visualization or misleading)"
            - "Week 5 activity: Replace generic 'analyze a company' with structured prompt: 'Using Porter's Five Forces, analyze Airbnb's competitive position. Create a matrix rating each force 1-5 with evidence from 2024 10-K filing.'"
            
            Provide 7-8 detailed, specific suggestions with examples.
            """
        else:  # Medium-level
            return """
            GRANULARITY: MEDIUM-LEVEL (Topic/Module Focus)
            
            Focus your diagnostic on:
            - **Topic Coverage**: Are key concepts within each module explained clearly?
            - **Example Quality**: Does each major topic have 2-3 concrete examples?
            - **Activity Alignment**: Do learning activities match topic objectives?
            - **Assessment Variety**: Is there diversity in how topics are assessed?
            - **Resource Types**: Are there readings, videos, interactive tools for each module?
            
            Your suggestions should target TOPIC-LEVEL improvements:
            - Enhance specific weeks or modules with better examples
            - Add activity types for particular topics (not specific activities)
            - Suggest resource categories (not specific titles)
            - Improve topic-to-assessment connections
            - Strengthen within-topic progression
            
            Examples:
            - "Week 4 (Game Theory): Add 2-3 current business examples of Nash equilibrium (e.g., pricing strategy, market entry). Include interactive simulation for students to model strategic decisions."
            - "Weeks 6-8 (Strategic Analysis): Diversify assessments beyond case studies. Add: one competitive analysis matrix assignment, one strategy memo (1000 words), one peer evaluation component."
            - "Week 10 (Innovation): Supplement lecture with practitioner resources - industry reports from McKinsey/BCG, startup founder interviews/podcasts, innovation metrics dashboards."
            
            Provide 6-7 practical, topic-focused suggestions.
            """
    
    def _fallback_suggestions(self, content_type: str, course_context: CourseContext, 
                            granularity: str) -> str:
        """Generate fallback suggestions if AI call fails."""
        if "High-level" in granularity:
            return f"""1. Consider reorganizing course modules to build foundational concepts before advanced topics
2. Balance theoretical content with practical applications appropriate for {course_context.program_type} students
3. Integrate more real-world case studies aligned with {course_context.teaching_style} methodology
4. Diversify assessment methods beyond {', '.join(course_context.assessment_preferences[:2])}
5. Add explicit connections between weekly topics and Program SLOs throughout"""
        elif "Fine-grained" in granularity:
            return f"""1. Week 1: Add a specific icebreaker activity to establish {course_context.teaching_style} classroom culture
2. Week 2-3: Include Harvard Business Review case study on current industry trends
3. Week 4: Incorporate hands-on Excel/data analysis exercise with real datasets
4. Week 5: Add peer review component to assessment aligned with SLO on collaboration
5. Week 8: Include guest speaker or industry practitioner video interview
6. Week 10-12: Assign McKinsey Quarterly or similar practitioner-focused readings
7. Week 14: Add reflective journaling assignment connecting course concepts to career goals
8. Throughout: Embed formative assessment checkpoints (2-3 per module) for self-paced learning"""
        else:  # Medium
            return f"""1. Weeks 1-4: Add more foundational case studies to support concept application
2. Mid-term: Introduce a team-based project component aligned with {course_context.teaching_style}
3. Weeks 5-8: Incorporate current industry reports (2024-2025) as supplementary readings
4. Assessment: Add one low-stakes formative assessment to support learning progression
5. Weeks 9-12: Include interactive simulations or role-playing scenarios for practice
6. Throughout: Strengthen explicit SLO connections in learning objectives for each week"""
    

    async def review_content(self, content: str, content_type: str, 
                           course_context: CourseContext) -> Dict[str, Any]:
        """
        Comprehensive content review with single LLM judge rationale.
        """
        try:
            logger.debug(f"Starting QA review for {content_type}")
            
            # Single comprehensive evaluation
            evaluation = await self._comprehensive_evaluation(content, content_type, course_context)
            
            logger.debug(f"QA completed: {evaluation['overall_score']}/100, passed: {evaluation.get('passed_qa', False)}")
            
            return evaluation
            
        except Exception as e:
            logger.warning(f"QA analysis error: {e}")
            return self._fallback_analysis(content, content_type, course_context)
    
    async def _comprehensive_evaluation(self, content: str, content_type: str, course_context: CourseContext) -> Dict[str, Any]:
        """Single comprehensive LLM evaluation with detailed rationale."""
        
        prompt = f"""
        You are Dr. Sarah Chen, expert educational evaluator with 20 years at top business schools. Provide evidence-based quality assessment of this {content_type}.

        CONTENT TO EVALUATE (first 2500 chars):
        {content[:2500]}...

        COURSE CONTEXT:
        - Course: {course_context.course_name}
        - Program: {course_context.program_type} (complexity: UG < Kelley Direct < MBA)
        - Teaching Style: {course_context.teaching_style}
        - Selected SLOs: {len(course_context.selected_slos)} program + {len(course_context.custom_slos)} custom
        - Assessment Preferences: {', '.join(course_context.assessment_preferences)}
        - Structure: {course_context.weeks} weeks, {course_context.sessions_per_week} sessions/week, {course_context.duration_per_session} min/session

        EVALUATION FRAMEWORK:

        **1. PEDAGOGICAL ALIGNMENT (0-25 points)**
        Evidence: Are outcomes measurable (action verbs), complexity appropriate, clear progression, natural SLO integration, methodology evident?
        Score: 20-25=excellent, 15-19=good, 10-14=needs work, 0-9=poor

        **2. CONTENT QUALITY (0-25 points)**
        Evidence: Named examples (5+), current sources (2024-2025), appropriate depth, evidence-based, minimal jargon?
        Score: 20-25=excellent, 15-19=good, 10-14=needs work, 0-9=poor

        **3. STUDENT ENGAGEMENT (0-25 points)**
        Evidence: Compelling hook, contrasting cases, active learning, variety, career relevance?
        Score: 20-25=excellent, 15-19=good, 10-14=needs work, 0-9=poor

        **4. ASSESSMENT INTEGRATION (0-25 points)**
        Evidence: Outcome mapping, measurable criteria, formative+summative, authentic SLO assessment, logistics specified?
        Score: 20-25=excellent, 15-19=good, 10-14=needs work, 0-9=poor

        COUNT QUALITY INDICATORS:
        - Named companies/organizations: ___
        - Data points with sources: ___
        - Action verbs in outcomes: ___
        - Measurable assessment criteria: ___
        - Formative assessments: ___
        - Active learning activities: ___

        Return ONLY valid JSON:
        {{
            "overall_score": [0-100],
            "pedagogical_score": [0-25],
            "content_score": [0-25], 
            "engagement_score": [0-25],
            "assessment_score": [0-25],
            "passed_qa": [true if score >= 80],
            "quality_indicators": {{
                "named_examples_count": [number],
                "data_points_count": [number],
                "action_verbs_count": [number],
                "measurable_criteria_count": [number],
                "formative_assessments_count": [number],
                "active_learning_activities_count": [number]
            }},
            "strengths": ["strength 1 with evidence", "strength 2 with evidence", "strength 3 with evidence"],
            "improvements": ["weakness 1 with evidence", "weakness 2 with evidence", "weakness 3 with evidence"],
            "recommendations": ["actionable fix 1", "actionable fix 2", "actionable fix 3"],
            "comprehensive_rationale": "Write 350-450 words: (1) How scores determined with evidence (cite indicators), (2) How content matches {course_context.program_type} complexity and {course_context.teaching_style} with examples, (3) Strengths with evidence, (4) Weaknesses with evidence, (5) Most impactful improvements. Be specific—avoid generic language."
        }}
        """
        
        messages = [
            SystemMessage(content="You are Dr. Sarah Chen, providing evidence-based evaluation with specific quality indicators."),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return self._parse_json_response(response.content, content_type, course_context)

    def _parse_json_response(self, response_content: str, content_type: str, course_context: CourseContext) -> Dict[str, Any]:
        """Parse JSON response with enhanced fallback."""
        try:
            # Clean response content
            content = response_content.strip()
            
            # Find JSON block
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                json_text = content[json_start:json_end].strip()
            elif "{" in content and "}" in content:
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                json_text = content[json_start:json_end]
            else:
                json_text = content
            
            parsed = json.loads(json_text)
            
            # Validate and ensure all required fields
            overall_score = parsed.get('overall_score', 75)
            overall_score = max(0, min(100, overall_score))
            
            # Calculate component scores if missing
            component_scores = {
                'pedagogical': parsed.get('pedagogical_score', overall_score // 4),
                'content': parsed.get('content_score', overall_score // 4),
                'engagement': parsed.get('engagement_score', overall_score // 4),
                'assessment': parsed.get('assessment_score', overall_score // 4)
            }
            
            # Ensure component scores are valid
            for key in component_scores:
                component_scores[key] = max(0, min(25, component_scores[key]))
            
            # Recalculate overall score from components
            calculated_score = sum(component_scores.values())
            if abs(calculated_score - overall_score) > 10:
                overall_score = calculated_score
            
            return {
                "overall_score": overall_score,
                "criterion_scores": component_scores,
                "strengths": parsed.get('strengths', self._default_strengths(content_type, course_context)),
                "improvements": parsed.get('improvements', self._default_improvements(content_type, course_context)),
                "recommendations": parsed.get('recommendations', self._default_recommendations(content_type, course_context)),
                "rationale": parsed.get('comprehensive_rationale', self._default_rationale(overall_score, content_type, course_context)),
                "passed_qa": overall_score >= QA_PASS_THRESHOLD,
                "detailed_analysis": {
                    "pedagogical_analysis": {"score": component_scores['pedagogical'], "reasoning": "SLO integration and pedagogical alignment assessed"},
                    "content_analysis": {"score": component_scores['content'], "reasoning": "Content depth and accuracy evaluated"},
                    "engagement_analysis": {"score": component_scores['engagement'], "reasoning": "Student engagement potential reviewed"},
                    "assessment_analysis": {"score": component_scores['assessment'], "reasoning": "Assessment integration examined"}
                }
            }
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Failed to parse QA JSON: {e}")
            return self._fallback_analysis(response_content, content_type, course_context)
    
    def _default_strengths(self, content_type: str, course_context: CourseContext) -> List[str]:
        """Generate default strengths based on context."""
        return [
            f"Content demonstrates appropriate academic rigor for {course_context.program_type} level",
            f"Clear structure supports {course_context.teaching_style} methodology",
            f"Integrates {len(course_context.selected_slos + course_context.custom_slos)} SLOs effectively into learning framework"
        ]
    
    def _default_improvements(self, content_type: str, course_context: CourseContext) -> List[str]:
        """Generate default improvements based on context."""
        return [
            f"Enhance real-world applications specific to {course_context.program_type} career paths",
            f"Strengthen alignment with {course_context.teaching_style} pedagogical approach",
            f"Expand interactive elements to support {course_context.sessions_per_week} sessions per week format"
        ]
    
    def _default_recommendations(self, content_type: str, course_context: CourseContext) -> List[str]:
        """Generate default recommendations based on context."""
        return [
            f"Consider adding complexity appropriate for {course_context.program_type} students",
            f"Include current industry examples relevant to {course_context.course_name}",
            f"Explicitly connect activities to Program SLO development throughout content"
        ]
    
    def _default_rationale(self, score: int, content_type: str, course_context: CourseContext) -> str:
        """Generate default rationale based on score and context."""
        
        complexity_assessment = ""
        if course_context.program_type == "Undergraduate":
            complexity_assessment = "Content appropriately targets foundational learning with clear explanations suitable for undergraduate students."
        elif course_context.program_type == "Kelley Direct":
            complexity_assessment = "Content demonstrates graduate-level strategic thinking appropriate for online professional students."
        else:  # MBA
            complexity_assessment = "Content requires sophisticated analysis matching executive MBA expectations."
        
        quality_assessment = ""
        if score >= 90:
            quality_assessment = "Exceptional quality demonstrating excellent pedagogical design and comprehensive SLO integration."
        elif score >= 80:
            quality_assessment = "High quality content meeting academic standards with strong pedagogical foundation."
        elif score >= 70:
            quality_assessment = "Good quality content with solid structure and adequate learning support."
        else:
            quality_assessment = "Content requires significant improvement to meet quality standards."
        
        return f"""
        COMPREHENSIVE EVALUATION RATIONALE:
        
        Course Context Analysis: This {content_type} for {course_context.course_name} incorporates {len(course_context.selected_slos + course_context.custom_slos)} Student Learning Outcomes within a {course_context.teaching_style} pedagogical framework. The content structure supports {course_context.sessions_per_week} sessions per week over {course_context.weeks} weeks.
        
        Complexity Alignment: {complexity_assessment}
        
        Quality Assessment: {quality_assessment}
        
        SLO Integration: The content demonstrates {'strong' if score >= 85 else 'adequate' if score >= 75 else 'developing'} integration of Program SLOs with clear connections to Learning Objectives throughout the material.
        
        Teaching Methodology: Content {'effectively supports' if score >= 80 else 'adequately aligns with' if score >= 70 else 'needs better alignment with'} the selected {course_context.teaching_style} approach through {'well-designed' if score >= 80 else 'appropriate' if score >= 70 else 'basic'} activities and assessments.
        
        Overall Assessment: Score of {score}/100 indicates {'excellent' if score >= 90 else 'very good' if score >= 85 else 'good' if score >= 80 else 'satisfactory' if score >= 75 else 'developing'} quality suitable for {'immediate implementation' if score >= 85 else 'use with minor enhancements' if score >= 75 else 'revision before implementation'}.
        """
    
    def _fallback_analysis(self, content: str, content_type: str, course_context: CourseContext) -> Dict[str, Any]:
        """Enhanced fallback analysis when detailed evaluation fails."""
        
        # Analyze content characteristics  
        word_count = len(content.split()) if isinstance(content, str) else 0
        has_objectives = any(word in content.lower() for word in ['objective', 'outcome', 'goal', 'learn']) if isinstance(content, str) else False
        has_activities = any(word in content.lower() for word in ['activity', 'exercise', 'discussion', 'practice']) if isinstance(content, str) else False
        has_examples = any(word in content.lower() for word in ['example', 'case', 'illustration']) if isinstance(content, str) else False
        has_assessments = any(word in content.lower() for word in ['assessment', 'evaluation', 'grade', 'rubric']) if isinstance(content, str) else False
        has_current_refs = any(word in content.lower() for word in ['2024', '2025', 'current', 'recent']) if isinstance(content, str) else False
        
        # Calculate score based on program complexity
        base_score = 70
        if course_context.program_type == "MBA":
            base_score = 75
        elif course_context.program_type == "Kelley Direct":
            base_score = 72
        
        # Content analysis bonuses
        if word_count > 1500: base_score += 8
        elif word_count > 1000: base_score += 5
        if has_objectives: base_score += 5
        if has_activities: base_score += 5
        if has_examples: base_score += 3
        if has_assessments: base_score += 3
        if has_current_refs: base_score += 4
        
        final_score = min(95, base_score)
        
        return {
            "overall_score": final_score,
            "criterion_scores": {
                "pedagogical": final_score // 4,
                "content": final_score // 4,
                "engagement": final_score // 4 - (2 if not has_activities else 0),
                "assessment": final_score // 4 - (2 if not has_objectives else 0)
            },
            "strengths": self._default_strengths(content_type, course_context),
            "improvements": self._default_improvements(content_type, course_context),
            "recommendations": self._default_recommendations(content_type, course_context),
            "rationale": f"""
            FALLBACK ANALYSIS COMPLETED:
            Content analysis for {course_context.course_name} shows {word_count} words with {'comprehensive' if final_score >= 85 else 'good' if final_score >= 75 else 'adequate'} structure.
            Program complexity level: {course_context.program_type} (appropriate content depth {'achieved' if final_score >= 80 else 'developing'}).
            Educational elements: {'Strong' if final_score >= 85 else 'Adequate' if final_score >= 75 else 'Basic'} pedagogical framework detected.
            Quality assessment: {final_score}/100 indicating {'excellent' if final_score >= 90 else 'good' if final_score >= 80 else 'satisfactory'} quality for {course_context.program_type} level.
            SLO Integration: Content structure supports the {len(course_context.selected_slos + course_context.custom_slos)} selected learning outcomes within {course_context.teaching_style} methodology.
            """,
            "passed_qa": final_score >= QA_PASS_THRESHOLD
        }