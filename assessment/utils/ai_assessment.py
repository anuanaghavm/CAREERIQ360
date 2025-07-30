# ai_assessment.py

from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.schema import SystemMessage, HumanMessage
from .rag_utils import load_or_create_vectorstore
from typing import List
import openai
import os
import re
import json
from django.utils import timezone

MAX_QUESTIONS = 2

openai.api_key = os.getenv("OPENAI_API_KEY")  # Or use a hardcoded key temporarily
client = openai

def generate_question(theory_text, previous_qas, question_count, theory_id):
    if question_count >= MAX_QUESTIONS:
        return {"question": "You have completed all questions.", "options": {}}

    # Load FAISS and retrieve relevant theory chunks
    db = load_or_create_vectorstore(theory_id, theory_text)
    retriever = db.as_retriever()
    relevant_docs = retriever.get_relevant_documents("next behavioral question")

    context = "\n".join([doc.page_content for doc in relevant_docs])

    prompt = f"""
You are a smart educational AI designed to understand user behavior and preferences based on learning theories.

Relevant Theory:
{context}

Previous Q&A:
{previous_qas if previous_qas else "None"}

Ask the next question in this format:

Q: <question>
A. <option A>
B. <option B>
C. <option C>
D. <option D>
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=300,
    )

    raw_output = response.choices[0].message.content.strip()
    question_match = re.search(r"Q:\s*(.+)", raw_output)
    options = re.findall(r"[A-D]\.\s*(.+)", raw_output)

    if not question_match or len(options) != 4:
        return {"question": "Invalid format", "options": {}}

    return {
        "question": question_match.group(1).strip(),
        "options": {
            "a": options[0].strip(),
            "b": options[1].strip(),
            "c": options[2].strip(),
            "d": options[3].strip(),
        }
    }


def evaluate_answer(question, answer_text, theory_text, theory_id):
    db = load_or_create_vectorstore(theory_id, theory_text)
    retriever = db.as_retriever()
    docs = retriever.get_relevant_documents(question)
    context = "\n".join([doc.page_content for doc in docs])

    prompt = f"""
Evaluate the answer based on this theory segment:

Theory Context:
{context}

Question:
{question}

Answer:
{answer_text}

What does this answer tell about the user?
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=300,
    )

    return response.choices[0].message.content.strip()

def generate_behavior_report_from_evaluations(evaluations: List[str]):
    if not evaluations:
        return {"error": "No evaluations available."}

    joined_evals = "\n".join([f"{i+1}. {ev}" for i, ev in enumerate(evaluations)])

    prompt = f"""
You are a student assessment AI. Based on the following evaluations from 5 behavioral tests, create a final summary report.

Each evaluation gives insights into a student's:
- Interest
- Aptitude
- Emotional intelligence
- Motivation
- Vision

Return the report in **pure JSON format** (no markdown, no triple backticks).

Format example:
{{
  "Interest": "92% - comment...",
  "Aptitude": "88% - comment...",
  "Emotional": "85% - comment...",
  "Motivation": "89% - comment...",
  "Vision": "91% - comment...",
  "CareerIQ360 Index": "8.7/10"
}}

Evaluations:
{joined_evals}
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        max_tokens=500,
    )

    content = response.choices[0].message.content.strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # Try to extract JSON manually in case of formatting issues
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except:
                pass
        return {"report": content}

