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
# ai_assessment.py

from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from .rag_utils import load_or_create_vectorstore
from typing import List, Dict
import openai
import os
import re
import json

openai.api_key = os.getenv("OPENAI_API_KEY")
client = openai

MAX_QUESTIONS = 3
VECTORSTORE_CACHE: Dict[str, FAISS] = {}  # Global in-memory cache


def get_vectorstore(theory_id: str, theory_text: str):
    if theory_id in VECTORSTORE_CACHE:
        return VECTORSTORE_CACHE[theory_id]
    vs = load_or_create_vectorstore(theory_id, theory_text)
    VECTORSTORE_CACHE[theory_id] = vs
    return vs


def generate_question(theory_text, test_name, test_description, previous_qas, question_count, theory_id):
    if question_count >= MAX_QUESTIONS:
        return {"question": "You have completed all questions.", "options": {}}

    db = get_vectorstore(theory_id, theory_text)
    docs = db.as_retriever().get_relevant_documents("next behavioral question")
    context = "\n".join(doc.page_content for doc in docs[:3])

    prompt = f"""
Generate the next behavioral multiple choice question for the "{test_name}" test.

Theory:
{context}

Previous Q&A:
{previous_qas or "None"}

Format:
Q: <question>
A. <option A>
B. <option B>
C. <option C>
D. <option D>
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6,
        max_tokens=300,
    )

    content = response.choices[0].message.content.strip()
    question_match = re.search(r"Q:\s*(.+)", content)
    options = re.findall(r"[A-D]\.\s*(.+)", content)

    if not question_match or len(options) != 4:
        return {"question": "Invalid format", "options": {}}

    return {
        "question": question_match.group(1).strip(),
        "options": {k: v.strip() for k, v in zip("abcd", options)}
    }


def evaluate_answer(question, answer_text, theory_text, test_name, test_description, theory_id):
    db = get_vectorstore(theory_id, theory_text)
    docs = db.as_retriever().get_relevant_documents(question)
    context = "\n".join(doc.page_content for doc in docs[:3])

    prompt = f"""
Evaluate this behavioral answer.

Test: {test_name}
Q: {question}
A: {answer_text}
Theory Context: {context}

What behavior trait does this suggest?
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        max_tokens=300,
    )

    return response.choices[0].message.content.strip()


def generate_behavior_report_from_evaluations(evaluations: List[str]):
    if not evaluations:
        return {"error": "No evaluations provided."}

    joined_evals = "\n".join([f"{i+1}. {ev}" for i, ev in enumerate(evaluations)])
    prompt = f"""
Generate a JSON report based on 5 behavioral insights.

Insights:
{joined_evals}

Return JSON only:
{{
  "Interest": "...",
  "Aptitude": "...",
  "Emotional": "...",
  "Motivation": "...",
  "Vision": "...",
  "CareerIQ360 Index": "x.x/10"
}}
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        max_tokens=600,
    )

    content = response.choices[0].message.content.strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except:
                return {"report": match.group()}
        return {"error": "Invalid JSON", "raw": content}


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
