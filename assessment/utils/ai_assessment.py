# import cohere
# import re
# from django.conf import settings

# # Initialize Cohere client
# co = cohere.Client(settings.COHERE_API_KEY)

# def clean_and_parse_question(text):
#     # Decode escape characters
#     cleaned = text.encode().decode('unicode_escape').strip()
#     lines = cleaned.split("\n")

#     question = ""
#     options = {}

#     for line in lines:
#         if line.lower().startswith("q:"):
#             question = line[2:].strip()
#         elif re.match(r"^[a-dA-D]\.", line.strip()):
#             key = line[0].lower()
#             val = line[2:].strip()
#             options[key] = val

#     return question, options

# def generate_question(theory_text, age_group, assessment_title, previous_qas):
#     prompt = f"""
# You are a smart educational AI. Your goal is to generate one behavior-assessment multiple-choice question based on:

# 1. The theory: {theory_text}
# 2. The age group of the user: {age_group}
# 3. The purpose of the assessment: {assessment_title}

# Ask questions that help understand the user's preferences or behaviors — do NOT ask factual or definition-based questions.

# Make sure the question is age-appropriate, engaging, and based on the learning theory.

# Previous Q&A history:
# {previous_qas if previous_qas else "None"}

# Format:
# Q: <behavior-based question>
# a. <option A>
# b. <option B>
# c. <option C>
# d. <option D>
# """

#     response = co.generate(
#         model="command-r-plus",
#         prompt=prompt,
#         max_tokens=300,
#         temperature=0.7,
#     )

#     raw_text = response.generations[0].text
#     question, options = clean_and_parse_question(raw_text)

#     return {
#         "question": question,
#         "options": options
#     }

# def evaluate_answer(question, answer, theory_text):
#     prompt = f"""
# Evaluate the answer provided for the question below based on the following theory. Return 'Correct' or 'Incorrect' and a short reason.

# Theory:
# {theory_text}

# Question:
# {question}

# User Answer:
# {answer}
# """

#     response = co.generate(
#         model="command-r-plus",
#         prompt=prompt,
#         max_tokens=150,
#         temperature=0.7,
#     )

#     return response.generations[0].text.strip()


# utils/ai_assessment.py

import openai
from django.conf import settings
import re

client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

def generate_question(theory_text, previous_qas):
    prompt = f"""
You are a smart educational AI designed to understand user behavior and preferences based on learning theories.

The goal is NOT to quiz the user about theory content. Instead, you should ask **reflective behavioral questions** that help infer the user's learning preferences, personality, or cognitive style, depending on the theory below.

Theory:
{theory_text}

Previous Questions and Answers:
{previous_qas if previous_qas else "None"}

Ask the next question in this format:

Q: <question>
A. <option A>
B. <option B>
C. <option C>
D. <option D>

Important:
- The question must be behavior-based.
- Do NOT mention the name of the theory in the question.
- Each option should reflect a different behavioral trait or preference related to the theory.
"""

    response = client.chat.completions.create(
        model="gpt-4o",  # 🔄 changed from gpt-3.5-turbo to gpt-4o
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=300,
    )

    raw_output = response.choices[0].message.content.strip()

    question_match = re.search(r"Q:\s*(.+)", raw_output)
    options = re.findall(r"[A-D]\.\s*(.+)", raw_output)

    if not question_match or len(options) != 4:
        return {
            "question": "Invalid question format received from AI.",
            "options": {},
        }

    question_text = question_match.group(1).strip()
    return {
        "question": question_text,
        "options": {
            "a": options[0].strip(),
            "b": options[1].strip(),
            "c": options[2].strip(),
            "d": options[3].strip(),
        }
    }


def evaluate_answer(question, answer, theory_text):
    prompt = f"""
Evaluate the answer provided for the question below based on the following theory. Return 'Correct' or 'Incorrect' and a short reason.

Theory:
{theory_text}

Question:
{question}

User Answer:
{answer}
"""

    response = client.chat.completions.create(
        model="gpt-4o",  # 🔄 changed from gpt-3.5-turbo to gpt-4o
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=300,
    )

    return response.choices[0].message.content
