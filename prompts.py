"""
Default Prompts - CORRECTED with COMPLETE verbatim prompts from original generators.py
All prompts extracted exactly as written in the original file.
"""

# Syllabus Generation Prompts
SYLLABUS_PROMPTS = {
    "schedule_metadata": """Generate structured course schedule for {course_name}.

{complexity_instructions}

Course Details:
- Weeks: {weeks}
- Sessions per week: {sessions_per_week}
- Session duration: {duration_per_session} minutes
- Teaching style: {teaching_style}

Return ONLY a JSON array with this exact structure:
[
  {{
    "week": 1,
    "week_theme": "Introduction to [Course Topic]",
    "sessions": [
      {{
        "session": "1.1",
        "topic": "Fundamentals and Overview",
        "duration": {duration_per_session}
      }},
      {{
        "session": "1.2", 
        "topic": "Key Concepts and Framework",
        "duration": {duration_per_session}
      }}
    ]
  }}
]

Generate {weeks} weeks, each with {sessions_per_week} sessions.
Topics must be specific to {course_name} and appropriate for {program_type} level.""",

    "header": """Create professional syllabus header:

{course_code} - {course_name_upper}
{semester_upper} SYLLABUS

Instructor: {professor_name}    {professor_email}
Office: {office_location}
Office Hours: {office_hours}
Class Schedule: {sessions_per_week} sessions per week, {duration_per_session} minutes each

Use exact information provided. Do not generate additional contact details.""",

    "introduction": """You are an experienced course designer. Write a compelling, intellectually honest introduction for {course_name}.

{complexity_instructions}

GROUNDING (critical):
- Any specific real-world fact — a statistic, dollar figure, market share, date, company result, or study — must come from the SOURCES provided to you and be cited inline as [n].
- Do NOT invent numbers, dates, financials, or studies. With no source for a figure, describe the idea qualitatively and give no number.
- Clearly-labelled hypothetical examples are fine for teaching, but frame them explicitly as illustrative.

WHAT TO DO:
1. Motivate why {course_name} matters to a {program_type} learner — the problems it lets them solve and the decisions it informs.
2. Name the core frameworks, methods, and skills the course develops (these are conceptual and need no external source).
3. Connect to real professional practice; where a source supports a specific claim, cite it as [n].
4. Preview how the course builds from foundations toward synthesis.

ANTI-PATTERNS (AVOID COMPLETELY):
- Generic openings: "In today's world," "rapidly changing," "ever-evolving," "competitive landscape"
- Vague promises: "gain insights," "develop understanding," "explore concepts," "learn about"
- Clichés: "journey," "unlock potential," "hands-on experience" without specifics
- Buzzwords without substance: "cutting-edge," "industry-leading," "world-class," "transformative," "synergy"
- ANY specific statistic, dollar amount, or dated event that is not drawn from and cited to a SOURCE

Course: {course_name}
Program: {program_type}
Teaching Style: {teaching_style}

Current Context (sources you may cite as [n]): {current_references}
{context_suffix}

Write 3-4 substantive paragraphs. Prefer concrete conceptual specificity (named frameworks, skills, decisions) over unsourced numeric claims.""",

    "learning_outcomes": """You are an expert in backward design and learning assessment. Create measurable, specific learning outcomes for {course_name}.

{complexity_instructions}

BACKWARD DESIGN REQUIREMENT:
For each outcome, think: "What SPECIFIC artifact/performance would prove a student achieved this?" Then work backward to define the outcome.

QUALITY STANDARDS (ALL REQUIRED):
1. Use Bloom's taxonomy verbs appropriate to {program_type} level (create, analyze, evaluate - NOT "understand" or "learn")
2. Each outcome must be MEASURABLE with specific evidence (e.g., "Design a DCF model with 3 scenarios" not "understand valuation")
3. Include CONCRETE deliverables (e.g., "Build a 15-slide pitch deck" or "Write a 2000-word analysis")
4. Map EACH outcome to specific assessment in the course (exam question type, project component, case analysis)
5. Reference SPECIFIC tools, frameworks, models by name (e.g., "Apply Porter's Five Forces to 3 industries")

ANTI-PATTERNS (AVOID):
- Vague verbs: understand, learn, know, appreciate, explore, gain familiarity
- Unmeasurable claims: "develop critical thinking," "gain insights"
- Generic statements: "apply concepts," "analyze problems"
- Missing specificity: "use frameworks" (which ones?), "solve business problems" (what kind?)

REQUIRED FORMAT FOR EACH OUTCOME:
**Learning Outcome [Number]**: [Specific, measurable statement]
- **Bloom's Level**: [Remember/Understand/Apply/Analyze/Evaluate/Create]
- **Program SLO Connection**: [Specific SLO code] - [Explain HOW this outcome develops that SLO capability]
- **Assessment Method**: [Specific way this will be measured - name the assignment/exam/project component]
- **Success Criteria**: [What does proficiency look like? Be specific]

Course: {course_name}
Program: {program_type}
Teaching Style: {teaching_style}

Available SLOs: {slo_content}

Create 5-7 outcomes that build in complexity. Start with foundational skills, progress to synthesis/creation.
{context_suffix}""",

    "course_overview": """Create course overview for {course_name}.

{complexity_instructions}

Include:
1. What {course_name} covers (topics and concepts)
2. Weekly structure over {weeks} weeks
3. How topics build upon each other
4. What makes {course_name} unique in {program_type}

Structure: {sessions_per_week} sessions per week
Teaching: {teaching_style}
Assessment: {assessment_preferences}
{context_suffix}""",

    "course_format": """Create course format details for {course_name}.

Include:
1. How {course_name} classes are conducted
2. Participation expectations
3. Technology requirements
4. Attendance policy
5. Communication guidelines

Program: {program_type}
Teaching Style: {teaching_style}
{context_suffix}""",

    "materials": """Create a materials and resources list for {course_name}.

{complexity_instructions}

GROUNDING: Do NOT fabricate specific ISBNs, editions, prices, or invented titles. If a specific source is provided below, cite it as [n]; otherwise describe the type of resource (e.g. "a current undergraduate-level microeconomics textbook") rather than inventing exact bibliographic details.

Include:
1. Core reading (textbook or equivalent) appropriate to {program_type}
2. Software/tools needed
3. Supplementary and open-access resources
4. Current resources drawn from the sources below, cited as [n]

Course: {course_name}
Program: {program_type}
Available sources (cite as [n]): {current_references}
{context_suffix}""",

    "assessment": """You are an expert in learning assessment design. Create a comprehensive, measurable assessment plan for {course_name}.

{complexity_instructions}

GROUNDING (critical):
- Assessment example prompts MAY reference real companies or scenarios, but you must NOT assert invented metrics (revenue, market share, user counts, dates) as real facts.
- If you cite a specific real figure, it must come from the SOURCES and be cited [n]. Otherwise, frame company scenarios as research tasks for students ("Research and analyze Company X's recent strategy in market Y") rather than stating fabricated numbers.
- Hypothetical figures are acceptable when clearly labelled as hypothetical ("Assume the firm earns $X").

QUALITY STANDARDS (ALL REQUIRED):
1. Each assessment must have SPECIFIC point values and clear grading criteria
2. Include CONCRETE deliverables with word counts, page limits, or submission formats
3. Map each assessment to 2-3 specific Learning Outcomes (reference by number)
4. Provide a clear example prompt per assessment, framed as a student research/analysis task (not as a set of asserted facts)
5. Include both formative (low-stakes) and summative (high-stakes) assessments
6. Specify collaboration policy for EACH assignment (individual/group/either)

REQUIRED ASSESSMENT BREAKDOWN:
- Total points: 1000 (makes calculation easy)
- 4-6 distinct assessment types from: {assessment_preferences}
- At least one formative assessment (low-stakes, practice)
- Clear progression: early assessments build skills for later ones

FOR EACH ASSESSMENT, PROVIDE:
1. **[Assessment Name]** (XXX points, XX% of grade)
   - **Format**: [Specific deliverable - e.g., "12-slide presentation with speaker notes"]
   - **Learning Outcomes Assessed**: [List specific LO numbers]
   - **Collaboration**: [Individual/Pairs/Groups of 3-4]
   - **Key Requirements**: [3-5 specific criteria that will be graded]
   - **Example Prompt/Topic**: [A student research/analysis task — e.g., "Analyze a public company's recent market-entry strategy using Porter's Five Forces"; cite any specific figure as [n]]
   - **Due Date**: [Week X, Day of Week]

GRADING POLICIES (these are course rules you set, not external facts — be specific):
- Late work: [Exact penalty - e.g., "10% per day, max 3 days"]
- Revision policy: [Can students revise? Which assignments? How many times?]
- Participation tracking: [How measured? Attendance + in-class activities?]
- Extra credit: [Available or not? Specific opportunities with point values]
- Lowest grade dropped: [Yes/no for which category? How many?]

ANTI-PATTERNS (AVOID):
- Vague criteria: "quality of work," "demonstration of understanding"
- Asserting fabricated company metrics as real facts
- Missing specifications: "presentation" (how long? how many slides?)
- Generic rubrics: "A=Excellent, B=Good" without observable criteria

Assessment Methods: {assessment_preferences}
Teaching Style: {teaching_style}
Duration: {weeks} weeks
{context_suffix}""",

    "administrative": """Create administrative section for {course_name}.

Include:
1. Instructor contact for questions
2. Communication expectations
3. Class policies
4. Support resources
5. AI classroom use policy

Instructor: {professor_name}
Email: {professor_email}
Office: {office_location}
Office Hours: {office_hours}

AI Policy for this course:
{ai_policy_text}

{context_suffix}""",

    "schedule": """Enhance this schedule for {course_name} by adding pedagogical structure UNDER each session.
Keep session titles EXACTLY as shown.

GROUNDING (critical): Worked examples should be pedagogically complete, but any real-world figure (market size, revenue, dates, company financials) must be drawn from the SOURCES and cited [n]. With no source, use a clearly-labelled hypothetical ("Suppose demand is 50,000 units") instead of asserting a real number. Never present invented data as fact.

REQUIRED ACTIVITY STRUCTURE (use for at least 50% of sessions):
1. Hook (5 min): A motivating question or example (cite [n] if it uses a real figure)
2. Worked Example (15-20 min): COMPLETE step-by-step reasoning, using sourced or clearly-hypothetical numbers
3. Faded Example (10-15 min): Partial solution, students complete
4. Independent Practice (10-15 min): New scenario, students apply
5. Formative Check (5 min): 2-3 quick questions

WORKED EXAMPLE TEMPLATE (use this):
- Worked Example: [Scenario — real and cited [n], or clearly hypothetical]
  - Step 1: [Action with reasoning] (e.g., "Calculate market size: assume 450,000 buyers × 12% = 54,000")
  - Step 2: [Analysis with reasoning] (e.g., "Apply Porter's Five Forces: Supplier power = HIGH because...")
  - Step 3: [Recommendation] (e.g., "Reduce price to target a larger share of the segment")
  - Common Mistake: [Specific error students make]

{schedule_metadata}

For EACH session, provide 2-4 specific activities with:
- Activity name and duration
- A scenario (sourced-and-cited, or clearly hypothetical)
- Expected outcome

Teaching style: {teaching_style}
Duration: {duration_per_session} min per session

Include worked examples in at least 8-10 sessions across the {weeks} weeks."""
}

# Lecture Notes Generation Prompts
LECTURE_PROMPTS = {
    "objectives": """Create learning objectives for {course_name} lecture: {topic}

{complexity_instructions}

Requirements:
- Objectives specific to {course_name} and {topic}
- Use "Program SLO" and "Learning Objective" terminology
- Show connections between {topic} and relevant SLOs
- 3-5 specific objectives for {topic}

Course: {course_name}
Teaching Style: {teaching_style}
Program SLOs: {slo_context}

Format: "By the end of this lecture, students will be able to..." """,

    "introduction": """Create introduction for {course_name} lecture: {topic}

{complexity_instructions}

Include:
1. Hook connecting {topic} to {course_name}
2. Why {topic} matters in {course_name}
3. How {topic} fits into course structure
4. Preview of {topic} coverage
5. Program SLO connections

Course: {course_name}
Program: {program_type}
Current Context: {current_content}""",

    "main_content": """You are an expert educator designing a {duration_per_session}-minute lecture on {topic} for {course_name}.

{complexity_instructions}

GROUNDING (critical): Any real-world fact — a company figure, statistic, date, or study — must come from the SOURCES provided and be cited [n]. Never invent numbers. Worked examples may use clearly-labelled HYPOTHETICAL figures ("Suppose...") when no source supports a real one.

COGNITIVE LOAD MANAGEMENT:
- Chunk content into 3-4 major segments (10-15 minutes each)
- Start each segment with a concrete example BEFORE theory
- Use the "worked example → faded example → independent practice" progression
- Limit new concepts to 5-7 per segment (working memory constraint)

REQUIRED STRUCTURE:

**SEGMENT 1: Hook & Foundation (10-12 min)**
- Open with a concrete, motivating case. If it uses a real event/figure, cite it [n] from the SOURCES; otherwise frame it as a clearly-hypothetical scenario
- Present 1 provocative question students will answer by end
- Introduce 3-5 core concepts with concrete definitions using real examples
- Use 2+ visual analogies or comparisons to familiar concepts

**SEGMENT 2: COMPLETE WORKED EXAMPLE (15-18 min) - CRITICAL**
YOU MUST PROVIDE A FULL WORKED EXAMPLE WITH ALL THESE ELEMENTS:
- **Scenario**: A concrete situation — a real, sourced-and-cited [n] case OR a clearly-labelled hypothetical (e.g., "Suppose a travel platform faces a 20% booking decline in one region")
- **Step 1**: [Action] with explanation (e.g., "First, calculate market size: assume 450,000 regional travelers × 12% adoption = 54,000 potential users")
- **Step 2**: [Action] with reasoning (e.g., "Next, analyze competitive threats: Booking.com gained 8% market share by...")
- **Step 3**: [Action] with decision rationale (e.g., "Then, apply Porter's Five Forces: Threat of substitutes (hotels) = HIGH because...")
- **Step 4**: [Conclusion] with numbers (e.g., "Result: Recommend pricing strategy reducing nightly rate 15% to regain 12% market share")
- **Common Mistakes**: List 2-3 errors students make (e.g., "Students often forget to adjust for seasonality, leading to 30%+ forecast errors")
- **Think-Aloud**: Show reasoning at each step ("Why did I start with market size? Because...")

**SEGMENT 3: Comparative Analysis (15-18 min)**
- Present 2-3 contrasting cases (real and cited [n], or clearly hypothetical)
- Create comparison table/matrix showing differences
- Highlight decision points: "Company A chose X because [reason], Company B chose Y because [different reason]"
- Connect decisions back to framework from Segment 1

**SEGMENT 4: FADED EXAMPLE (12-15 min) - CRITICAL**
- Present NEW scenario (different company, different year)
- Work through first 2 steps together (thinking aloud)
- Have students complete remaining steps independently or in pairs
- Provide correct answer with explanation
- Quick formative check: 2-3 questions testing understanding
- Preview connection to upcoming assignment

QUALITY REQUIREMENTS:
1. Use concrete examples; any named-company datum must be cited [n] from the SOURCES (otherwise keep it qualitative or hypothetical)
2. Do NOT invent statistics — cite real figures [n] or label them as assumptions/hypotheticals
3. Reference 2-3 specific tools/models/frameworks BY NAME (conceptual — no source needed)
4. Provide 2+ "common mistakes" or "pitfalls to avoid" with specific consequences
5. Include 3+ discussion questions requiring analysis, not recall
6. Map content to SLO capabilities: {relevant_slo_codes}

ANTI-PATTERNS (AVOID):
- Bullet lists without narrative ("Companies use SWOT for..." → Show HOW with worked example)
- Definitions without examples ("Market segmentation is..." → Show Spotify's actual segmentation)
- Examples without analysis ("Netflix did X" → WHY did they do X? What was the reasoning?)
- Passive voice: "it can be seen," "there are many approaches"
- Chronological history unless revealing pattern/principle
- Saying "worked example" without actually working through one step-by-step

TIMING CHECKPOINTS (include these):
[0 min] Opening hook
[12 min] Transition to worked example
[30 min] Begin comparative analysis
[45 min] Start faded example
[60 min] Formative assessment
[70 min] Connect to assignment, preview next class

Course: {course_name}
Teaching Style: {teaching_style}
Program: {program_type}
Current Examples: {current_content}

Focus on SLOs: {relevant_slo_codes}
Show how {topic} develops these SLO capabilities through COMPLETE worked examples with all steps shown.""",

    "activities": """Design activities for {course_name} lecture: {topic}

{complexity_instructions}

Requirements:
- Activities help develop Program SLO capabilities
- Show connections to Learning Objectives
- Use "Program SLO" and "Learning Objective" terminology
- 2-3 activities (15-20 minutes total)

Create activities that:
1. Apply {topic} to {course_name} scenarios
2. Use {teaching_style} methodology
3. Develop specific SLO capabilities
4. Show Learning Objective achievement

For each activity include:
- Objective (connected to Program SLOs)
- Instructions
- Time allocation
- Materials needed
- Expected SLO development""",

    "assessment": """Create assessment for {course_name} lecture: {topic}

{complexity_instructions}

Include:
1. Quick assessment of {topic} understanding
2. Key takeaways from {topic}
3. Preview of next session
4. Assignment preparation
5. Program SLO development reflection

Assessment Methods: {assessment_preferences}"""
}

# Assignment Generation Prompts
ASSIGNMENT_PROMPTS = {
    "assignment_content": """Create detailed instructions for {course_name} assignment: {topic}

{complexity_instructions}

GROUNDING (critical): Frame company scenarios as student research tasks ("Research and analyze Company X…"), not as asserted facts. Any specific real figure must come from the SOURCES and be cited [n]; otherwise use clearly-labelled hypothetical numbers. Never invent prices, financials, or dates.

CRITICAL: Provide COMPLETE step-by-step instructions with concrete examples at each step.

STEP-BY-STEP STRUCTURE (REQUIRED):
Step 1: [Specific action with measurable outcome]
- Example: "Analyze Tesla's Q3 2024 Cybertruck pricing strategy"
- Deliverable: 2-page analysis using Porter's Five Forces
- Success criteria: Identify 3+ competitive threats with data

Step 2: [Build on Step 1]
- Example: "Calculate breakeven price point using 2024 production costs"
- Tool: Excel financial model (template provided)
- Output: One-page memo with recommendation

[Continue for 4-6 steps total]

SPECIFICITY REQUIREMENTS:
1. Name 5+ real companies as comparison/context (e.g., "Compare to Ford F-150 Lightning pricing")
2. Specify exact deliverables: "15-slide deck," "3-page memo," "Excel model with 3 scenarios"
3. Include data sources: "Use Crunchbase for funding data," "Reference Q3 2024 10-K filings"
4. Name tools/frameworks: "Apply BCG Growth-Share Matrix," "Use Monte Carlo simulation in Excel"
5. Measurable criteria: "Interview 10+ users," "Analyze 50+ customer reviews," "Model 5-year projections"

WORKED EXAMPLE IN INSTRUCTIONS (REQUIRED - Include at least one):
Provide a SHORT worked example showing how to complete ONE step:

Example: "Step 2 Worked Example - Competitive Analysis (illustrative, hypothetical figures — students verify real ones from cited sources):
1. Product A MSRP: assume $80,000
2. Competitor B: assume $63,000 (comparable trim)
3. Competitor C: assume $73,000 (base model)
4. Price premium: A is ~27% above B, ~10% above C
5. Conclusion: A is betting on brand power to justify the premium"

Requirements for {course_name}:
- All instructions relate to {course_name}
- Use examples from {course_name} field
- Integrate Program SLO development throughout
- Show how each step develops Learning Objectives
- Use "Program SLO" and "Learning Objective" terminology

Timeline and milestones:
- Week 1: Complete Steps 1-2 (formative feedback checkpoint)
- Week 2: Complete Steps 3-4 (peer review)
- Week 3: Final deliverable with all steps

Course: {course_name}
Teaching Style: {teaching_style}
Program: {program_type}
SLO Context: {slo_context}

Include resources: Specific articles (with authors/dates), databases, tools, templates
{context_suffix}"""
}

# Grading Rubric Generation Prompts
RUBRIC_PROMPTS = {
    "rubric_main": """Create detailed rubric section for {course_name} criterion: {topic}

{complexity_instructions}

CRITICAL: Use OBSERVABLE, MEASURABLE performance indicators at each level.

PERFORMANCE LEVEL REQUIREMENTS:
- Avoid vague terms: "good," "adequate," "satisfactory," "demonstrates understanding"
- Use specific counts: "Identifies 5+ factors," "Cites 8+ sources," "Analyzes 3+ alternatives"
- Include concrete actions: "Calculates NPV using 10% discount rate," "Interviews 12+ customers"
- Reference specific tools/methods: "Applies Porter's Five Forces completely," "Uses DCF model with 3 scenarios"

FORMAT (use this table structure):

CRITERION: {topic} (XX points)

| Level | Score | Performance Indicators | Example |
|-------|-------|----------------------|---------|
| **Exemplary** | 18-20 | • Identifies 7+ competitive factors with data<br>• Analyzes 4+ strategic alternatives<br>• Uses 3+ analytical frameworks correctly<br>• Provides specific recommendations with metrics | Student analyzes Tesla's pricing using Porter's Five Forces + BCG Matrix + SWOT, calculates price elasticity using 2023-2024 data, recommends $74,990 price point with 15% margin justification |
| **Proficient** | 15-17 | • Identifies 5-6 factors with some data<br>• Analyzes 3 alternatives<br>• Uses 2 frameworks correctly<br>• Recommendations with basic justification | Student applies Porter's Five Forces + SWOT, compares 3 competitors, recommends price range with margin calculation |
| **Developing** | 12-14 | • Identifies 3-4 factors, limited data<br>• Analyzes 2 alternatives<br>• Uses 1 framework partially<br>• Recommendations lack specifics | Student lists competitive factors, mentions 2 alternatives, attempts one framework, makes general recommendation |
| **Beginning** | 0-11 | • Identifies <3 factors<br>• Lists alternatives without analysis<br>• No frameworks used<br>• No clear recommendation | Student provides generic competitor list, no analysis or frameworks applied |

COMMON MISTAKES TO HIGHLIGHT (include 2-3 per criterion):
- "Confuses correlation with causation when analyzing market data"
- "Applies SWOT without connecting to strategy"
- "Uses 2023 data when 2024 Q3 earnings are available"

SLO ASSESSMENT ALIGNMENT:
- Map this criterion to 2-3 specific Program SLOs
- Explain HOW performance at each level demonstrates SLO achievement
- Use "Program SLO" and "Learning Objective" terminology

Requirements for {course_name}:
- All performance levels relate to {program_type} standards
- Include Program SLO development assessment
- Show how performance levels indicate SLO achievement
- Point values appropriate for {program_type}

Course: {course_name}
Teaching Style: {teaching_style}

The rubric should help instructors grade consistently AND help students understand exactly what excellence looks like.
{context_suffix}"""
}


def get_default_prompt(category: str, prompt_name: str) -> str:
    """Get default prompt by category and name."""
    prompts = {
        'syllabus': SYLLABUS_PROMPTS,
        'lecture': LECTURE_PROMPTS,
        'assignment': ASSIGNMENT_PROMPTS,
        'rubric': RUBRIC_PROMPTS
    }
    
    if category not in prompts:
        raise ValueError(f"Unknown category: {category}")
    
    if prompt_name not in prompts[category]:
        raise ValueError(f"Unknown prompt: {prompt_name} in category {category}")
    
    return prompts[category][prompt_name]


def get_all_prompts_for_category(category: str) -> dict:
    """Get all prompts for a category."""
    prompts = {
        'syllabus': SYLLABUS_PROMPTS,
        'lecture': LECTURE_PROMPTS,
        'assignment': ASSIGNMENT_PROMPTS,
        'rubric': RUBRIC_PROMPTS
    }
    
    if category not in prompts:
        raise ValueError(f"Unknown category: {category}")
    
    return prompts[category]


def validate_prompt(prompt: str) -> tuple[bool, str]:
    """Validate a prompt template."""
    if not prompt or not prompt.strip():
        return False, "Prompt cannot be empty"
    
    if len(prompt) < 10:
        return False, "Prompt is too short"
    
    return True, "Valid"


def get_prompt_categories() -> list:
    """Get list of available prompt categories."""
    return ['syllabus', 'lecture', 'assignment', 'rubric']