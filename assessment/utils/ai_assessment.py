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
        "theory": "Based on Kolb’s Learning Styles, VARK model, and Bloom’s Taxonomy",
        "theory_id": "neurostyle-index",
        "section": "Middle School(13-15)",
        "prompt": """You are a psychometrician designing a psychometric test for school students aged 13–16 (grades 8 to 10). Generate, age-appropriate multiple-choice questions that help identify each student's dominant learning style and cognitive preferences based on the following frameworks:

1. *Kolb’s Learning Styles* – Identify if the student is more of a Converger, Diverger, Assimilator, or Accommodator through scenario-based questions.
2. *VARK Model* – Determine if the student prefers Visual, Auditory, Reading/Writing, or Kinesthetic learning styles using situations from school or home life.
3. *Bloom’s Taxonomy* – Questions should also tap into different cognitive levels (Remembering, Understanding, Applying, Analyzing, Evaluating, Creating).

Guidelines:
- Each question must have 4 options.
- Use simple language and familiar situations from school life (e.g., group projects, studying, presentations, sports, hobbies).
- Avoid technical jargon.
- Ensure the questions are balanced across the three frameworks. 
 
Label: [VARK – Learning Preference]"""
    },
    "Cognitive Spark": {
        "description": "Multiple Intelligence & aptitude discovery",
        "theory": "Based on Gardner’s Multiple Intelligences and CHC model",
        "theory_id": "cognitive-spark",
        "section": "Middle School(13-15)",
        "prompt": """You are a psychometrician designing a psychometric test for school students aged 13–16 (grades 8 to 10). Generate 30 engaging, age-appropriate multiple-choice questions that assess a student's cognitive aptitude and intellectual strengths, based on the following frameworks:

1. *Gardner’s Multiple Intelligences (MI)* – Identify dominant intelligences such as linguistic, logical-mathematical, spatial, musical, bodily-kinesthetic, interpersonal, intrapersonal, and naturalistic.
2. *CHC Theory (Cattell–Horn–Carroll)* – Assess broad cognitive abilities including fluid reasoning (Gf), visual-spatial processing (Gv), crystallized intelligence (Gc), auditory processing (Ga), and short-term working memory (Gsm).

Guidelines:
- Each question should be situational and relatable to a student's school life, hobbies, or daily experiences.
- Use language that is simple, engaging, and suitable for middle and high school students.
- Each question must have 4 answer options (A–D).
- Ensure a mix of questions across MI types and CHC abilities.
- Label each question with the related intelligence or CHC domain. (e.g., [MI – Musical], [CHC – Gv])
"""
    },
    "Emerging Identity Map": {
        "description": "Personality sketch & early identity shaping",
        "theory": "Based on MBTI (Lite) and Erikson’s theory",
        "theory_id": "emerging-identity",
        "section": "Middle School(13-15)",
        "prompt": """You are a psychometric test question generator.

Create scenario-based questions for a personality and identity test called "Emerging Identity Map." The test is meant for school students in classes 8 to 10 (ages 13–16) in India. It is based on:

1. MBTI (Lite), focusing on:
   - Introversion (I)
   - Extraversion (E)
   - Sensing (S)
   - Intuition (N)
   - Thinking (T)
   - Feeling (F)
   - Judging (J)
   - Perceiving (P)

2. Erikson’s Identity vs. Role Confusion theory.

*Instructions:*
- Each question must describe a short, simple real-life scenario relevant to a school student (class, homework, exams, friends, emotions, goals, etc.).
- Provide 4 multiple-choice options labeled A, B, C, and D.
- Each option should represent a distinct personality trait (from MBTI or Erikson’s identity stage).
- Do *not* use psychological jargon like "introvert" or "judging".
- Use casual, age-appropriate school language and relatable everyday experiences.
- Avoid “None of the above” or overly similar options."""
    },
    "Pathfinder RIASEC-Lite": {
        "description": "Interest mapping for career exploration",
        "theory": "Based on Holland Code theory",
        "theory_id": "pathfinder-RIASEC-Lite",
        "section": "Middle School(13-15)",
        "prompt": """You are a psychometrician designing a psychometric test for school students aged 13–16 (grades 8 to 10). Generate  age-appropriate, engaging multiple-choice questions to help identify students' dominant interest patterns based on Holland’s RIASEC Model (RIASEC-Lite):

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
- Avoid career jargon; focus on behaviors and preferences."""
    },
    "FutureScope": {
        "description": "Future readiness, grit, adaptability",
        "theory": "Based on Grit Scale, Super's Theory",
        "theory_id": "futurescope",
        "section": "Middle School(13-15)",
        "prompt": """Future scope 

You are a psychometrician designing a psychometric test for students aged 13–16 (grades 8 to 10). Generate simple, engaging multiple-choice questions that measure behavioral tendencies, career readiness, and cognitive aptitude using the following frameworks:

1. *Grit Scale (Angela Duckworth)* – Assess persistence, consistency of effort, and passion for long-term goals.
2. *CHC Theory (Cattell–Horn–Carroll)* – Evaluate core cognitive aptitudes like fluid reasoning (Gf), crystallized knowledge (Gc), visual-spatial processing (Gv), short-term working memory (Gwm), and processing speed (Gs).
3. *Super’s Theory of Career Development* – Understand the student’s level of self-awareness, vocational identity, role exploration, and readiness for future planning.

Guidelines:
- Questions should use relatable, school-life scenarios (e.g., study habits, long-term projects, leadership roles, future dreams).
- Each question must have 4 options (A–D), reflecting varying levels or expressions of the trait being measured.
- Language must be age-appropriate and friendly, with no technical jargon.
- Distribute questions across all three frameworks.
- Label each question with its corresponding psychological dimension (e.g., [Grit – Consistency], [CHC – Gf], [Super – Career Maturity]).
"""
    },
    # Add others similarly...
}

def generate_questions(test_name: str, section_name: str = "Middle School(13-15)", total: int = 30):
    test_info = STATIC_TESTS[test_name]
    theory_text = test_info["theory"]
    theory_id = test_info["theory_id"]
    prompt_intro = test_info.get("prompt", "")

    db = get_vectorstore(theory_id, theory_text)
    docs = db.as_retriever().get_relevant_documents("behavioral question")
    context = "\n".join(doc.page_content for doc in docs[:3])

    all_questions = []

    batch_size = 10
    num_batches = total // batch_size

    for i in range(num_batches):
        full_prompt = f"""
You are generating psychometric questions for the "{section_name}" section.

{prompt_intro}

Use this theory context as reference:
{context}

Generate {batch_size} multiple choice behavioral questions.

Format:
Q: <question>
A. <option A>
B. <option B>
C. <option C>
D. <option D>
"""
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": full_prompt}],
            temperature=0.6,
            max_tokens=2000,
        )

        content = response.choices[0].message.content.strip()
        questions_raw = re.split(r"(?:^|\n)(?=Q[:\s])", content.strip(), flags=re.IGNORECASE)

        for block in questions_raw[1:]:
            lines = block.strip().split("\n")
            if len(lines) >= 5:
                question = lines[0].strip()
                options = dict(zip("abcd", [line[2:].strip() for line in lines[1:5]]))
                all_questions.append({"question": question, "options": options})

    return all_questions


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
        model="gpt-3.5-turbo",
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


