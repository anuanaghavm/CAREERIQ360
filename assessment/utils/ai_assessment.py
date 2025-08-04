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

STATIC_TESTS = {
    "NeuroStyle Index": {
        "description": "Learning preferences & cognitive strengths",
        "theory": "Based on Kolb's Learning Styles, VARK model, and Bloom's Taxonomy",
        "theory_id": "neurostyle-index",
        "section": "Middle School(13-15)",
        "prompt": """CRITICAL: Generate 30 COMPLETELY UNIQUE questions for NeuroStyle Index test. Each question must be ENTIRELY DIFFERENT from any previous version - different scenarios, contexts, wording, and situations.

You are creating questions for middle school students (13-15 years) to assess learning preferences using:

1. Kolb's Learning Styles: Converger, Diverger, Assimilator, Accommodator (10 questions)
2. VARK Model: Visual, Auditory, Reading/Writing, Kinesthetic (10 questions)  
3. Bloom's Taxonomy: Remember, Understand, Apply, Analyze, Evaluate, Create (10 questions)

UNIQUENESS REQUIREMENTS:
- Use completely different school situations each time (math class, science lab, art project, sports, group work, homework, exams, presentations, etc.)
- Vary question structures: "When you...", "If your teacher...", "During a project...", "While studying..."
- Use diverse contexts: classroom, home study, extracurricular activities, peer interactions, technology use
- Ensure each answer choice reflects different learning preferences clearly

MANDATORY: Each question must be set in a DIFFERENT scenario/context. No repetition of situations or phrasings.

Format each question as:
Q1: [Question text]
A. [Option A]
B. [Option B]  
C. [Option C]
D. [Option D]

Continue until Q30 with completely unique scenarios."""
    },
    "Cognitive Spark": {
        "description": "Multiple Intelligence & aptitude discovery",
        "theory": "Based on Gardner's Multiple Intelligences and CHC model",
        "theory_id": "cognitive-spark",
        "section": "Middle School(13-15)",
        "prompt": """CRITICAL: Generate 30 COMPLETELY UNIQUE questions for Cognitive Spark test. Each question must be ENTIRELY DIFFERENT from any previous version.

You are creating questions for middle school students (13-15 years) to assess cognitive aptitude using:

1. Gardner's Multiple Intelligences: Linguistic, Logical-Mathematical, Spatial, Musical, Bodily-Kinesthetic, Interpersonal, Intrapersonal, Naturalistic
2. CHC Theory: Fluid Reasoning (Gf), Visual-Spatial (Gv), Crystallized Intelligence (Gc), Auditory Processing (Ga), Working Memory (Gsm)

UNIQUENESS REQUIREMENTS:
- Create completely different scenarios each time: different subjects, different school activities, different problem-solving situations
- Vary question contexts: classroom activities, extracurricular clubs, home projects, social situations, creative tasks
- Use diverse intelligence indicators: word games, math puzzles, spatial challenges, music activities, physical coordination, social understanding, self-reflection, nature observation
- Each scenario must be COMPLETELY DIFFERENT from previous versions

DISTRIBUTION: Cover all 8 MI types and 5 CHC abilities across 30 questions with varied difficulty and contexts.

Format each question as:
Q1: [Question text]
A. [Option A]
B. [Option B]
C. [Option C]
D. [Option D]

Continue until Q30 with completely unique scenarios."""
    },
    "Emerging Identity Map": {
        "description": "Personality sketch & early identity shaping",
        "theory": "Based on MBTI (Lite) and Erikson's theory",
        "theory_id": "emerging-identity",
        "section": "Middle School(13-15)",
        "prompt": """CRITICAL: Generate 30 COMPLETELY UNIQUE questions for Emerging Identity Map test. Each question must be ENTIRELY DIFFERENT from any previous version.

You are creating questions for middle school students (13-15 years) to assess personality and identity development using:

1. MBTI Lite: Introversion/Extraversion, Sensing/Intuition, Thinking/Feeling, Judging/Perceiving
2. Erikson's Identity vs Role Confusion: self-concept, values exploration, future goals, peer relationships, independence

UNIQUENESS REQUIREMENTS:
- Create completely different life scenarios each time: different social situations, different decisions, different conflicts, different goals
- Vary contexts: family situations, friend groups, school events, personal choices, future planning, hobby selection, value decisions
- Use diverse personality indicators: social preferences, decision-making styles, emotional responses, planning approaches, conflict resolution
- Each scenario must be COMPLETELY DIFFERENT from previous versions
- Avoid psychological jargon - use teen-friendly language

DISTRIBUTION: 
- MBTI traits: 4-5 questions each for I/E, S/N, T/F, J/P
- Erikson themes: 6-8 questions on identity exploration
- Blended questions: 4-6 questions combining both frameworks

Format each question as:
Q1: [Question text]
A. [Option A]
B. [Option B]
C. [Option C]
D. [Option D]

Continue until Q30 with completely unique scenarios."""
    },
    "Pathfinder RIASEC-Lite": {
        "description": "Interest mapping for career exploration",
        "theory": "Based on Holland Code theory",
        "theory_id": "pathfinder-RIASEC-Lite",
        "section": "Middle School(13-15)",
        "prompt": """You are a psychometrician designing a psychometric test for school students aged 13–16 (grades 8 to 10). Generate 30 age-appropriate, engaging multiple-choice questions to help identify students' dominant interest patterns based on Holland's RIASEC Model (RIASEC-Lite):

1. *Realistic (R):* Preference for hands-on, physical, or technical tasks  
2. *Investigative (I):* Interest in thinking, analyzing, exploring, or solving problems  
3. *Artistic (A):* Creative expression, imagination, and originality  
4. *Social (S):* Helping, teaching, or interacting with others  
5. *Enterprising (E):* Leadership, persuasion, or entrepreneurial activities  
6. *Conventional (C):* Structure, organization, detail-oriented work

Guidelines:
- Keep language simple, relatable, and suitable for middle to high school students.
- Situations should reflect school life, hobbies, future dreams, or group tasks.
- Each question must have 4 answer choices (A–D), representing different RIASEC traits.
- Avoid career jargon; focus on behaviors and preferences.

Format each question as:
Q1: [Question text]
A. [Option A]
B. [Option B]
C. [Option C]
D. [Option D]

Q2: [Question text]
A. [Option A]
B. [Option B]
C. [Option C]
D. [Option D]

... continue until Q30"""
    },
    "FutureScope": {
        "description": "Future readiness, grit, adaptability",
        "theory": "Based on Grit Scale, Super's Theory",
        "theory_id": "futurescope",
        "section": "Middle School(13-15)",
        "prompt": """You are a psychometrician designing a psychometric test for students aged 13–16 (grades 8 to 10). Generate 30 simple, engaging multiple-choice questions that measure behavioral tendencies, career readiness, and cognitive aptitude using the following frameworks:

1. *Grit Scale (Angela Duckworth)* – Assess persistence, consistency of effort, and passion for long-term goals.
2. *CHC Theory (Cattell–Horn–Carroll)* – Evaluate core cognitive abilities like fluid reasoning (Gf), crystallized knowledge (Gc), visual-spatial processing (Gv), short-term working memory (Gwm), and processing speed (Gs).
3. *Super's Theory of Career Development* – Understand the student's level of self-awareness, vocational identity, role exploration, and readiness for future planning.

Guidelines:
- Questions should use relatable, school-life scenarios (e.g., study habits, long-term projects, leadership roles, future dreams).
- Each question must have 4 options (A–D), reflecting varying levels or expressions of the trait being measured.
- Language must be age-appropriate and friendly, with no technical jargon.
- Distribute questions across all three frameworks.

Format each question as:
Q1: [Question text]
A. [Option A]
B. [Option B]
C. [Option C]
D. [Option D]

Q2: [Question text]
A. [Option A]
B. [Option B]
C. [Option C]
D. [Option D]

... continue until Q30"""
    },
}

def fetch_questions(batch_prompt):
    response = client.chat.completions.create(
        model="gpt-4o",
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

IMPORTANT: You must generate exactly 30 multiple choice behavioral questions. Number them Q1 through Q30.

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
"""
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
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
                model="gpt-4o",
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
        model="gpt-4o",
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
        model="gpt-4o",
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


