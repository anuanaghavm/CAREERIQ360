# ai_assessment.py - Key changes for timeout handling
import openai
import os
import re
import json
from typing import List, Dict,Any
from langchain_community.vectorstores import FAISS  # Updated import
from langchain_community.embeddings import OpenAIEmbeddings  # Updated import
from langchain_community.chat_models import ChatOpenAI  # Updated import
from .rag_utils import load_or_create_vectorstore
import openai
import os
import time
import httpx

# Configure OpenAI client with timeout
openai.api_key = os.getenv("OPENAI_API_KEY")

# Create client with timeout settings
client = openai.OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    timeout=httpx.Timeout(60.0, connect=10.0),  # 60s total, 10s connect
    max_retries=2
)

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
    """Fetch questions with retry logic and timeout handling"""
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": batch_prompt}],
                temperature=0.6,
                max_tokens=3000,
                timeout=60  # 60 second timeout
            )
            return response.choices[0].message.content.strip()
            
        except openai.TimeoutError as e:
            print(f"Attempt {attempt + 1}: OpenAI timeout error: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
                continue
            raise Exception(f"OpenAI API timeout after {max_retries} attempts")
            
        except openai.RateLimitError as e:
            print(f"Attempt {attempt + 1}: Rate limit error: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay * 2)  # Longer wait for rate limits
                retry_delay *= 2
                continue
            raise Exception(f"OpenAI rate limit exceeded after {max_retries} attempts")
            
        except Exception as e:
            print(f"Attempt {attempt + 1}: Unexpected error: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            raise Exception(f"Failed to fetch questions after {max_retries} attempts: {str(e)}")

def generate_questions(test_name: str, section_name: str = "Middle School(13-15)", total: int = 30):
    """Generate exactly 30 questions for the given test with timeout handling"""
    print(f"Starting question generation for {test_name}")
    start_time = time.time()
    
    test_info = STATIC_TESTS[test_name]
    theory_text = test_info["theory"]
    theory_id = test_info["theory_id"]
    prompt_intro = test_info.get("prompt", "")

    # Get context from vectorstore with timeout protection
    try:
        db = get_vectorstore(theory_id, theory_text)
        docs = db.as_retriever().invoke("behavioral question")  # Updated method
        context = "\n".join(doc.page_content for doc in docs[:3])
    except Exception as e:
        print(f"Error getting vectorstore context: {e}")
        context = theory_text  # Fallback to theory text

    all_questions = []
    max_attempts = 2  # Reduced attempts to prevent long waits

    for attempt in range(max_attempts):
        print(f"Generation attempt {attempt + 1}")
        
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
                model="gpt-4o",
                messages=[{"role": "user", "content": full_prompt}],
                temperature=0.6,
                max_tokens=4000,
                timeout=90  # 90 second timeout for large generation
            )

            content = response.choices[0].message.content.strip()
            questions = parse_questions_from_content(content)
            
            if len(questions) >= total:
                all_questions = questions[:total]
                break
            else:
                print(f"Attempt {attempt + 1}: Only got {len(questions)} questions")
                all_questions.extend(questions)
                
        except Exception as e:
            print(f"Error in generation attempt {attempt + 1}: {e}")
            if attempt == max_attempts - 1:
                # On final attempt, return what we have or raise error
                if len(all_questions) == 0:
                    raise Exception(f"Failed to generate any questions: {str(e)}")
            continue

    # Ensure we have at least some questions
    if len(all_questions) < total and len(all_questions) > 0:
        print(f"Warning: Only generated {len(all_questions)} questions instead of {total}")
    
    final_questions = all_questions[:total] if all_questions else []
    
    elapsed_time = time.time() - start_time
    print(f"Generated {len(final_questions)} questions for {test_name} in {elapsed_time:.2f} seconds")
    
    return final_questions

# Keep your existing parse_questions_from_content function unchanged
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

def evaluate_answers(test_name: str, qas_with_answers: List[dict], section_name: str = "middle"):
    """Evaluate answers with timeout handling"""
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

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=1500,
            timeout=60
        )

        lines = response.choices[0].message.content.strip().split("\n")
        return [line.partition(".")[2].strip() for line in lines if "." in line]
        
    except Exception as e:
        print(f"Error in evaluate_answers: {e}")
        return [f"Evaluation temporarily unavailable" for _ in qas_with_answers]

# def generate_detailed_assessment_report(test_name, test_description, theory_description, qas: List[dict]):
#     """Generate report with timeout handling"""
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

#     try:
#         response = client.chat.completions.create(
#             model="gpt-4o",
#             messages=[{"role": "user", "content": prompt}],
#             temperature=0.5,
#             max_tokens=600,
#             timeout=60
#         )

#         return response.choices[0].message.content.strip()
        
#     except Exception as e:
#         print(f"Error generating report: {e}")
#         return "Assessment report temporarily unavailable. Please try again later."

def analyze_learning_style_breakdown(qas: List[dict], test_name: str) -> Dict[str, Any]:
    """Analyze answers to determine learning style percentages and breakdowns"""
    
    if test_name == "NeuroStyle Index":
        return analyze_neurostyle_breakdown(qas)
    elif test_name == "Cognitive Spark":
        return analyze_cognitive_spark_breakdown(qas)
    elif test_name == "Emerging Identity Map":
        return analyze_identity_breakdown(qas)
    elif test_name == "Pathfinder RIASEC-Lite":
        return analyze_riasec_breakdown(qas)
    elif test_name == "FutureScope":
        return analyze_futurescope_breakdown(qas)
    
    return {}

def analyze_neurostyle_breakdown(qas: List[dict]) -> Dict[str, Any]:
    """Analyze NeuroStyle Index responses for VARK learning styles"""
    
    # Count responses by pattern (you'll need to map your answers to these categories)
    visual_count = 0
    auditory_count = 0
    kinesthetic_count = 0
    reading_writing_count = 0
    creative_thinking_count = 0
    
    # Analyze each answer (simplified logic - you'll need to enhance this)
    for qa in qas:
        if qa.get("answer"):
            answer = qa["answer"].lower()
            
            # Simple keyword matching (enhance with your specific answer patterns)
            if any(word in answer for word in ["see", "visual", "diagram", "chart", "picture", "watch"]):
                visual_count += 1
            elif any(word in answer for word in ["hear", "listen", "discuss", "talk", "explain", "audio"]):
                auditory_count += 1
            elif any(word in answer for word in ["hands-on", "practice", "try", "do", "movement", "touch"]):
                kinesthetic_count += 1
            elif any(word in answer for word in ["read", "write", "notes", "text", "list"]):
                reading_writing_count += 1
            elif any(word in answer for word in ["create", "creative", "brainstorm", "innovative"]):
                creative_thinking_count += 1
    
    total_answers = len([qa for qa in qas if qa.get("answer")])
    
    if total_answers == 0:
        return {}
    
    # Calculate percentages
    visual_pct = round((visual_count / total_answers) * 100)
    auditory_pct = round((auditory_count / total_answers) * 100)
    kinesthetic_pct = round((kinesthetic_count / total_answers) * 100)
    creative_pct = round((creative_thinking_count / total_answers) * 100)
    
    # Determine primary characteristics
    growth_potential = "High" if (visual_pct + auditory_pct + kinesthetic_pct) > 70 else "Medium"
    collaboration_style = "Balanced" if abs(visual_pct - auditory_pct) < 15 else "Specialized"
    learning_approach = "Multi-modal" if len([x for x in [visual_pct, auditory_pct, kinesthetic_pct] if x > 20]) >= 2 else "Focused"
    focus_areas = "Strategic" if creative_pct > 25 else "Systematic"
    
    return {
        "test_type": "NeuroStyle Index",
        "breakdown": {
            "Visual Learning": {
                "percentage": f"{visual_pct}%",
                "description": "Learns through visual aids and written information",
                "color_class": "visual"
            },
            "Auditory Learning": {
                "percentage": f"{auditory_pct}%", 
                "description": "Learns through listening and verbal instruction",
                "color_class": "auditory"
            },
            "Kinesthetic Learning": {
                "percentage": f"{kinesthetic_pct}%",
                "description": "Learns through hands-on experience and movement", 
                "color_class": "kinesthetic"
            },
            "Creative Thinking": {
                "percentage": f"{creative_pct}%",
                "description": "Learns through creative problem-solving approaches",
                "color_class": "creative"
            }
        },
        "characteristics": {
            "Growth Potential": {
                "value": growth_potential,
                "description": "Strong adaptability across learning contexts",
                "color": "green"
            },
            "Collaboration Style": {
                "value": collaboration_style,
                "description": "Effective in both individual and group settings",
                "color": "blue"
            },
            "Learning Approach": {
                "value": learning_approach,
                "description": "Integrates visual, auditory, and kinesthetic elements",
                "color": "purple"
            },
            "Focus Areas": {
                "value": focus_areas,
                "description": "Demonstrates systematic problem-solving approach",
                "color": "orange"
            }
        }
    }

def analyze_cognitive_spark_breakdown(qas: List[dict]) -> Dict[str, Any]:
    """Analyze Cognitive Spark for Gardner's Multiple Intelligences"""
    
    # Intelligence counters
    intelligence_counts = {
        "Linguistic": 0,
        "Logical-Mathematical": 0, 
        "Spatial": 0,
        "Musical": 0,
        "Bodily-Kinesthetic": 0,
        "Interpersonal": 0,
        "Intrapersonal": 0,
        "Naturalistic": 0
    }
    
    # Analyze answers for intelligence patterns
    for qa in qas:
        if qa.get("answer"):
            answer = qa["answer"].lower()
            
            # Keywords for each intelligence (enhance with your specific patterns)
            if any(word in answer for word in ["words", "reading", "writing", "language", "stories"]):
                intelligence_counts["Linguistic"] += 1
            elif any(word in answer for word in ["numbers", "math", "logic", "patterns", "problem"]):
                intelligence_counts["Logical-Mathematical"] += 1
            elif any(word in answer for word in ["visual", "art", "design", "space", "picture"]):
                intelligence_counts["Spatial"] += 1
            elif any(word in answer for word in ["music", "rhythm", "sound", "melody", "sing"]):
                intelligence_counts["Musical"] += 1
            elif any(word in answer for word in ["sports", "movement", "hands-on", "physical", "build"]):
                intelligence_counts["Bodily-Kinesthetic"] += 1
            elif any(word in answer for word in ["people", "friends", "social", "help", "team"]):
                intelligence_counts["Interpersonal"] += 1
            elif any(word in answer for word in ["self", "alone", "reflect", "independent", "think"]):
                intelligence_counts["Intrapersonal"] += 1
            elif any(word in answer for word in ["nature", "animals", "environment", "outdoors", "plants"]):
                intelligence_counts["Naturalistic"] += 1
    
    total_answers = len([qa for qa in qas if qa.get("answer")])
    
    if total_answers == 0:
        return {}
    
    # Calculate percentages and find top intelligences
    intelligence_percentages = {}
    for intelligence, count in intelligence_counts.items():
        intelligence_percentages[intelligence] = round((count / total_answers) * 100)
    
    # Sort by percentage to get top intelligences
    sorted_intelligences = sorted(intelligence_percentages.items(), key=lambda x: x[1], reverse=True)
    
    # Create breakdown for top 4 intelligences
    breakdown = {}
    colors = ["blue", "green", "purple", "orange"]
    
    for i, (intelligence, percentage) in enumerate(sorted_intelligences[:4]):
        breakdown[intelligence] = {
            "percentage": f"{percentage}%",
            "description": get_intelligence_description(intelligence),
            "color_class": colors[i % len(colors)]
        }
    
    return {
        "test_type": "Cognitive Spark",
        "breakdown": breakdown,
        "characteristics": {
            "Dominant Intelligence": {
                "value": sorted_intelligences[0][0],
                "description": f"Primary strength in {sorted_intelligences[0][0].lower()} intelligence",
                "color": "green"
            },
            "Learning Profile": {
                "value": "Multi-faceted" if len([x for x in intelligence_percentages.values() if x > 15]) >= 3 else "Specialized",
                "description": "Shows diverse cognitive strengths",
                "color": "blue"
            },
            "Development Focus": {
                "value": "Balanced",
                "description": "Strong foundation across multiple intelligence areas",
                "color": "purple"
            }
        }
    }

def get_intelligence_description(intelligence: str) -> str:
    """Get description for each intelligence type"""
    descriptions = {
        "Linguistic": "Strength with words, language, reading, and writing",
        "Logical-Mathematical": "Skill with numbers, logic, patterns, and reasoning",
        "Spatial": "Visual and artistic abilities, design and navigation skills", 
        "Musical": "Sensitivity to rhythm, melody, and musical patterns",
        "Bodily-Kinesthetic": "Physical coordination and hands-on learning",
        "Interpersonal": "Understanding others and strong social skills",
        "Intrapersonal": "Self-awareness, reflection, and independence",
        "Naturalistic": "Connection with nature and environmental patterns"
    }
    return descriptions.get(intelligence, "Cognitive strength area")

def analyze_identity_breakdown(qas: List[dict]) -> Dict[str, Any]:
    """Analyze Emerging Identity Map responses for MBTI-style dimensions"""
    
    # MBTI dimension counters
    dimension_counts = {
        "Extraversion": 0,
        "Introversion": 0,
        "Sensing": 0,
        "Intuition": 0,
        "Thinking": 0,
        "Feeling": 0,
        "Judging": 0,
        "Perceiving": 0
    }
    
    # Analyze answers for personality patterns
    for qa in qas:
        if qa.get("answer"):
            answer = qa["answer"].lower()
            
            # Keywords for MBTI dimensions (enhance with your specific patterns)
            if any(word in answer for word in ["social", "group", "friends", "party", "outgoing", "energized by people"]):
                dimension_counts["Extraversion"] += 1
            elif any(word in answer for word in ["quiet", "alone", "private", "solitude", "independent", "small group"]):
                dimension_counts["Introversion"] += 1
            elif any(word in answer for word in ["practical", "concrete", "facts", "details", "experience", "realistic"]):
                dimension_counts["Sensing"] += 1
            elif any(word in answer for word in ["ideas", "possibilities", "future", "creative", "theoretical", "innovative"]):
                dimension_counts["Intuition"] += 1
            elif any(word in answer for word in ["logical", "objective", "analyze", "fair", "criticism", "rational"]):
                dimension_counts["Thinking"] += 1
            elif any(word in answer for word in ["feelings", "harmony", "values", "personal", "empathy", "compassion"]):
                dimension_counts["Feeling"] += 1
            elif any(word in answer for word in ["organized", "planned", "schedule", "structure", "decided", "closure"]):
                dimension_counts["Judging"] += 1
            elif any(word in answer for word in ["flexible", "spontaneous", "adapt", "open", "options", "last-minute"]):
                dimension_counts["Perceiving"] += 1
    
    total_answers = len([qa for qa in qas if qa.get("answer")])
    
    if total_answers == 0:
        return {}
    
    # Calculate percentages for primary dimensions
    extraversion_pct = round((dimension_counts["Extraversion"] / (dimension_counts["Extraversion"] + dimension_counts["Introversion"] + 1)) * 100)
    intuition_pct = round((dimension_counts["Intuition"] / (dimension_counts["Intuition"] + dimension_counts["Sensing"] + 1)) * 100)
    feeling_pct = round((dimension_counts["Feeling"] / (dimension_counts["Feeling"] + dimension_counts["Thinking"] + 1)) * 100)
    perceiving_pct = round((dimension_counts["Perceiving"] / (dimension_counts["Perceiving"] + dimension_counts["Judging"] + 1)) * 100)
    
    # Determine personality tendencies
    energy_source = "Extraversion" if dimension_counts["Extraversion"] > dimension_counts["Introversion"] else "Introversion"
    info_processing = "Intuition" if dimension_counts["Intuition"] > dimension_counts["Sensing"] else "Sensing"
    decision_making = "Feeling" if dimension_counts["Feeling"] > dimension_counts["Thinking"] else "Thinking"
    life_approach = "Perceiving" if dimension_counts["Perceiving"] > dimension_counts["Judging"] else "Judging"
    
    return {
        "test_type": "Emerging Identity Map",
        "breakdown": {
            f"{energy_source} Tendency": {
                "percentage": f"{extraversion_pct if energy_source == 'Extraversion' else 100-extraversion_pct}%",
                "description": f"Primary energy source and social orientation",
                "color_class": "energy"
            },
            f"{info_processing} Processing": {
                "percentage": f"{intuition_pct if info_processing == 'Intuition' else 100-intuition_pct}%",
                "description": "How you naturally take in and process information",
                "color_class": "processing"
            },
            f"{decision_making} Decisions": {
                "percentage": f"{feeling_pct if decision_making == 'Feeling' else 100-feeling_pct}%",
                "description": "Your natural approach to making decisions",
                "color_class": "decisions"
            },
            f"{life_approach} Structure": {
                "percentage": f"{perceiving_pct if life_approach == 'Perceiving' else 100-perceiving_pct}%",
                "description": "How you prefer to organize your outer world",
                "color_class": "structure"
            }
        },
        "characteristics": {
            "Identity Formation": {
                "value": "Developing",
                "description": "Actively exploring personal identity and values",
                "color": "purple"
            },
            "Social Confidence": {
                "value": "Growing" if extraversion_pct > 60 else "Reflective",
                "description": "Comfortable with social interactions and group settings",
                "color": "blue"
            },
            "Decision Style": {
                "value": "Values-based" if feeling_pct > 50 else "Logic-based",
                "description": "Considers personal values and impact on others",
                "color": "green"
            },
            "Adaptability": {
                "value": "Flexible" if perceiving_pct > 50 else "Structured",
                "description": "Open to new experiences and changing plans",
                "color": "orange"
            }
        }
    }

def analyze_riasec_breakdown(qas: List[dict]) -> Dict[str, Any]:
    """Analyze Pathfinder RIASEC-Lite responses for Holland Code interests"""
    
    # RIASEC counters
    riasec_counts = {
        "Realistic": 0,
        "Investigative": 0,
        "Artistic": 0,
        "Social": 0,
        "Enterprising": 0,
        "Conventional": 0
    }
    
    # Analyze answers for RIASEC patterns
    for qa in qas:
        if qa.get("answer"):
            answer = qa["answer"].lower()
            
            # Keywords for RIASEC types (enhance with your specific patterns)
            if any(word in answer for word in ["build", "fix", "tools", "mechanical", "hands-on", "outdoors", "practical"]):
                riasec_counts["Realistic"] += 1
            elif any(word in answer for word in ["research", "analyze", "science", "investigate", "study", "data", "theory"]):
                riasec_counts["Investigative"] += 1
            elif any(word in answer for word in ["creative", "art", "design", "music", "write", "express", "imaginative"]):
                riasec_counts["Artistic"] += 1
            elif any(word in answer for word in ["help", "teach", "care", "counsel", "people", "serve", "support"]):
                riasec_counts["Social"] += 1
            elif any(word in answer for word in ["lead", "sell", "manage", "persuade", "compete", "organize", "business"]):
                riasec_counts["Enterprising"] += 1
            elif any(word in answer for word in ["organize", "detail", "system", "procedure", "accurate", "office", "data"]):
                riasec_counts["Conventional"] += 1
    
    total_answers = len([qa for qa in qas if qa.get("answer")])
    
    if total_answers == 0:
        return {}
    
    # Calculate percentages and find top interests
    riasec_percentages = {}
    for interest, count in riasec_counts.items():
        riasec_percentages[interest] = round((count / total_answers) * 100)
    
    # Sort by percentage to get top interests
    sorted_interests = sorted(riasec_percentages.items(), key=lambda x: x[1], reverse=True)
    
    # Create breakdown for top 4 interests
    breakdown = {}
    colors = ["blue", "green", "purple", "orange"]
    
    for i, (interest, percentage) in enumerate(sorted_interests[:4]):
        breakdown[interest] = {
            "percentage": f"{percentage}%",
            "description": get_riasec_description(interest),
            "color_class": colors[i % len(colors)]
        }
    
    return {
        "test_type": "Pathfinder RIASEC-Lite",
        "breakdown": breakdown,
        "characteristics": {
            "Primary Interest": {
                "value": sorted_interests[0][0],
                "description": f"Strongest interest in {sorted_interests[0][0].lower()} activities",
                "color": "green"
            },
            "Career Focus": {
                "value": get_career_focus(sorted_interests[:2]),
                "description": "Suggested career exploration areas",
                "color": "blue"
            },
            "Work Environment": {
                "value": get_work_environment(sorted_interests[0][0]),
                "description": "Preferred work setting and activities",
                "color": "purple"
            },
            "Interest Pattern": {
                "value": "Diverse" if len([x for x in riasec_percentages.values() if x > 15]) >= 3 else "Focused",
                "description": "Range of career interests and exploration areas",
                "color": "orange"
            }
        }
    }

def get_riasec_description(interest: str) -> str:
    """Get description for each RIASEC type"""
    descriptions = {
        "Realistic": "Hands-on, practical work with tools and machines",
        "Investigative": "Research, analysis, and scientific problem-solving",
        "Artistic": "Creative expression, design, and imaginative work",
        "Social": "Helping, teaching, and working with people",
        "Enterprising": "Leading, persuading, and business activities",
        "Conventional": "Organizing, detail work, and systematic tasks"
    }
    return descriptions.get(interest, "Career interest area")

def get_career_focus(top_interests: List[tuple]) -> str:
    """Determine career focus based on top 2 interests"""
    if len(top_interests) < 2:
        return "Specialized"
    
    combinations = {
        ("Realistic", "Investigative"): "Technical",
        ("Realistic", "Conventional"): "Skilled Trades",
        ("Investigative", "Artistic"): "Creative Research",
        ("Artistic", "Social"): "Creative Services",
        ("Social", "Enterprising"): "People Leadership",
        ("Enterprising", "Conventional"): "Business Management"
    }
    
    combo = (top_interests[0][0], top_interests[1][0])
    reverse_combo = (top_interests[1][0], top_interests[0][0])
    
    return combinations.get(combo, combinations.get(reverse_combo, "Multifaceted"))

def get_work_environment(primary_interest: str) -> str:
    """Get preferred work environment for primary interest"""
    environments = {
        "Realistic": "Hands-on Workshop",
        "Investigative": "Research Laboratory",
        "Artistic": "Creative Studio",
        "Social": "People-Centered",
        "Enterprising": "Dynamic Business",
        "Conventional": "Structured Office"
    }
    return environments.get(primary_interest, "Flexible")

def analyze_futurescope_breakdown(qas: List[dict]) -> Dict[str, Any]:
    """Analyze FutureScope responses for grit and resilience patterns"""
    
    # Grit and resilience counters
    grit_dimensions = {
        "High_Perseverance": 0,
        "Medium_Perseverance": 0,
        "Low_Perseverance": 0,
        "Growth_Mindset": 0,
        "Fixed_Mindset": 0,
        "High_Resilience": 0,
        "Medium_Resilience": 0,
        "Passion_Consistency": 0,
        "Adaptability": 0
    }
    
    # Analyze answers for grit patterns
    for qa in qas:
        if qa.get("answer"):
            answer = qa["answer"].lower()
            
            # Keywords for grit and resilience (enhance with your specific patterns)
            if any(word in answer for word in ["keep trying", "never give up", "practice more", "work harder", "persist"]):
                grit_dimensions["High_Perseverance"] += 1
            elif any(word in answer for word in ["try again", "keep going", "don't quit", "continue"]):
                grit_dimensions["Medium_Perseverance"] += 1
            elif any(word in answer for word in ["give up", "quit", "stop", "too hard"]):
                grit_dimensions["Low_Perseverance"] += 1
            elif any(word in answer for word in ["learn from", "improve", "get better", "practice", "develop"]):
                grit_dimensions["Growth_Mindset"] += 1
            elif any(word in answer for word in ["not good at", "can't do", "not talented", "born with"]):
                grit_dimensions["Fixed_Mindset"] += 1
            elif any(word in answer for word in ["bounce back", "recover", "overcome", "find another way"]):
                grit_dimensions["High_Resilience"] += 1
            elif any(word in answer for word in ["passionate", "love", "committed", "dedicated"]):
                grit_dimensions["Passion_Consistency"] += 1
            elif any(word in answer for word in ["adapt", "flexible", "change approach", "try different"]):
                grit_dimensions["Adaptability"] += 1
    
    total_answers = len([qa for qa in qas if qa.get("answer")])
    
    if total_answers == 0:
        return {}
    
    # Calculate grit level
    high_grit = grit_dimensions["High_Perseverance"] + grit_dimensions["Growth_Mindset"] + grit_dimensions["High_Resilience"]
    medium_grit = grit_dimensions["Medium_Perseverance"] + grit_dimensions["Adaptability"]
    low_grit = grit_dimensions["Low_Perseverance"] + grit_dimensions["Fixed_Mindset"]
    
    grit_level = "High" if high_grit > medium_grit and high_grit > low_grit else ("Medium" if medium_grit > low_grit else "Developing")
    
    # Calculate percentages
    perseverance_pct = round(((grit_dimensions["High_Perseverance"] + grit_dimensions["Medium_Perseverance"]) / total_answers) * 100)
    growth_mindset_pct = round((grit_dimensions["Growth_Mindset"] / total_answers) * 100)
    resilience_pct = round((grit_dimensions["High_Resilience"] / total_answers) * 100)
    passion_pct = round((grit_dimensions["Passion_Consistency"] / total_answers) * 100)
    
    return {
        "test_type": "FutureScope",
        "breakdown": {
            "Perseverance": {
                "percentage": f"{perseverance_pct}%",
                "description": "Persistence in facing challenges and setbacks",
                "color_class": "perseverance"
            },
            "Growth Mindset": {
                "percentage": f"{growth_mindset_pct}%",
                "description": "Belief that abilities can be developed through effort",
                "color_class": "growth"
            },
            "Resilience": {
                "percentage": f"{resilience_pct}%",
                "description": "Ability to bounce back from failures and setbacks",
                "color_class": "resilience"
            },
            "Passion": {
                "percentage": f"{passion_pct}%",
                "description": "Consistency of interests and long-term commitment",
                "color_class": "passion"
            }
        },
        "characteristics": {
            "Overall Grit": {
                "value": grit_level,
                "description": "Combined measure of perseverance and passion",
                "color": "green" if grit_level == "High" else "blue"
            },
            "Mindset": {
                "value": "Growth-Oriented" if growth_mindset_pct > 60 else "Developing",
                "description": "Approach to learning and ability development",
                "color": "purple"
            },
            "Challenge Response": {
                "value": "Resilient" if resilience_pct > 50 else "Learning",
                "description": "How you typically respond to difficulties",
                "color": "orange"
            },
            "Future Readiness": {
                "value": "Strong" if perseverance_pct > 70 else "Building",
                "description": "Preparedness for future challenges and goals",
                "color": "blue"
            }
        }
    }

def generate_comprehensive_assessment_report(test_name: str, test_description: str, theory_description: str, qas: List[dict]) -> Dict[str, Any]:
    """Generate comprehensive structured assessment report"""
    
    # Get breakdown analysis
    breakdown_data = analyze_learning_style_breakdown(qas, test_name)
    
    # Generate insights and recommendations
    insights = generate_insights_from_breakdown(breakdown_data, qas)
    recommendations = generate_personalized_recommendations(breakdown_data, test_name)
    
    # Create comprehensive report structure
    comprehensive_report = {
        "test_name": test_name,
        "test_description": test_description, 
        "theory_description": theory_description,
        "assessment_overview": generate_assessment_overview(breakdown_data, qas),
        "breakdown": breakdown_data.get("breakdown", {}),
        "characteristics": breakdown_data.get("characteristics", {}),
        "insights": insights,
        "recommendations": recommendations,
        "strengths_capabilities": generate_strengths_analysis(breakdown_data, qas),
        "complete_report": generate_narrative_summary(breakdown_data, insights, qas)
    }
    
    return comprehensive_report

def generate_assessment_overview(breakdown_data: Dict, qas: List[dict]) -> str:
    """Generate overview paragraph similar to the dashboard"""
    
    answered_count = len([qa for qa in qas if qa.get("answer")])
    test_type = breakdown_data.get("test_type", "Assessment")
    
    if test_type == "NeuroStyle Index":
        return f"The NeuroStyle Index assessment reveals a diverse array of learning preferences and cognitive strengths, highlighting a multi-faceted approach to learning. The individual exhibits a strong inclination towards both visual and auditory learning styles, frequently engaging with written texts, visual aids, and auditory activities such as lectures and discussions."
    
    elif test_type == "Cognitive Spark":
        return f"The Cognitive Spark assessment identifies multiple intelligence strengths across Gardner's framework, revealing diverse cognitive abilities and learning preferences. The individual demonstrates varied intellectual capabilities with particular strengths in specific intelligence areas, suggesting a multifaceted cognitive profile."
    
    elif test_type == "Emerging Identity Map":
        return f"The Emerging Identity Map assessment explores personality development and identity formation patterns typical of adolescence. The individual shows emerging preferences in social energy, information processing, decision-making approaches, and life organization styles, indicating healthy identity exploration and development."
    
    elif test_type == "Pathfinder RIASEC-Lite":
        return f"The Pathfinder RIASEC-Lite assessment maps career interests and work preferences across Holland's six career themes. The individual demonstrates clear interest patterns that can guide future educational and career exploration decisions, highlighting natural preferences for specific types of work environments and activities."
    
    elif test_type == "FutureScope":
        return f"The FutureScope assessment measures resilience, grit, and future readiness through various challenging scenarios. The individual demonstrates specific patterns in perseverance, growth mindset, and adaptability that indicate their preparedness for future challenges and long-term goal achievement."
    
    return f"This {test_type} assessment provides insights into learning preferences and cognitive patterns based on {answered_count} completed responses."

def generate_insights_from_breakdown(breakdown_data: Dict, qas: List[dict]) -> str:
    """Generate insights paragraph"""
    
    if not breakdown_data.get("breakdown"):
        return "Insights will be generated based on assessment responses."
    
    breakdown = breakdown_data["breakdown"]
    top_areas = sorted(breakdown.items(), key=lambda x: int(x[1]["percentage"].rstrip('%')), reverse=True)[:2]
    
    if len(top_areas) >= 2:
        area1, data1 = top_areas[0]
        area2, data2 = top_areas[1]
        
        return f"This suggests a balanced integration of {area1.lower()} and {area2.lower()} in their learning strategy. Additionally, the preference for hands-on experiments and practical exercises indicates a kinesthetic learning style, emphasizing experiential learning through physical engagement."
    
    return "Analysis suggests a balanced approach to learning with diverse cognitive strengths."

def generate_personalized_recommendations(breakdown_data: Dict, test_name: str) -> List[Dict[str, Any]]:
    """Generate personalized recommendations"""
    
    recommendations = []
    
    if test_name == "NeuroStyle Index":
        recommendations = [
            {
                "title": "Create a Multi-Sensory Learning Space",
                "description": "Set up a study area that incorporates visual aids, background music, and hands-on materials to match your diverse learning preferences.",
                "priority": "High Priority",
                "category": "Study Environment",
                "action": "Take action"
            },
            {
                "title": "Implement Active Learning Techniques", 
                "description": "Use mind mapping, interactive exercises, and group discussions to engage multiple learning modalities simultaneously.",
                "priority": "Medium Priority",
                "category": "Learning Strategy", 
                "action": "Take action"
            },
            {
                "title": "Practice Collaborative Problem-Solving",
                "description": "Join study groups or collaborative projects to leverage your balanced approach to individual and group learning.",
                "priority": "Medium Priority",
                "category": "Skill Development",
                "action": "Take action"
            }
        ]
    
    elif test_name == "Cognitive Spark":
        recommendations = [
            {
                "title": "Develop Your Dominant Intelligence",
                "description": "Focus on activities and learning opportunities that strengthen your primary intelligence area while maintaining others.",
                "priority": "High Priority",
                "category": "Intelligence Development",
                "action": "Take action"
            },
            {
                "title": "Cross-Intelligence Learning Projects",
                "description": "Engage in projects that combine multiple intelligences to maximize your diverse cognitive strengths.",
                "priority": "Medium Priority",
                "category": "Skill Integration",
                "action": "Take action"
            },
            {
                "title": "Explore Intelligence-Based Activities",
                "description": "Participate in clubs, hobbies, and courses that align with your strongest intelligence areas.",
                "priority": "Medium Priority",
                "category": "Extracurricular Activities",
                "action": "Take action"
            }
        ]
    
    elif test_name == "Emerging Identity Map":
        recommendations = [
            {
                "title": "Identity Exploration Activities",
                "description": "Engage in diverse experiences, volunteer work, and new activities to continue exploring your developing identity.",
                "priority": "High Priority",
                "category": "Personal Development",
                "action": "Take action"
            },
            {
                "title": "Reflect on Personal Values",
                "description": "Keep a journal or engage in regular self-reflection to better understand your evolving values and beliefs.",
                "priority": "Medium Priority",
                "category": "Self-Awareness",
                "action": "Take action"
            },
            {
                "title": "Build Social Confidence",
                "description": "Practice social skills and gradually expand your comfort zone in group settings and leadership opportunities.",
                "priority": "Medium Priority",
                "category": "Social Skills",
                "action": "Take action"
            }
        ]
    
    elif test_name == "Pathfinder RIASEC-Lite":
        recommendations = [
            {
                "title": "Career Exploration Activities",
                "description": "Participate in job shadowing, internships, or informational interviews in your areas of highest interest.",
                "priority": "High Priority",
                "category": "Career Exploration",
                "action": "Take action"
            },
            {
                "title": "Skills Development in Interest Areas",
                "description": "Take courses, join clubs, or pursue certifications related to your primary career interest themes.",
                "priority": "Medium Priority",
                "category": "Skill Building",
                "action": "Take action"
            },
            {
                "title": "Build a Career Portfolio",
                "description": "Start documenting experiences, projects, and skills related to your career interests for future applications.",
                "priority": "Medium Priority",
                "category": "Portfolio Development",
                "action": "Take action"
            }
        ]
    
    elif test_name == "FutureScope":
        recommendations = [
            {
                "title": "Set Long-term Goals",
                "description": "Practice setting and working toward challenging, long-term goals to build grit and perseverance.",
                "priority": "High Priority",
                "category": "Goal Setting",
                "action": "Take action"
            },
            {
                "title": "Develop Growth Mindset Practices",
                "description": "Focus on learning from failures and viewing challenges as opportunities to grow and improve.",
                "priority": "Medium Priority",
                "category": "Mindset Development",
                "action": "Take action"
            },
            {
                "title": "Build Resilience Skills",
                "description": "Practice stress management, problem-solving strategies, and seeking support when facing difficulties.",
                "priority": "Medium Priority",
                "category": "Resilience Building",
                "action": "Take action"
            }
        ]
    
    return recommendations

def generate_strengths_analysis(breakdown_data: Dict, qas: List[dict]) -> str:
    """Generate strengths and capabilities analysis"""
    
    test_type = breakdown_data.get("test_type", "Assessment")
    
    if test_type == "NeuroStyle Index":
        return "The individual also demonstrates a strategic and adaptive problem-solving approach, often utilizing brainstorming and cognitive mapping techniques, which underscores their creative and collaborative mindset. Furthermore, the preference for structured environments and methodical study habits, such as reading and summarizing notes, suggests a systematic and organized approach to learning. This blend of learning styles and problem-solving strategies positions the individual as a versatile learner capable of adapting to different educational contexts and challenges."
    
    elif test_type == "Cognitive Spark":
        return "The individual demonstrates exceptional cognitive versatility across multiple intelligence domains, showing particular strength in their dominant areas while maintaining competency in others. This multifaceted intellectual profile suggests strong potential for complex problem-solving and creative thinking. The ability to draw upon diverse cognitive strengths positions them well for interdisciplinary learning and innovative approaches to challenges."
    
    elif test_type == "Emerging Identity Map":
        return "The individual shows healthy identity development with emerging clarity in personal preferences and decision-making styles. Their developing self-awareness and growing confidence in social situations indicate positive psychological development. The balanced approach to different personality dimensions suggests flexibility and adaptability during this crucial developmental period."
    
    elif test_type == "Pathfinder RIASEC-Lite":
        return "The individual demonstrates clear career interest patterns that align well with specific work environments and activities. Their interest profile suggests natural motivation and engagement in certain types of tasks and settings. This clarity of interests, combined with diverse secondary interests, provides a strong foundation for career exploration and educational planning."
    
    elif test_type == "FutureScope":
        return "The individual exhibits strong foundational resilience and grit characteristics that bode well for future success and goal achievement. Their approach to challenges demonstrates developing emotional intelligence and problem-solving capabilities. The combination of perseverance, growth mindset, and adaptability creates a robust foundation for navigating future academic and personal challenges."
    
    return "The individual demonstrates developing strengths and capabilities across multiple assessment dimensions, suggesting positive growth and potential for continued development."

def generate_narrative_summary(breakdown_data: Dict, insights: str, qas: List[dict]) -> str:
    """Generate complete narrative summary"""
    
    overview = generate_assessment_overview(breakdown_data, qas)
    strengths = generate_strengths_analysis(breakdown_data, qas)
    
    return f"{overview} {insights} {strengths}"

# Update your existing function to use the new comprehensive structure
def generate_detailed_assessment_report(test_name, test_description, theory_description, qas: List[dict]):
    """Generate comprehensive structured report instead of single paragraph"""
    
    answered = [qa for qa in qas if qa.get("answer")]
    if not answered:
        return {"error": "No answered questions"}

    try:
        # Generate comprehensive structured report
        comprehensive_report = generate_comprehensive_assessment_report(
            test_name=test_name,
            test_description=test_description, 
            theory_description=theory_description,
            qas=answered
        )
        
        return comprehensive_report
        
    except Exception as e:
        print(f"Error generating comprehensive report: {e}")
        return {
            "error": "Assessment report temporarily unavailable",
            "test_name": test_name,
            "fallback_summary": f"Assessment completed with {len(answered)} responses."
        }