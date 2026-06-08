"""
Configuration and Data Models
Defines all enums, data classes, and configuration settings for the course builder.
Keeps all data structures in one place for easy maintenance.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime

# ============= Enums =============

class BloomLevel(str, Enum):
    """Bloom's Taxonomy cognitive levels - hidden from frontend but used internally"""
    REMEMBER = "Remember (Recall facts and basic concepts)"
    UNDERSTAND = "Understand (Explain ideas or concepts)"
    APPLY = "Apply (Use information in new situations)"
    ANALYZE = "Analyze (Draw connections among ideas)"
    EVALUATE = "Evaluate (Justify a stand or decision)"
    CREATE = "Create (Produce new or original work)"

class TeachingStyle(str, Enum):
    """Different pedagogical approaches for course design"""
    HANDS_ON = "Hands-on / Experiential"
    RESEARCH_HEAVY = "Research-heavy / Academic"
    DISCUSSION_BASED = "Discussion-based / Socratic"
    CASE_STUDY = "Case Study / Problem-based"
    PROJECT_BASED = "Project-based / Applied"
    LECTURE_FOCUSED = "Lecture-focused / Traditional"

class AssessmentStyle(str, Enum):
    """Assessment and evaluation methods"""
    MCQ = "Multiple Choice Questions"
    ESSAY = "Essay Questions"
    CASE_STUDY = "Case Study Analysis"
    PROJECT = "Project-based Assessment"
    PRESENTATION = "Oral Presentations"
    PORTFOLIO = "Portfolio Assessment"
    PRACTICAL = "Practical Exercises"
    PEER_REVIEW = "Peer Review Activities"

class LectureFormat(str, Enum):
    """Lecture content generation formats"""
    NOTES = "Generate as Notes"
    AI_SCRIPT = "Generate as AI Script"

class ProgramType(str, Enum):
    """Academic program types"""
    UNDERGRADUATE = "Undergraduate"
    RESIDENTIAL_MBA = "Residential MBA"
    KELLEY_DIRECT = "Kelley Direct"

class ModelType(str, Enum):
    """Available AI models for content generation"""
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_4O = "gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"
    CLAUDE_SONNET = "claude-sonnet-3-5"
    GEMINI_PRO = "gemini-pro"
    

class AIClassroomUse(str, Enum):
    """AI use policies for classroom"""
    PROHIBITIVE = "Prohibitive"
    CONDITIONAL = "Conditional" 
    PERMISSIVE = "Permissive"

class SuggestionGranularity(str, Enum):
    """Granularity levels for AI actionable suggestions"""
    HIGH_LEVEL = "High-level (Broad structural guidance)"
    MEDIUM_LEVEL = "Medium-level (Section/topic feedback)"
    FINE_GRAINED = "Fine-grained (Detailed content improvements)"

MAX_SYLLABUS_VERSIONS = 3
# ============= Data Classes =============

@dataclass
class CustomSLO:
    """Custom Student Learning Outcome"""
    title: str
    content: str
    bloom_level: str = ""
    assessment_method: str = ""

@dataclass
class CourseContext:
    """Complete course information and preferences"""
    course_code: str
    course_name: str
    program_type: str
    semester: str
    weeks: int
    professor_name: str
    professor_email: str
    office_location: str
    office_hours: str
    selected_slos: List[Dict]
    custom_slos: List[CustomSLO]
    teaching_style: str
    assessment_preferences: List[str]
    bloom_levels: List[str]
    ai_classroom_use: str
    sessions_per_week: int
    duration_per_session: int

@dataclass
class GeneratedContent:
    """Container for AI-generated content with metadata"""
    content: str
    rationale: str
    quality_score: float
    suggestions: List[str]
    version: int
    timestamp: datetime
    schedule_metadata: Optional[List[Dict]] = None
    suggestion_history: Optional[List[Dict]] = None

@dataclass
class ContentVersion:
    """Version tracking for content iterations"""
    version_number: int
    content: str
    feedback: str
    approved: bool
    timestamp: datetime

# ============= Configuration Settings =============

# Program-specific SLOs - Exact wording as provided
KELLEY_DIRECT_SLOS = [
    {"code": "KD-1.1", "description": "Identify and analyze a business problem through the lens of any given functional area"},
    {"code": "KD-1.2", "description": "Show how actions in one business functional area affect the operations of other functional areas"},
    {"code": "KD-1.3", "description": "Analyze and solve a business problem involving two or more functional areas"},
    {"code": "KD-1.4", "description": "Assess capabilities and deficiencies of a firm from various functional perspectives"},
    {"code": "KD-2.1", "description": "Describe how an external force (e.g. taxes, regulations, competition) relates to the functional areas of a firm"},
    {"code": "KD-2.2", "description": "Describe how firm policy choices affect external stakeholders (e.g., customers, society)"},
    {"code": "KD-2.3", "description": "Analyze an external strategic problem facing a firm in order to recommend a sound solution to management"},
    {"code": "KD-2.4", "description": "Analyze the fit between the internal structure of the firm and the external environment"},
    {"code": "KD-3.1", "description": "Identify the most appropriate tools or frameworks to solve a given business problem"},
    {"code": "KD-3.2", "description": "Explain how a given decision or intervention affects each of the key functional areas of a firm"},
    {"code": "KD-3.3", "description": "Apply analytical tools and techniques from more than one functional area to address a problem or case"},
    {"code": "KD-4.1", "description": "Articulate ideas, thoughts, recommendations, and other communications clearly, concisely, and persuasively to business audiences"},
    {"code": "KD-4.2", "description": "Respond appropriately to feedback, demonstrating emotional intelligence"},
    {"code": "KD-4.3", "description": "Work effectively with others to complete projects or other work"},
    {"code": "KD-5.1", "description": "Identify ethical implications in a given business problem"},
    {"code": "KD-5.2", "description": "Apply systematic reasoning to make decisions where ethics are concerned"},
    {"code": "KD-5.3", "description": "Identify legal issues in a given business situation"},
    {"code": "KD-5.4", "description": "Defend business decisions with respect to legal considerations"},
    {"code": "KD-6.1", "description": "Explain the value of Diversity, Equity, or Inclusion for external stakeholders and its implication for firm strategy"},
    {"code": "KD-6.2", "description": "Explain the value of Diversity, Equity, or Inclusion for internal management of a firm or organization"}
]

RESIDENTIAL_MBA_SLOS = [
    {"code": "MBA-1.1", "description": "Identify and analyze a business problem through the lens of any given functional area"},
    {"code": "MBA-1.2", "description": "Show how actions in one business functional area affect the operations of other functional areas"},
    {"code": "MBA-1.3", "description": "Analyze and solve a business problem involving two or more functional areas"},
    {"code": "MBA-1.4", "description": "Assess capabilities and deficiencies of a firm from various functional perspectives"},
    {"code": "MBA-2.1", "description": "Describe how an external force (e.g. taxes, regulations, competition) relates to the functional areas of a firm"},
    {"code": "MBA-2.2", "description": "Describe how firm policy choices affect external stakeholders (e.g., customers, society)"},
    {"code": "MBA-2.3", "description": "Analyze an external strategic problem facing a firm in order to recommend a sound solution to management"},
    {"code": "MBA-2.4", "description": "Analyze the fit between the internal structure of the firm and the external environment"},
    {"code": "MBA-3.1", "description": "Identify the most appropriate tools or frameworks to solve a given business problem"},
    {"code": "MBA-3.2", "description": "Explain how a given decision or intervention affects each of the key functional areas of a firm"},
    {"code": "MBA-3.3", "description": "Apply analytical tools and techniques from more than one functional area to address a problem or case"},
    {"code": "MBA-4.1", "description": "Articulate ideas, thoughts, recommendations, and other communications clearly, concisely, and persuasively to business audiences"},
    {"code": "MBA-4.2", "description": "Respond appropriately to feedback, demonstrating emotional intelligence"},
    {"code": "MBA-4.3", "description": "Work effectively with others to complete projects or other work"},
    {"code": "MBA-5.1", "description": "Identify ethical implications in a given business problem"},
    {"code": "MBA-5.2", "description": "Apply systematic reasoning to make decisions where ethics are concerned"},
    {"code": "MBA-5.3", "description": "Identify legal issues in a given business situation"},
    {"code": "MBA-5.4", "description": "Defend business decisions with respect to legal considerations"},
    {"code": "MBA-6.1", "description": "Explain the value of Diversity, Equity, or Inclusion for external stakeholders and its implication for firm strategy"},
    {"code": "MBA-6.2", "description": "Explain the value of Diversity, Equity, or Inclusion for internal management of a firm or organization"}
]

UNDERGRADUATE_SLOS = [
    {"code": "UG-1.1", "description": "Identify the relationships between two or more business functions; explain how actions in one functional area affect other functional areas"},
    {"code": "UG-1.2", "description": "Describe how the relationships among the functional areas relate to the goals of the organization"},
    {"code": "UG-1.3", "description": "Use integrative techniques, structures, or frameworks to make business decisions"},
    {"code": "UG-2.1", "description": "Identify the ethical dimension(s) of a business decision"},
    {"code": "UG-2.2", "description": "Recognize the tradeoffs created by application of competing ethical theories and perspectives"},
    {"code": "UG-2.3", "description": "Formulate and defend a well-supported recommendation for the resolution of an ethical issue"},
    {"code": "UG-3.1", "description": "Recognize the implications of a proposed decision from a variety of diverse stakeholder perspectives"},
    {"code": "UG-3.2", "description": "Evaluate the integrity of the supporting evidence and data for a given decision"},
    {"code": "UG-3.3", "description": "Analyze a given decision using critical techniques, structures, or frameworks"},
    {"code": "UG-4.1", "description": "Deliver clear, concise, and audience-centered individual and team presentations"},
    {"code": "UG-4.2", "description": "Write clear, concise, and audience-centered business documents"},
    {"code": "UG-4.3", "description": "Effectively participate in informational and employment interviews"},
    {"code": "UG-4.4", "description": "Articulate one's unique value proposition to a given audience"},
    {"code": "UG-5.1", "description": "Use appropriate technology to solve a given business problem"},
    {"code": "UG-5.2", "description": "Analyze business problems using appropriate mathematical theories and techniques"},
    {"code": "UG-5.3", "description": "Explain the role of technologies in business decision making analysis, or modeling"},
    {"code": "UG-5.4", "description": "Structure logic and frame quantitative analysis to solve business problems"},
    {"code": "UG-6.1", "description": "Participate actively in team meetings and collaborate effectively in both face-to-face and virtual interactions"},
    {"code": "UG-6.2", "description": "Create a cohesive and integrated team deliverable"},
    {"code": "UG-6.3", "description": "Assess individual or team collaboration with respect to both productivity and interpersonal relationships"},
    {"code": "UG-6.4", "description": "Identify and manage behaviors related to biases and assumptions to build trust with colleagues that have different backgrounds and perspectives"},
    {"code": "UG-7.1", "description": "Identify the risks and opportunities associated with determining and implementing optimal global business strategies"},
    {"code": "UG-7.2", "description": "Integrate international, regional, and local non-market forces into strategic decisions of multinational corporations"},
    {"code": "UG-7.3", "description": "Analyze obstacles resulting from cultural differences and recommend leadership approaches that leverage diversity to enhance business performance"},
    {"code": "UG-7.4", "description": "Identify the personal and contrasting attitudes, values, and beliefs that shape business relationships"}
]

def get_program_slos(program_type: str) -> List[Dict[str, str]]:
    """Get all SLOs for specific program type"""
    slo_mapping = {
        ProgramType.UNDERGRADUATE.value: UNDERGRADUATE_SLOS,
        ProgramType.RESIDENTIAL_MBA.value: RESIDENTIAL_MBA_SLOS,
        ProgramType.KELLEY_DIRECT.value: KELLEY_DIRECT_SLOS
    }
    return slo_mapping.get(program_type, RESIDENTIAL_MBA_SLOS)

def get_all_course_slos(course_context: CourseContext) -> List[Dict[str, str]]:
    """
    Get combined list of selected program SLOs and custom SLOs.
    Custom SLOs are added after program-specific SLOs.
    """
    all_slos = []
    
    # Add selected program SLOs first
    all_slos.extend(course_context.selected_slos)
    
    # Add custom SLOs after program SLOs
    for custom_slo in course_context.custom_slos:
        all_slos.append({
            "code": custom_slo.title,
            "description": custom_slo.content
        })
    
    return all_slos

# Bloom's taxonomy mapping based on teaching style
BLOOM_MAPPING = {
    TeachingStyle.HANDS_ON.value: [BloomLevel.APPLY.value, BloomLevel.ANALYZE.value, BloomLevel.CREATE.value],
    TeachingStyle.RESEARCH_HEAVY.value: [BloomLevel.ANALYZE.value, BloomLevel.EVALUATE.value, BloomLevel.CREATE.value],
    TeachingStyle.DISCUSSION_BASED.value: [BloomLevel.UNDERSTAND.value, BloomLevel.ANALYZE.value, BloomLevel.EVALUATE.value],
    TeachingStyle.CASE_STUDY.value: [BloomLevel.APPLY.value, BloomLevel.ANALYZE.value, BloomLevel.EVALUATE.value],
    TeachingStyle.PROJECT_BASED.value: [BloomLevel.APPLY.value, BloomLevel.ANALYZE.value, BloomLevel.CREATE.value],
    TeachingStyle.LECTURE_FOCUSED.value: [BloomLevel.REMEMBER.value, BloomLevel.UNDERSTAND.value, BloomLevel.APPLY.value]
}

# Default assessment preferences
DEFAULT_ASSESSMENTS = [AssessmentStyle.CASE_STUDY.value, AssessmentStyle.PROJECT.value]

# Quality thresholds
QA_PASS_THRESHOLD = 80
QA_EXCELLENT_THRESHOLD = 90

# ============= AI CLASSROOM USE POLICY TEXTS =============

AI_POLICY_TEXTS = {
    AIClassroomUse.PROHIBITIVE.value: """

### AI USE POLICY - PROHIBITIVE

In this course, the use of generative artificial intelligence (AI) in completing assignments is strictly prohibited.

The primary reason for this prohibition is to ensure that the learning process remains authentic and personal. Generative AI, while impressive in its capabilities, can inadvertently hinder the development of critical thinking and problem-solving skills. These skills are best cultivated through active engagement with the course material and hands-on problem solving. Relying on AI to generate responses or solutions can create a passive learning environment and may prevent you from fully understanding the concepts being taught.

Remember, the goal of education is not just about getting the right answers but understanding the process of how to arrive at those answers. Therefore, it's essential that all work submitted for this course is your own, reflecting your understanding and application of the course material.

Kelley students are expected to adhere to the Kelley Student Honor Code (https://kelley.iu.edu/programs/undergrad/academics/honor-code.html) which includes an emphasis on Integrity as a key value. In this course, the use of generative AI to complete assignments will be considered plagiarism which is a violation of both the Kelley Student Honor Code and the IU Student Code of Conduct. https://studentcode.iu.edu/responsibilities/academic-misconduct.html

"Plagiarism: Plagiarism is defined as presenting someone else's work, including the work of other students, as the submitting student's own. A student must not present ideas or materials taken from another source for either written or oral use without fully acknowledging the source, unless the information is common knowledge. What is considered "common knowledge" may differ from course to course."

""",

    AIClassroomUse.CONDITIONAL.value: """

### AI USE POLICY - CONDITIONAL

In this course, the use of generative artificial intelligence (AI) is permitted, but only for specified assignments and in specified ways. This allowance is designed to provide you with an opportunity to explore the capabilities of AI and understand its potential benefits and limitations. However, it's important to note that the use of AI should not replace your own critical thinking and problem-solving skills. Each assignment in the course will have a clear designation regarding whether the use of AI is permissible or not. For the assignments where AI is allowed, clear guidelines will be provided on how it should be used. Any deviation from these guidelines may result in the assignment being marked down or, if egregious, considered plagiarism and Academic Misconduct. Remember, the goal is not to have AI do the work for you, but to use it as a tool to enhance your own learning and understanding.

Importantly when AI usage is permissible, you should understand that all large language models tend to make up incorrect facts and fake citations. They may perpetuate biases, and image generation models can occasionally come up with offensive results. You will be responsible for any inaccurate, biased, offensive, or otherwise unethical content you submit.

""",

    AIClassroomUse.PERMISSIVE.value: """

### AI USE POLICY - PERMISSIVE

In this course, we encourage the use of generative artificial intelligence (AI) as a tool to assist in your learning process. You are welcome to use AI in all aspects of the course, from research to data analysis, and even for generating ideas for creative assignments. However, it's important to note that while AI can be a valuable tool, any work produced by AI should not be presented as your own. Always acknowledge the use of AI in your assignments and cite it appropriately. The goal is to use AI as a supplement to your own critical thinking and problem-solving skills, not as a replacement. Remember, the purpose of education is to enhance your own understanding and abilities, and AI is just one of many tools you can use to achieve this.

Importantly, you should understand that all large language models tend to make up incorrect facts and fake citations. They may perpetuate biases, and image generation models can occasionally come up with offensive results. You will be responsible for any inaccurate, biased, offensive, or unethical content you submit.

When using AI in your assignments, it's important to properly cite its use to maintain academic integrity. Here are some general guidelines for citing AI in a variety of learning situations:

1. Data Analysis: If you're using AI to analyze data, mention the specific AI tool used and describe its role in your analysis. For example, "Data analysis was performed using [AI tool], which helped identify patterns and trends in the dataset."

2. Research: If AI was used to gather resources or provide summaries, cite the AI tool as you would any other source. For example, "Preliminary research was conducted using [AI tool], which provided a comprehensive overview of the topic."

3. Creativity Enhancement: If you used AI for inspiration in a creative assignment, acknowledge its contribution. For example, "Ideas generated by [AI tool] were used as a starting point for this piece."

4. Language Translation: If you used AI for translation, mention the tool and the languages translated. For example, "Translations in this assignment were provided by [AI tool], translating from [language A] to [language B]."

5. Coding Assistance: If AI provided code suggestions or bug detection, acknowledge its use. For example, "Code suggestions and bug detection were provided by [AI tool], aiding in the development of the final program."

6. MLA Citations: The MLA handbook has been updated to include citations to AI for situations where MLA style is utilized.

Remember, the goal is not to hide the use of AI, but to transparently acknowledge its role in your work. This maintains academic integrity and allows for a clear understanding of your process.
"""
}


def get_ai_policy_text(ai_classroom_use: str) -> str:
    """Get AI policy text for the selected classroom use type"""
    return AI_POLICY_TEXTS.get(ai_classroom_use, "")

# ============= MANDATORY APPENDIX SYSTEM =============

GRADUATE_APPENDIX = """

**ACADEMIC MISCONDUCT:**  The vast majority of IU and Kelley students act honestly and with integrity in
their personal lives and in class. Unfortunately, each year a small group of students deviate from those
values and (either intentionally or unintentionally) engage in academic misconduct. Please do not find
yourself among that group.

To avoid academic misconduct, you are responsible for knowing and complying with the responsibilities
and duties set forth in your graduate program's Code of Conduct, the revised (2023) Indiana University
Code of Student Rights, Responsibilities, and Conduct, and any other Kelley or IU rules and
regulation about academic misconduct. In the event you commit an act of academic misconduct, an
appropriate sanction will be imposed, and the misconduct will be reported to Indiana University.
Sanctions could include a grade of F for the class.

Note that academic misconduct includes plagiarism, even if unintentional. Hence, be sure to carefully
review the definition of plagiarism found in the IU Code. Additionally, sharing (including uploading) past
or current quizzes, tests, or homework assignments from this class with each other (unless specifically
authorized by assignment, test, or quiz instructions) or via unauthorized sources, including third party
websites such as Chegg, is against course rules and constitutes academic misconduct, even when the
intent is not to enhance one's personal grade. Likewise, accessing (including downloading) past or
current quizzes, tests, or homework assignments via unauthorized sources, including third party
websites such as Chegg, or using ChatGPT or other LLMs unless explicitly authorized, is also against
course rules and constitutes academic misconduct.

If I determine that you have committed academic misconduct, I will notify you by meeting with you and
explaining the basis for my determination. I may also consult with the program Conduct Review
Committee. Then, I will report the misconduct to the University, as I am required to do. If you are the
subject of a report of misconduct that you believe is inaccurate or if you believe that an imposed
sanction is inappropriate, you have a right to appeal the finding of misconduct and/or the sanction.
Appeals are initiated by emailing ksappeal@indiana.edu.

**EARLY ALERT WARNINGS (EAWs):** In this course the instructor wants to make sure you connect with
resources that will help you be successful. If you receive a message through the Student Engagement
Roster that asks you to consult with your advisor, please know that the message is sent to both you and
your academic advisor, who will follow up and view the feedback from this course.
ACCOMMODATION FOR RELIGIOUS OBSERVANCES: Students missing class for a religious observance
must fill out the accommodation form on the Vice Provost for Faculty and Academic Affairs webpage at
least two weeks before your anticipated absence.

**ACCESSIBILITY, ACCOMMODATION & PREGNANCY:** Indiana University is dedicated to ensuring that
students with disabilities have the support services and reasonable accommodations needed to provide
equal access to academic programs. To request an accommodation, you must establish your eligibility by
working with Accessible Educational Services (AES) on your campus (Bloomington Campus AES email is
iubaes@iu.edu). Additional information can be found at accessibility.iu.edu. Note that services are
confidential, may take time to put into place, and are not retroactive; captions and alternate media for 
print materials may take three or more weeks to get produced. Please contact your campus AES office
as soon as possible if accommodations are needed.

Additionally, IU is dedicated to supporting students who are pregnant or have experienced other
conditions related to pregnancy (termination of pregnancy, miscarriage, lactation, or related medical
conditions). To register for accommodations due to pregnancy or a related medical condition, please
contact our campus Accessible Educational Services (AES) office.

To learn about the rights and resources available to students, such as academic accommodations, please
visit pregnancy.iu.edu or email ocrc@iu.edu for more information.

**MENTAL HEALTH AND STRESS MANAGEMENT AT KELLEY AND IU:** As a student, you may experience a
range of issues that can cause barriers to learning, such as difficulties with mental health, including
increased anxiety (feeling irritable, restless, or overwhelmed), difficulty concentrating or managing your
time. Or you may find that you feel sad or "empty," less interested in activities you once enjoyed;
inadequate compared to others; or even hopeless. These mental health concerns could lead to
diminished academic performance, drug/alcohol misuse, strained relationships, and/or a reduced ability
to participate in daily activities. The moment you experience any of these, we are here to support you.
The Kelley School of Business and Indiana University encourage you to reach out. Here are some
resources to help:

• If your mental health or stress is affecting this class in particular, reach out to me via e-mail or
office hours. I can work with you and direct you to support resources.
• Indiana University Counseling and Psychological Services (CAPS) is available to assist you. You
can learn more about the broad range of confidential mental health services available on
campus via the CAPS website (http://healthcenter.indiana.edu/counseling/).

• You have access to TimelyCare services 365 days a year (timelycare.com/IU), which is a tool with
24/7 virtual access to mental health care professionals. That means you have access during
breaks, after-hours, and any time you need support.

• A Care Referral is another easy way to request help with an issue or concern, especially if you do
not know which office or department to contact. You can submit a Care Referral for yourself or
another related to academic/administrative, personal, health/wellness, behavioral, or bias
issues. File a report at https://studentlife.indiana.edu/care-advocacy/care-and-resourcecenter/submit-care-referral.html

**SEXUAL MISCONDUCT & TITLE IX:** As your instructor, one of my responsibilities is to create a positive
learning environment for all students. IU policy prohibits sexual misconduct in any form, including sexual
harassment, sexual assault, stalking, sexual exploitation, and dating and domestic violence. If you have
experienced sexual misconduct, or know someone who has, the University can help. If you are seeking
help and would like to speak to someone confidentially, you can contact IU Sexual Assault Crisis Services
at (812) 855-8900, or contact a Confidential Victim Advocate at (812) 856-2469 or cva@iu.edu.
Additionally, Indiana University also prohibits discrimination. See the university's Non-Discrimination
policy here: https://policies.iu.edu/policies/ua-01-non-discrimination/index.html

It is also important that you know that because of my role, University policy requires me to share
information brought to my attention about potential sexual misconduct. In that event, you may be
contacted with information about resources and your options for any next steps. Protecting student
privacy is of utmost concern, and information will only be shared with those who need to know to 
ensure the university can respond and assist. I encourage you to visit stopsexualviolence.iu.edu and
ocrc.iu.edu to learn more.

If you feel like you have experienced discrimination, harassment, or sexual misconduct and wish to make
a report, please use the online form available through the Office of Civil Rights Compliance.
https://ocrc.iu.edu/report-incident/index.html

**BIAS INCIDENT REPORTING:** Bias-based incident reports can be made by students, faculty, and staff. Any
act of discrimination or harassment based on race, ethnicity, religious affiliation, gender, gender
identity, sexual orientation or disability can be reported through any of the options: 1) fill out an online
report at https://reportincident.iu.edu/; 2) call the Dean of Students Office at (812) 855-8187. Reports
can be made anonymously at https://reportincident.iu.edu.

**KELLEY BIAS INCIDENT SUPPORT OMBUDSPERSON (KBISO):** You may experience or witness a bias or
discrimination incident or an incident that you are unsure how to interpret. We understand that
reporting an incident and/or navigating the University or Kelley School processes and offices that are
available to support you can feel daunting at times. Professor Sheri Walter is the Kelley Bias Incident
Support Ombudsperson (KBISO), a resource available to all graduate students. In this role, Professor
Walter will provide safe and confidential support so that students feel respected and heard when
considering how to navigate incidents of bias or discrimination. She can help students evaluate and
select among a variety of options to address incidents of bias or discriminationâ€”including answering
students' questions about how to report incidents of bias or discriminationâ€”or help find others who can
answer students' questions. She can make appropriate referrals for filing University-level reports of bias
or discrimination and advise students about informal and formal resolution techniques to address
current or future incidents of bias or discrimination. In this role, Professor Walter will not give legal
advice. She will not investigate claims or participate in formal grievance processes, hearings, or judicial
processes. She will not make administrative or academic decisions for the School or University. Instead,
she will listen intently and discuss conflicts, disputes, concerns, and complaints that students have about
unfair treatment or actions stemming from bias or discrimination on the part of other students, faculty
and/or staff. The purpose of this role is student support. If you need support or direction related to an
incident of bias or discrimination, please contact Professor Walter at sherwalt@iu.edu.

**UNAUTHORIZED USE, SALE, OR DISTRIBUTION OF COURSE MATERIAL AND CONTENT:** The course
instructor holds the exclusive right to distribute, modify, post, and reproduce any course materials
created for this course, including written materials, study guides, lectures, assignments, exercises, and
exams. Commercial tutoring services and/or online platforms may offer students something of value
(money, access to materials for other courses, etc.) for sharing materials from this course. Doing so is a
violation of the instructor's intellectual property rights and may violate related University policies.
In addition, some online course content, including recorded lectures and/or recordings of class sessions
may be made available to you to view and download. While you can take notes on such content for your
personal use, you are not permitted to distribute or re-post such content either in its original or altered
form without the instructor's written permission.
Finally, you may not record, capture, or photograph class sessions (whether in person or online) without
the instructor's express written permission.

Violation of course rules involving unauthorized or improper use, sale, or distribution of course material
and content as outlined above is an act academic misconduct under the IU Code of Student Rights,
Responsibilities, and Conduct and will subject students who do so to disciplinary sanctions.
"""

UNDERGRADUATE_APPENDIX = """

**ACADEMIC MISCONDUCT:** The vast majority of IU and Kelley students act honestly and with integrity in
their personal lives and in class. Indeed, integrity and accountability are fundamental values of the
Kelley School of Business undergraduate program. To avoid academic misconduct, you must know and
comply with the responsibilities and duties set forth in the Kelley School of Business Student Honor
Code, the Indiana University Code of Student Rights, Responsibilities, and Conduct, and any other Kelley
or IU rules and regulations about academic misconduct. In the event you commit an act of academic
misconduct, an appropriate sanction will be imposed, and the misconduct will be reported to Indiana
University. Sanctions could include a grade of F for the class.

Note that academic misconduct includes plagiarism, even if unintentional. Be sure to carefully review
the definition of plagiarism found in the IU Code. Additionally, sharing (including uploading) past or
current quizzes, tests, or homework assignments from this class with each other (unless specifically
authorized by assignment, test, or quiz instructions) or via unauthorized sources, including third-party
websites such as Chegg, is against course rules and constitutes academic misconduct, even if your intent
is not to enhance your performance or grade in this class. Likewise, accessing (including downloading)
past or current quizzes, tests, or homework assignments via unauthorized sources, including third party
websites such as Chegg, or using ChatGPT or other LLMs unless explicitly authorized, is also against
course rules and constitutes academic misconduct.

If I determine that you have committed academic misconduct, I will notify you by meeting with you and
explaining the basis for my determination. Then, I will report it to the University, as I am required to do.
If you are the subject of a report of misconduct that you believe is inaccurate or if you believe that an
imposed sanction is inappropriate, you have a right to appeal the finding of misconduct and/or the
sanction. You will be notified by the Dean of Students' Office of Student Conduct about your appeal
rights. Questions regarding an appeal of an academic misconduct charge can be e-mailed to
ksappeal@indiana.edu. You can find more details here: Academic Misconduct Procedures - Kelley School
of Business

**EARLY ALERT WARNINGS (EAWs):** In this course the instructor wants to make sure you connect with
resources that will help you be successful. If you receive a message through the Student Engagement
Roster that asks you to consult with your advisor, please know that the message is sent to both you and
your academic advisor, who will follow up and view the feedback from this course.
ACCOMMODATION FOR RELIGIOUS OBSERVANCES: Students missing class for a religious observance
must fill out the accommodation form on the Vice Provost for Faculty and Academic Affairs webpage at
least two weeks before your anticipated absence.

**ACCESSIBILITY, ACCOMMODATION & PREGNANCY:** Indiana University is dedicated to ensuring that
students with disabilities have the support services and reasonable accommodations needed to provide
equal access to academic programs. To request an accommodation, you must establish your eligibility by
working with Accessible Educational Services (AES) on your campus (Bloomington Campus AES email is
iubaes@iu.edu). Additional information can be found at accessibility.iu.edu. Note that services are
confidential, may take time to put into place, and are not retroactive; captions and alternate media for
print materials may take three or more weeks to get produced. Please contact your campus AES office
as soon as possible if accommodations are needed. 

Additionally, IU is dedicated to supporting students who are pregnant or have experienced other
conditions related to pregnancy (termination of pregnancy, miscarriage, lactation, or related medical
conditions). To register for accommodations due to pregnancy or a related medical condition, please
contact our campus Accessible Educational Services (AES) office.

To learn about the rights and resources available to students, such as academic accommodations, please
visit pregnancy.iu.edu or email ocrc@iu.edu for more information.

**MENTAL HEALTH AND STRESS MANAGEMENT AT KELLEY AND IU:** As a student, you may experience a
range of issues that can cause barriers to learning, such as difficulties with mental health, including
increased anxiety (feeling irritable, restless, or overwhelmed), difficulty concentrating or managing your
time. Or you may find that you feel sad or "empty," less interested in activities you once enjoyed;
inadequate compared to others; or even hopeless. These mental health concerns could lead to
diminished academic performance, drug/alcohol misuse, strained relationships, and/or a reduced ability
to participate in daily activities. The moment you experience any of these, we are here to support you.
The Kelley School of Business and Indiana University encourage you to reach out. Here are some
resources to help:

• If your mental health or stress is affecting this class, reach out to me via e-mail or office hours. I
can work with you and direct you to support resources.
• If you are not sure where to start or what you need, meet with Kelley Student Support. With
them, you can discuss individual needs/support, organizational consultation, or ideas in the
areas of mental health and wellness, women's, and LGBTQ+ initiatives. To sign up for a time to
meet, go to https://gokelley.iu.edu/studentsupportsignup.

• Indiana University Counseling and Psychological Services (CAPS) is available to assist you. You
can learn more about the broad range of confidential mental health services available on
campus via the CAPS website (http://healthcenter.indiana.edu/counseling/).

• You have access to TimelyCare services 365 days a year (timelycare.com/IU), which is a tool with
24/7 virtual access to mental health care professionals. That means you have access during
breaks, after-hours, and any time you need support.

• A Care Referral is another easy way to request help with an issue or concern, especially if you do
not know which office or department to contact. You can submit a Care Referral for yourself or
another related to academic/administrative, personal, health/wellness, behavioral, or bias
issues. File a report at https://studentlife.indiana.edu/care-advocacy/care-and-resourcecenter/submit-care-referral.html

**SEXUAL MISCONDUCT & TITLE IX:** As your instructor, one of my responsibilities is to create a positive
learning environment for all students. IU policy prohibits sexual misconduct in any form, including sexual
harassment, sexual assault, stalking, sexual exploitation, and dating and domestic violence. If you have
experienced sexual misconduct, or know someone who has, the University can help. If you are seeking
help and would like to speak to someone confidentially, you can contact IU Sexual Assault Crisis Services
at (812) 855-8900, or contact a Confidential Victim Advocate at (812) 856-2469 or cva@iu.edu.
Additionally, Indiana University also prohibits discrimination. See the university's Non-Discrimination
policy here: https://policies.iu.edu/policies/ua-01-non-discrimination/index.html
It is also important that you know that because of my role, University policy requires me to share
information brought to my attention about potential sexual misconduct. In that event, you may be
contacted with information about resources and your options for any next steps. Protecting student 
privacy is of utmost concern, and information will only be shared with those who need to know to
ensure the university can respond and assist. I encourage you to visit stopsexualviolence.iu.edu and
ocrc.iu.edu to learn more.

If you feel like you have experienced discrimination, harassment, or sexual misconduct and wish to make
a report, please use the online form available through the Office of Civil Rights Compliance.
https://ocrc.iu.edu/report-incident/index.html

**BIAS INCIDENT REPORTING:** Bias-based incident reports can be made by students, faculty, and staff. Any
act of discrimination or harassment based on race, ethnicity, religious affiliation, gender, gender
identity, sexual orientation or disability can be reported through any of the options: 1) fill out an online
report at https://reportincident.iu.edu/; 2) call the Dean of Students Office at (812) 855-8187. Reports
can be made anonymously at https://reportincident.iu.edu.

**KELLEY BIAS INCIDENT SUPPORT OMBUDSPERSON (KBISO):** You may experience or witness a bias or
discrimination incident or an incident that you are unsure how to interpret. We understand that
reporting an incident and/or navigating the University or Kelley School processes and offices that are
available to support you can feel daunting at times. Professor Stephanie Moore is the Kelley Bias
Incident Support Ombudsperson (KBISO), a resource available to all undergraduate students. In this
role, Professor Moore will provide safe and confidential support so that students feel respected and
heard when considering how to navigate incidents of bias or discrimination. She can help students
evaluate and select among a variety of options to address incidents of bias or discriminationâ€”including
answering students' questions about how to report incidents of bias or discriminationâ€”or help find
others who can answer students' questions. She can make appropriate referrals for filing Universitylevel reports of bias or discrimination and advise students about informal and formal resolution
techniques to address current or future incidents of bias or discrimination. In this role, Professor Moore
will not give legal advice. She will not investigate claims or participate in formal grievance processes,
hearings, or judicial processes. She will not make administrative or academic decisions for the School or
University. Instead, she will listen intently and discuss conflicts, disputes, concerns, and complaints that
students have about unfair treatment or actions stemming from bias or discrimination on the part of
other students, faculty and/or staff. The purpose of this role is student support. If you need support or
direction related to an incident of bias or discrimination, please contact Professor Moore in her KBISO
role at kbiso@indiana.edu.

**UNAUTHORIZED USE, SALE, OR DISTRIBUTION OF COURSE MATERIAL AND CONTENT:** The course
instructor holds the exclusive right to distribute, modify, post, and reproduce any course materials
created for this course, including written materials, study guides, lectures, assignments, exercises, and
exams. Commercial tutoring services and/or online platforms may offer students something of value
(money, access to materials for other courses, etc.) for sharing materials from this course. Doing so is a
violation of the instructor's intellectual property rights and may violate related University policies.
In addition, some online course content, including recorded lectures and/or recordings of class sessions
may be made available to you to view and download. While you can take notes on such content for your
personal use, you are not permitted to distribute or re-post such content either in its original or altered
form without the instructor's written permission.

Finally, you may not record, capture, or photograph class sessions (whether in person or online) without
the instructor's express written permission.
Violation of course rules involving unauthorized or improper use, sale, or distribution of course material
and content as outlined above is an act academic misconduct under the IU Code of Student Rights,
Responsibilities, and Conduct and will subject students who do so to disciplinary sanctions.

"""

def get_program_appendix(program_type: str) -> str:
    """Get mandatory appendix for program type"""
    if program_type == ProgramType.UNDERGRADUATE.value:
        return UNDERGRADUATE_APPENDIX
    else:  # Both MBA and Kelley Direct use graduate appendix
        return GRADUATE_APPENDIX

def auto_assign_bloom_levels(teaching_style: str) -> List[str]:
    """
    Auto-assign appropriate Bloom's taxonomy levels based on teaching style.
    Hidden from frontend but used internally for pedagogical alignment.
    """
    return BLOOM_MAPPING.get(teaching_style, [BloomLevel.APPLY.value, BloomLevel.ANALYZE.value])

def get_all_course_slos(course_context: 'CourseContext') -> List[Dict]:
    """
    Get all SLOs (selected + custom) for a course.
    
    Args:
        course_context: Course context with selected and custom SLOs
        
    Returns:
        List of all SLO dictionaries
    """
    all_slos = []
    
    # Add selected program SLOs
    if course_context.selected_slos:
        all_slos.extend(course_context.selected_slos)
    
    # Add custom SLOs converted to dict format
    if course_context.custom_slos:
        for custom_slo in course_context.custom_slos:
            all_slos.append({
                'code': custom_slo.title,
                'description': custom_slo.content
            })
    
    return all_slos
