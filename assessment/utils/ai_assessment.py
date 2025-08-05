# # ai_assessment.py
# from langchain.vectorstores import FAISS
# from langchain.embeddings import OpenAIEmbeddings
# from langchain.chat_models import ChatOpenAI
# from langchain.chains import RetrievalQA
# from langchain.schema import SystemMessage, HumanMessage
# from .rag_utils import load_or_create_vectorstore
# from typing import List
# import openai
# import os
# import re
# import json
# from django.utils import timezone

# MAX_QUESTIONS = 3

# openai.api_key = os.getenv("OPENAI_API_KEY")  # Or use a hardcoded key temporarily
# client = openai

# def generate_question(theory_text, test_name, test_description, previous_qas, question_count, theory_id):
#     if question_count >= MAX_QUESTIONS:
#         return {"question": "You have completed all questions.", "options": {}}

#     db = load_or_create_vectorstore(theory_id, theory_text)
#     retriever = db.as_retriever()
#     relevant_docs = retriever.get_relevant_documents("next behavioral question")

#     context = "\n".join([doc.page_content for doc in relevant_docs])

#     prompt = f"""
# You are a smart educational AI. Generate a behavioral question based on:
# - The learning theory context below
# - The goal of the test: {test_name}
# - Test description: {test_description}
# - Previously answered Q&A (if any)

# Learning Theory:
# {context}

# Previous Q&A:
# {previous_qas if previous_qas else "None"}

# Ask the next question in this format:

# Q: <question>
# A. <option A>
# B. <option B>
# C. <option C>
# D. <option D>
# """

#     response = client.chat.completions.create(
#         model="gpt-4o",
#         messages=[{"role": "user", "content": prompt}],
#         temperature=0.7,
#         max_tokens=300,
#     )

#     raw_output = response.choices[0].message.content.strip()
#     question_match = re.search(r"Q:\s*(.+)", raw_output)
#     options = re.findall(r"[A-D]\.\s*(.+)", raw_output)

#     if not question_match or len(options) != 4:
#         return {"question": "Invalid format", "options": {}}

#     return {
#         "question": question_match.group(1).strip(),
#         "options": {
#             "a": options[0].strip(),
#             "b": options[1].strip(),
#             "c": options[2].strip(),
#             "d": options[3].strip(),
#         }
#     }


# def evaluate_answer(question, answer_text, theory_text, test_name, test_description, theory_id):
#     db = load_or_create_vectorstore(theory_id, theory_text)
#     retriever = db.as_retriever()
#     docs = retriever.get_relevant_documents(question)
#     context = "\n".join([doc.page_content for doc in docs])

#     prompt = f"""
# Evaluate this answer in the context of:
# - Test Name: {test_name}
# - Test Description: {test_description}
# - Related Theory: {context}

# Question:
# {question}

# User's Answer:
# {answer_text}

# What does this answer reveal about the user's behavioral traits or learning tendencies?
# """

#     response = client.chat.completions.create(
#         model="gpt-4o",
#         messages=[{"role": "user", "content": prompt}],
#         temperature=0.7,
#         max_tokens=300,
#     )

#     return response.choices[0].message.content.strip()


# def generate_behavior_report_from_evaluations(evaluations: List[str]):
#     if not evaluations:
#         return {"error": "No evaluations available."}

#     joined_evals = "\n".join([f"{i+1}. {ev}" for i, ev in enumerate(evaluations)])

#     prompt = f"""
# You are a student assessment AI. Based on the following evaluations from 5 behavioral tests, create a final summary report.

# Each evaluation gives insights into a student's:
# - Interest
# - Aptitude
# - Emotional intelligence
# - Motivation
# - Vision

# Return the report in **pure JSON format** (no markdown, no triple backticks).

# Format example:
# {{
#   "Interest": "92% - comment...",
#   "Aptitude": "88% - comment...",
#   "Emotional": "85% - comment...",
#   "Motivation": "89% - comment...",
#   "Vision": "91% - comment...",
#   "CareerIQ360 Index": "8.7/10"
# }}

# Evaluations:
# {joined_evals}
# """

#     response = client.chat.completions.create(
#         model="gpt-4o",
#         messages=[{"role": "user", "content": prompt}],
#         temperature=0.5,
#         max_tokens=500,
#     )

#     content = response.choices[0].message.content.strip()

#     try:
#         return json.loads(content)
#     except json.JSONDecodeError:
#         # Try to extract JSON manually in case of formatting issues
#         match = re.search(r'\{.*\}', content, re.DOTALL)
#         if match:
#             try:
#                 return json.loads(match.group())
#             except:
#                 pass
#         return {"report": content}

# def generate_detailed_assessment_report(test_name: str, theory_description: str, qas: List[dict]):
#     answered_qas = [qa for qa in qas if qa.get("answer")]

#     question_answer_pairs = "\n".join(
#         [f"Q{i+1}: {qa['question']}\nA: {qa['answer']}\nInsight: {qa['evaluation']}" for i, qa in enumerate(answered_qas)]
#     )

#     prompt = f"""
# You are a student assessment AI that evaluates users based on behavioral theory.

# Test Name: {test_name}
# Theory Summary:
# {theory_description}

# Below are the answered questions with insight evaluations:

# {question_answer_pairs}

# Write a detailed behavioral analysis report for this test in a **clear paragraph format**. Cover:
# - What the answers suggest about the user’s behavioral traits.
# - Patterns in interest, decision-making, emotional tendencies, or motivation.
# - Overall summary of their profile based on this test.

# Start with "This report evaluates the user's responses for the {test_name} test..."
# """

#     response = client.chat.completions.create(
#         model="gpt-4o",
#         messages=[{"role": "user", "content": prompt}],
#         temperature=0.5,
#         max_tokens=600,
#     )

#     return response.choices[0].message.content.strip()


# ai_assessment.py
# from langchain.vectorstores import FAISS
# from langchain.embeddings import OpenAIEmbeddings
# from .rag_utils import load_or_create_vectorstore
# from typing import List, Dict
# import openai
# import os
# import re
# import json

# openai.api_key = os.getenv("OPENAI_API_KEY")
# client = openai

# MAX_QUESTIONS = 3
# VECTORSTORE_CACHE: Dict[str, FAISS] = {}  # Global in-memory cache


# def get_vectorstore(theory_id: str, theory_text: str):
#     if theory_id in VECTORSTORE_CACHE:
#         return VECTORSTORE_CACHE[theory_id]
#     vs = load_or_create_vectorstore(theory_id, theory_text)
#     VECTORSTORE_CACHE[theory_id] = vs
#     return vs


# def generate_question(theory_text, test_name, test_description, previous_qas, question_count, theory_id):
#     if question_count >= MAX_QUESTIONS:
#         return {"question": "You have completed all questions.", "options": {}}

#     db = get_vectorstore(theory_id, theory_text)
#     docs = db.as_retriever().get_relevant_documents("next behavioral question")
#     context = "\n".join(doc.page_content for doc in docs[:3])

#     prompt = f"""
# Generate the next behavioral multiple choice question for the "{test_name}" test.

# Theory:
# {context}

# Previous Q&A:
# {previous_qas or "None"}

# Format:
# Q: <question>
# A. <option A>
# B. <option B>
# C. <option C>
# D. <option D>
# """

#     response = client.chat.completions.create(
#         model="gpt-4o",
#         messages=[{"role": "user", "content": prompt}],
#         temperature=0.6,
#         max_tokens=300,
#     )

#     content = response.choices[0].message.content.strip()
#     question_match = re.search(r"Q:\s*(.+)", content)
#     options = re.findall(r"[A-D]\.\s*(.+)", content)

#     if not question_match or len(options) != 4:
#         return {"question": "Invalid format", "options": {}}

#     return {
#         "question": question_match.group(1).strip(),
#         "options": {k: v.strip() for k, v in zip("abcd", options)}
#     }


# def evaluate_answer(question, answer_text, theory_text, test_name, test_description, theory_id):
#     db = get_vectorstore(theory_id, theory_text)
#     docs = db.as_retriever().get_relevant_documents(question)
#     context = "\n".join(doc.page_content for doc in docs[:3])

#     prompt = f"""
# Evaluate this behavioral answer.

# Test: {test_name}
# Q: {question}
# A: {answer_text}
# Theory Context: {context}

# What behavior trait does this suggest?
# """

#     response = client.chat.completions.create(
#         model="gpt-4o",
#         messages=[{"role": "user", "content": prompt}],
#         temperature=0.5,
#         max_tokens=300,
#     )

#     return response.choices[0].message.content.strip()


# def generate_behavior_report_from_evaluations(evaluations: List[str]):
#     if not evaluations:
#         return {"error": "No evaluations provided."}

#     joined_evals = "\n".join([f"{i+1}. {ev}" for i, ev in enumerate(evaluations)])
#     prompt = f"""
# Generate a JSON report based on 5 behavioral insights.

# Insights:
# {joined_evals}

# Return JSON only:
# {{
#   "Interest": "...",
#   "Aptitude": "...",
#   "Emotional": "...",
#   "Motivation": "...",
#   "Vision": "...",
#   "CareerIQ360 Index": "x.x/10"
# }}
# """

#     response = client.chat.completions.create(
#         model="gpt-4o",
#         messages=[{"role": "user", "content": prompt}],
#         temperature=0.4,
#         max_tokens=600,
#     )

#     content = response.choices[0].message.content.strip()

#     try:
#         return json.loads(content)
#     except json.JSONDecodeError:
#         match = re.search(r'\{.*\}', content, re.DOTALL)
#         if match:
#             try:
#                 return json.loads(match.group())
#             except:
#                 return {"report": match.group()}
#         return {"error": "Invalid JSON", "raw": content}


# def generate_detailed_assessment_report(test_name, test_description, theory_description, qas: List[dict]):
#     answered = [qa for qa in qas if qa.get("answer")]
#     if not answered:
#         return "No answered questions."

#     qa_block = "\n".join([f"Q{i+1}: {qa['question']}\nA: {qa['answer']}\nInsight: {qa['evaluation']}" for i, qa in enumerate(answered)])

#     prompt = f"""
# Generate a short narrative behavioral report.

# Test: {test_name}
# Description: {test_description}
# Theory: {theory_description}

# Answered Questions + Insights:
# {qa_block}

# Respond in 1 paragraph.
# """

#     response = client.chat.completions.create(
#         model="gpt-4o",
#         messages=[{"role": "user", "content": prompt}],
#         temperature=0.5,
#         max_tokens=600,
#     )

#     return response.choices[0].message.content.strip()


# ai_assessment.py
import openai
import os
import re
import json
from typing import List, Dict
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from .rag_utils import load_or_create_vectorstore
import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")
client = openai
MAX_QUESTIONS = 30
VECTORSTORE_CACHE: Dict[str, FAISS] = {}

def get_vectorstore(theory_id: str, theory_text: str):
    if theory_id in VECTORSTORE_CACHE:
        return VECTORSTORE_CACHE[theory_id]
    vs = load_or_create_vectorstore(theory_id, theory_text)
    VECTORSTORE_CACHE[theory_id] = vs
    return vs

STATIC_TESTS ={
		"NeuroStyle Index": {
        "description": "Learning preferences & cognitive strengths",
        "theory": "Based on Kolb's Learning Styles, VARK model, and Bloom's Taxonomy",
        "theory_id": "neurostyle-index",
        "section": "Middle School(13-15)",
        "prompt": """You are creating a learning style assessment for 13-15 year old students based on Kolb's Learning Styles (Concrete Experience, Reflective Observation, Abstract Conceptualization, Active Experimentation), VARK model (Visual, Auditory, Reading/Writing, Kinesthetic), and Bloom's Taxonomy levels.

Create 30 COMPLETELY UNIQUE questions that explore how students naturally learn and process information. Each question must test a different aspect of learning preference using TOTALLY DIFFERENT scenarios.

THEORY MAPPING:
- Visual learners: prefer diagrams, charts, demonstrations, seeing examples
- Auditory learners: prefer discussions, explanations, hearing information
- Reading/Writing learners: prefer text, notes, written instructions, lists
- Kinesthetic learners: prefer hands-on activities, movement, trial-and-error

MANDATORY: Use these 30 COMPLETELY DIFFERENT scenarios (one per question):
1. Learning to cook a new recipe
2. Understanding a video game strategy
3. Remembering phone numbers
4. Planning a birthday party
5. Learning dance moves
6. Understanding news events
7. Remembering shopping lists
8. Learning to drive a car
9. Understanding movie plots
10. Organizing your bedroom
11. Learning magic tricks
12. Understanding sports rules
13. Remembering appointments
14. Learning skateboard tricks
15. Understanding weather patterns
16. Memorizing song lyrics
17. Learning card games
18. Understanding directions to new places
19. Remembering people's names
20. Learning photography techniques
21. Understanding science experiments
22. Memorizing passwords
23. Learning knitting/crafting
24. Understanding historical events
25. Remembering book characters
26. Learning bike repair
27. Understanding math concepts
28. Memorizing vocabulary words
29. Learning computer shortcuts
30. Understanding art techniques

ANSWER PATTERN (rotate these 4 types):
Type A (Visual): "I prefer seeing/watching/looking at examples"
Type B (Auditory): "I like hearing/discussing/talking through it" 
Type C (Reading/Writing): "I need to read/write/take notes about it"
Type D (Kinesthetic): "I learn by doing/trying/practicing it myself"

FORMAT REQUIREMENTS:
- Use simple vocabulary (grade 7-8 reading level)
- Each question explores a completely different learning situation
- No repeated contexts or scenarios allowed
- Questions should reveal natural learning preferences
- Options should be 8-12 words maximum
- Focus on "how" and "what helps you" rather than "what should you do"

CRITICAL: Every question must use a scenario from the list above. No exceptions.

Generate exactly 30 questions numbered Q1-Q30 with the specified unique scenarios."""
    },

    "Cognitive Spark": {
        "description": "Multiple Intelligence & aptitude discovery",
        "theory": "Based on Gardner's Multiple Intelligences and CHC model",
        "theory_id": "cognitive-spark",
        "section": "Middle School(13-15)",
        "prompt": """You are creating a multiple intelligence assessment for 13-15 year olds based on Gardner's 8 Intelligences and the CHC (Cattell-Horn-Carroll) model of cognitive abilities.

Create 30 COMPLETELY UNIQUE questions that identify students' natural strengths and interests across different intelligence areas using TOTALLY DIFFERENT scenarios.

GARDNER'S 8 INTELLIGENCES TO ASSESS:
1. Linguistic (words, language, reading, writing)
2. Logical-Mathematical (numbers, logic, patterns, reasoning)
3. Spatial (visual, artistic, design, navigation)
4. Musical (rhythm, melody, sound, music)
5. Bodily-Kinesthetic (movement, sports, hands-on activities)
6. Interpersonal (understanding others, social skills)
7. Intrapersonal (self-awareness, reflection, independence)
8. Naturalistic (nature, animals, environment, patterns)

MANDATORY: Use these 30 COMPLETELY DIFFERENT scenarios (one per question):
1. Weekend free time activity choice
2. Ideal summer job selection  
3. Favorite podcast topic
4. Dream bedroom decoration
5. Perfect pet choice
6. Ideal board game type
7. Favorite YouTube content
8. Best vacation destination
9. Preferred hobby to start
10. Ideal superhero power
11. Best way to earn money
12. Favorite weather activity
13. Perfect birthday gift to receive
14. Best club to join at school
15. Ideal talent show act
16. Perfect volunteer opportunity
17. Best way to help a sad friend
18. Ideal dinner party theme
19. Perfect study snack
20. Best movie genre to watch
21. Ideal garden to plant
22. Perfect exercise routine
23. Best way to decorate locker
24. Ideal time travel destination
25. Perfect invention to create
26. Best way to spend snow day
27. Ideal competition to enter
28. Perfect fundraiser idea
29. Best way to organize closet
30. Ideal legacy to leave behind

ANSWER OPTIONS PATTERN:
Each set of 4 options should represent different intelligences:
- Rotate through all 8 intelligences across questions
- No repeated intelligence combinations

CRITICAL REQUIREMENTS:
- Every question uses a COMPLETELY different scenario from the list
- Simple language appropriate for ages 13-15
- Focus on natural preferences, not learned skills
- Options are 8-15 words maximum
- Questions reveal what energizes and interests them
- No repetition of contexts, activities, or situations allowed

Generate exactly 30 questions numbered Q1-Q30, each using the specified unique scenarios."""
    },

    "Emerging Identity Map": {
        "description": "Personality sketch & early identity shaping",
        "theory": "Based on MBTI (Lite) and Erikson's theory",
        "theory_id": "emerging-identity",
        "section": "Middle School(13-15)",
        "prompt": """You are creating a personality assessment for 13-15 year olds based on simplified MBTI dimensions and Erikson's Identity vs Role Confusion stage (ages 12-18).

Create 30 COMPLETELY UNIQUE questions that explore personality preferences and identity development patterns using TOTALLY DIFFERENT scenarios.

MBTI DIMENSIONS TO ASSESS (simplified for teens):
1. Energy Source: Introversion vs Extraversion (where they get energy)
2. Information Processing: Sensing vs Intuition (how they take in information)  
3. Decision Making: Thinking vs Feeling (how they make choices)
4. Life Approach: Judging vs Perceiving (how they organize their world)

MANDATORY: Use these 30 COMPLETELY DIFFERENT scenarios (one per question):
1. Choosing what to wear each morning
2. Deciding on weekend plans with friends
3. Handling a disagreement with parents
4. Reacting to unexpected schedule changes
5. Choosing elective classes for next year
6. Dealing with a rumor about yourself
7. Planning your ideal 16th birthday
8. Responding to criticism from teacher
9. Choosing Halloween costume
10. Handling social media drama
11. Deciding summer vacation activities
12. Reacting to failing a test
13. Choosing Christmas gifts for family
14. Handling peer pressure situations
15. Planning future high school courses
16. Dealing with friend moving away
17. Choosing extracurricular activities
18. Handling embarrassing moments
19. Deciding career exploration topics
20. Reacting to winning an award
21. Choosing room redecoration style
22. Handling family dinner conversations
23. Deciding volunteer opportunities
24. Reacting to first day at new school
25. Choosing social media platforms
26. Handling disappointing news
27. Deciding dating relationship approach
28. Reacting to sibling conflicts
29. Choosing personal values priorities
30. Handling future uncertainty feelings

ANSWER PATTERNS (rotate):
Type 1 - Energy: Introversion vs Extraversion responses
Type 2 - Processing: Concrete/detail vs Big picture/possibility responses  
Type 3 - Decisions: Logic/fairness vs Values/harmony responses
Type 4 - Organization: Structure/planning vs Flexibility/spontaneity responses

CRITICAL REQUIREMENTS:
- Every question uses a COMPLETELY different scenario from the list
- Use situations teens actually face
- Simple vocabulary (grade 7-8 level)
- Options 8-12 words maximum
- No repeated scenarios or contexts allowed

Generate exactly 30 questions numbered Q1-Q30 using the specified unique scenarios."""
    },

   "Pathfinder RIASEC-Lite": {
        "description": "Interest mapping for career exploration",
        "theory": "Based on Holland Code theory",
        "theory_id": "pathfinder-RIASEC-Lite",
        "section": "Middle School(13-15)",
        "prompt": """You are creating a career interest assessment for 13-15 year olds based on Holland's RIASEC model (Realistic, Investigative, Artistic, Social, Enterprising, Conventional).

Create 30 COMPLETELY UNIQUE questions using TOTALLY DIFFERENT contexts. NO repetition of scenarios.

HOLLAND'S 6 TYPES TO ASSESS:
1. REALISTIC (R): Hands-on, practical, building, fixing, outdoors, tools
2. INVESTIGATIVE (I): Research, science, analysis, discovery, problem-solving
3. ARTISTIC (A): Creative, design, music, writing, imagination, expression
4. SOCIAL (S): Helping people, teaching, caring, supporting others
5. ENTERPRISING (E): Leading, selling, persuading, competing, organizing people
6. CONVENTIONAL (C): Data, details, organizing information, following systems

MANDATORY: Use these 30 DIFFERENT scenario types (one per question):
1. Smartphone notification preferences
2. Dream house design features
3. Perfect pet training approach
4. Ideal car customization
5. Favorite cooking show type
6. Best way to learn language
7. Perfect camping trip role
8. Ideal photography subject
9. Best treasure hunt strategy
10. Perfect birthday surprise planning
11. Favorite puzzle type
12. Best way to help elderly neighbor
13. Ideal science fair project
14. Perfect art museum section
15. Best way to organize photos
16. Ideal fantasy novel character
17. Perfect community garden contribution
18. Best way to plan family reunion
19. Ideal time capsule contents
20. Perfect weather day activity
21. Best way to decorate classroom
22. Ideal historical era to visit
23. Perfect invention for humanity
24. Best way to help animal shelter
25. Ideal magic power to possess
26. Perfect way to spend lottery winnings
27. Best approach to group project leadership
28. Ideal documentary topic creation
29. Perfect retirement activity
30. Best way to preserve family memories

ANSWER PATTERNS (rotate these):
Set A: R-focus, I-focus, A-focus, S-focus
Set B: I-focus, A-focus, S-focus, E-focus  
Set C: A-focus, S-focus, E-focus, C-focus
Set D: S-focus, E-focus, C-focus, R-focus

CRITICAL REQUIREMENTS:
- Every question uses a COMPLETELY different scenario from the list above
- NO repeated contexts or situations allowed
- Focus on personal interests and natural preferences
- Use everyday situations teens experience
- Simple vocabulary (grade 7-8 level)
- Options 8-12 words maximum
- Mix all 6 RIASEC types across the 30 questions

Generate exactly 30 questions numbered Q1-Q30, each using a completely different scenario from the list above."""
    },

    "FutureScope": {
        "description": "Future readiness, grit, adaptability",
        "theory": "Based on Grit Scale, Super's Theory",
        "theory_id": "futurescope",
        "section": "Middle School(13-15)",
        "prompt": """You are creating a resilience and future readiness assessment for 13-15 year olds based on Duckworth's Grit Scale and Super's Career Development Theory.

Create 30 COMPLETELY UNIQUE questions that assess perseverance, passion for long-term goals, adaptability, and future orientation using TOTALLY DIFFERENT scenarios.

KEY CONCEPTS TO ASSESS:
GRIT COMPONENTS:
1. Perseverance of Effort (working hard despite setbacks)
2. Consistency of Interests (maintaining focus on goals)  
3. Passion for Goals (deep engagement with objectives)
4. Resilience (bouncing back from failure)

MANDATORY: Use these 30 COMPLETELY DIFFERENT scenarios (one per question):
1. Learning to skateboard after multiple falls
2. Saving money for expensive gaming console
3. Training for school marathon despite slow progress
4. Learning piano when fingers feel clumsy
5. Growing garden when plants keep dying
6. Building model airplane that keeps breaking
7. Learning new language with difficult pronunciation
8. Training pet that won't follow commands
9. Practicing magic tricks that audience doesn't like
10. Learning to cook when meals taste terrible
11. Building friendship with shy classmate
12. Improving grades in most difficult subject
13. Learning photography with blurry pictures
14. Training for sport with frequent losses
15. Learning art when drawings look childish
16. Organizing messy room that stays cluttered
17. Learning computer coding with constant errors
18. Building confidence for public speaking
19. Improving handwriting when it's barely legible
20. Learning dance moves that feel awkward
21. Mastering video game with difficult levels
22. Building muscle strength from weak starting point
23. Learning instrument when sounds are harsh
24. Improving social skills when feeling shy
25. Developing fashion sense when outfits clash
26. Learning debate skills when losing arguments
27. Building stamina when getting tired quickly
28. Learning jokes when nobody laughs
29. Improving organization when constantly forgetting
30. Building patience when everything feels rushed

ANSWER PATTERNS (measuring different resilience aspects):
- High Grit: Shows persistence, learns from failure, maintains long-term focus
- Moderate Grit: Shows some persistence but may get discouraged  
- Growth Mindset: Believes abilities can be developed through effort
- Fixed Mindset: Believes abilities are unchangeable traits

CRITICAL REQUIREMENTS:
- Every question uses a COMPLETELY different scenario from the list above
- Use realistic teen challenges and situations
- Simple, clear language (grade 7-8 level)
- Options 8-15 words maximum
- Positive, solution-focused framing
- No repeated scenarios or contexts allowed

Generate exactly 30 questions numbered Q1-Q30, each exploring different aspects of resilience using the specified unique scenarios."""
    }
}

def fetch_questions(batch_prompt):
    response = client.chat.completions.create(
        model="gpt-4o",  # Updated to GPT-4o
        messages=[{"role": "user", "content": batch_prompt}],
        temperature=0.6,
        max_tokens=3000,  # Increased token limit
    )
    return response.choices[0].message.content.strip()

def parse_questions_from_content(content: str) -> List[dict]:
    """Parse questions from AI response content"""
    questions = []
    
    # Split by question numbers (Q1:, Q2:, etc.)
    question_blocks = re.split(r'\n(?=Q\d+:)', content.strip())
    
    for block in question_blocks:
        if not block.strip():
            continue
            
        lines = [line.strip() for line in block.strip().split('\n') if line.strip()]
        
        if len(lines) < 5:  # Need at least question + 4 options
            continue
        
        # Extract question (first line)
        question_line = lines[0]
        if ':' in question_line:
            question = question_line.split(':', 1)[1].strip()
        else:
            question = question_line.strip()
        
        # Extract options
        options = {}
        option_letters = ['A', 'B', 'C', 'D']
        
        for i, letter in enumerate(option_letters):
            if i + 1 < len(lines):
                option_line = lines[i + 1]
                # Remove the letter prefix (A., B., etc.)
                if option_line.startswith(f"{letter}.") or option_line.startswith(f"{letter})"):
                    option_text = option_line[2:].strip()
                elif option_line.startswith(f"{letter}:"):
                    option_text = option_line[2:].strip()
                else:
                    option_text = option_line.strip()
                
                options[letter.lower()] = option_text
        
        # Only add if we have all 4 options
        if len(options) == 4 and question:
            questions.append({
                "question": question,
                "options": options
            })
    
    return questions

def generate_questions(test_name: str, section_name: str = "Middle School(13-15)", total: int = 30):
    """Generate exactly 30 questions for the given test"""
    test_info = STATIC_TESTS[test_name]
    theory_text = test_info["theory"]
    theory_id = test_info["theory_id"]
    prompt_intro = test_info.get("prompt", "")

    # Get context from vectorstore
    try:
        db = get_vectorstore(theory_id, theory_text)
        docs = db.as_retriever().get_relevant_documents("behavioral question")
        context = "\n".join(doc.page_content for doc in docs[:3])
    except Exception as e:
        print(f"Error getting vectorstore context: {e}")
        context = theory_text  # Fallback to theory text

    all_questions = []
    max_attempts = 3  # Maximum attempts to get 30 questions

    for attempt in range(max_attempts):
        full_prompt = f"""
You are generating psychometric questions for the "{section_name}" section.

{prompt_intro}

Use this theory context as reference:
{context}

CRITICAL REQUIREMENTS:
- You must generate exactly 30 multiple choice behavioral questions
- Number them Q1 through Q30
- Each question must use a completely different scenario (no repetition allowed)
- Follow the mandatory scenario list provided in the prompt above

Each question must follow this exact format:
Q1: [Question text here]
A. [Option A text]
B. [Option B text] 
C. [Option C text]
D. [Option D text]

Q2: [Question text here]
A. [Option A text]
B. [Option B text]
C. [Option C text] 
D. [Option D text]

Continue this pattern until Q30. Do not include any other text or explanations.

IMPORTANT: Use each scenario from the provided list exactly once. No scenario repetition allowed.
"""
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o",  # Updated to GPT-4o
                messages=[{"role": "user", "content": full_prompt}],
                temperature=0.6,
                max_tokens=4000,  # Increased for 30 questions
            )

            content = response.choices[0].message.content.strip()
            questions = parse_questions_from_content(content)
            
            if len(questions) >= total:
                all_questions = questions[:total]  # Take exactly 30 questions
                break
            else:
                print(f"Attempt {attempt + 1}: Only got {len(questions)} questions, retrying...")
                all_questions.extend(questions)
                
        except Exception as e:
            print(f"Error in attempt {attempt + 1}: {e}")
            continue

    # If we still don't have enough questions, generate additional ones
    while len(all_questions) < total:
        remaining = total - len(all_questions)
        
        additional_prompt = f"""
Generate {remaining} additional multiple choice behavioral questions for the "{section_name}" section about {test_name}.

Use this theory: {theory_text}

CRITICAL: Use completely different scenarios from any previous questions. No repetition.

Format each question as:
Q{len(all_questions) + 1}: [Question text]
A. [Option A]
B. [Option B]
C. [Option C] 
D. [Option D]

Continue numbering from Q{len(all_questions) + 1} to Q{total}.
"""
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o",  # Updated to GPT-4o
                messages=[{"role": "user", "content": additional_prompt}],
                temperature=0.7,
                max_tokens=2000,
            )
            
            content = response.choices[0].message.content.strip()
            additional_questions = parse_questions_from_content(content)
            all_questions.extend(additional_questions)
            
        except Exception as e:
            print(f"Error generating additional questions: {e}")
            break

    # Ensure we have exactly the requested number of questions
    final_questions = all_questions[:total]
    
    print(f"Generated {len(final_questions)} questions for {test_name}")
    return final_questions

def evaluate_answers(test_name: str, qas_with_answers: List[dict], section_name: str = "middle"):
    theory = STATIC_TESTS[test_name]["theory"]

    joined = "\n".join([
        f"Q{i+1}: {qa['question']}\nA: {qa['answer']}" for i, qa in enumerate(qas_with_answers)
    ])

    prompt = f"""
You are evaluating answers for the '{section_name}' section students.

Theory:
{theory}

{joined}

Give one insight per question:

1. <Insight>
2. <Insight>
... up to {len(qas_with_answers)}
"""

    response = client.chat.completions.create(
        model="gpt-4o",  # Updated to GPT-4o
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        max_tokens=1500,
    )

    lines = response.choices[0].message.content.strip().split("\n")
    return [line.partition(".")[2].strip() for line in lines if "." in line]

def generate_detailed_assessment_report(test_name, test_description, theory_description, qas: List[dict]):
    answered = [qa for qa in qas if qa.get("answer")]
    if not answered:
        return "No answered questions."

    qa_block = "\n".join([f"Q{i+1}: {qa['question']}\nA: {qa['answer']}\nInsight: {qa['evaluation']}" for i, qa in enumerate(answered)])

    prompt = f"""
Generate a short narrative behavioral report.

Test: {test_name}
Description: {test_description}
Theory: {theory_description}

Answered Questions + Insights:
{qa_block}

Respond in 1 paragraph.
"""

    response = client.chat.completions.create(
        model="gpt-4o",  # Updated to GPT-4o
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        max_tokens=600,
    )

    return response.choices[0].message.content.strip()

# def generate_behavior_report_from_evaluations(evaluations: List[str]):
#     if not evaluations:
#         return {"error": "No evaluations provided."}

#     joined_evals = "\n".join([f"{i+1}. {ev}" for i, ev in enumerate(evaluations)])
#     prompt = f"""
# Generate a JSON report based on 5 behavioral insights.

# Insights:
# {joined_evals}

# Return JSON only:
# {{
#   "Interest": "...",
#   "Aptitude": "...",
#   "Emotional": "...",
#   "Motivation": "...",
#   "Vision": "...",
#   "CareerIQ360 Index": "x.x/10"
# }}
# """

#     response = client.chat.completions.create(
#         model="gpt-3.5-turbo",
#         messages=[{"role": "user", "content": prompt}],
#         temperature=0.4,
#         max_tokens=600,
#     )

#     content = response.choices[0].message.content.strip()

#     try:
#         return json.loads(content)
#     except json.JSONDecodeError:
#         match = re.search(r'\{.*\}', content, re.DOTALL)
#         if match:
#             try:
#                 return json.loads(match.group())
#             except:
#                 return {"report": match.group()}
#         return {"error": "Invalid JSON", "raw": content}


# def generate_detailed_assessment_report(test_name, test_description, theory_description, qas: List[dict]):
#     answered = [qa for qa in qas if qa.get("answer")]
#     if not answered:
#         return "No answered questions."

#     qa_block = "\n".join([f"Q{i+1}: {qa['question']}\nA: {qa['answer']}\nInsight: {qa['evaluation']}" for i, qa in enumerate(answered)])

#     prompt = f"""
# Generate a short narrative behavioral report.

# Test: {test_name}
# Description: {test_description}
# Theory: {theory_description}

# Answered Questions + Insights:
# {qa_block}

# Respond in 1 paragraph.
# """

#     response = client.chat.completions.create(
#         model="gpt-3.5-turbo",
#         messages=[{"role": "user", "content": prompt}],
#         temperature=0.5,
#         max_tokens=600,
#     )

#     return response.choices[0].message.content.strip()


