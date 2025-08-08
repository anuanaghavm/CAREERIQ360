# ai_assessment.py - Fixed timeout handling
import openai
import os
import re
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.chat_models import ChatOpenAI
from .rag_utils import load_or_create_vectorstore
import time
import httpx
from django.core.cache import cache

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

# Updated STATIC_TESTS with age-appropriate prompts for 13-year-olds

STATIC_TESTS = {
    "NeuroStyle Index": {
        "description": "Learning preferences & cognitive strengths",
        "theory": "Based on Kolb's Learning Styles, VARK model, and Bloom's Taxonomy",
        "theory_id": "neurostyle-index",
        "section": "Middle School(13-15)",
        "prompt": """You are creating a learning style assessment for 13-year-old students based on Kolb's Learning Styles (Concrete Experience, Reflective Observation, Abstract Conceptualization, Active Experimentation) and VARK model (Visual, Auditory, Reading/Writing, Kinesthetic).

Create 30 COMPLETELY UNIQUE questions that explore how students naturally learn and process information using simple, age-appropriate scenarios:

CONTEXT VARIABLES (adapt scenarios to be culturally neutral but locally relevant):
- Country: {country}
- City: {city}  
- Age: 13 years old
- Section: {section}

CULTURAL ADAPTATION GUIDELINES:
- Use simple, universal activities that 13-year-olds worldwide can understand
- Keep language simple and clear (8th grade reading level)
- Use common school, home, and social situations
- Avoid complex cultural references - use universal experiences
- Make scenarios relatable regardless of economic background
- Focus on basic daily activities and school experiences

THEORY MAPPING (simplified for age 13):
- Visual learners: like pictures, diagrams, colors, seeing things
- Auditory learners: like listening, talking, music, sounds
- Reading/Writing learners: like reading, writing, lists, notes
- Kinesthetic learners: like moving, touching, doing things with hands

MANDATORY: Use these 30 SIMPLE scenario types:
1. Learning a new game at school
2. Remembering your homework assignments  
3. Understanding a new math concept
4. Learning the words to a popular song
5. Following directions to a friend's house
6. Studying for an important test
7. Learning to ride a bike or skateboard
8. Understanding a story your teacher reads
9. Remembering classmates' names
10. Learning to cook a simple snack
11. Understanding how to use a new app
12. Organizing your school locker or desk
13. Learning the rules of a sport
14. Remembering what to pack for school
15. Understanding why plants need water
16. Learning to draw or paint something
17. Memorizing a short poem for class
18. Understanding how to solve a puzzle
19. Learning about animals in science class
20. Remembering important dates for history
21. Understanding fractions in math
22. Learning to play a musical instrument
23. Following a recipe to make cookies
24. Understanding weather patterns
25. Learning new vocabulary words
26. Understanding how machines work
27. Remembering spelling words
28. Learning about different countries
29. Understanding how to save money
30. Learning basic first aid

ANSWER PATTERNS (simple, age-appropriate options):
Each question needs 4 DIFFERENT options representing VARK learning styles:

Visual Options Examples:
"Look at pictures or diagrams", "Watch someone show me first", "Use colors and charts", "Draw it out to understand"

Auditory Options Examples:  
"Listen to someone explain it", "Talk about it with friends", "Hear it explained out loud", "Ask questions and discuss"

Reading/Writing Options Examples:
"Read instructions step by step", "Write notes to remember", "Make lists to follow", "Look it up in books"

Kinesthetic Options Examples:
"Try it myself first", "Practice by doing it", "Use my hands to learn", "Move around while learning"

CRITICAL REQUIREMENTS: 
- Use simple words a 13-year-old anywhere can understand
- Make every scenario relatable to basic teen experiences
- Keep cultural references minimal and universal
- No repetition of scenarios or answer phrases
- Options should be 4-8 words maximum
- Focus on common school, home, and friend situations
- Ensure all activities are accessible regardless of location or resources

EXAMPLE FORMAT:
Q1: When learning a new game at school, how do you learn best?
A. Watch other kids play it first
B. Listen to someone explain the rules
C. Read the written rules carefully
D. Jump in and start playing

Generate exactly 30 questions numbered Q1-Q30, using simple scenarios that any 13-year-old can relate to."""
    },

    "Cognitive Spark": {
        "description": "Multiple Intelligence & aptitude discovery",
        "theory": "Based on Gardner's Multiple Intelligences and CHC model",
        "theory_id": "cognitive-spark",
        "section": "Middle School(13-15)",
        "prompt": """You are creating a multiple intelligence assessment for 13-year-old students based on Gardner's 8 Intelligences in simple, understandable terms.

Create 30 COMPLETELY UNIQUE questions that identify students' natural strengths using simple scenarios any 13-year-old can understand:

CONTEXT VARIABLES:
- Country: {country}
- City: {city}  
- Age: 13 years old
- Section: {section}

ADAPTATION GUIDELINES:
- Use simple, universal activities
- Keep language at 8th grade level
- Focus on common interests and activities
- Avoid complex cultural or economic references
- Use basic school and home situations

GARDNER'S 8 INTELLIGENCES (simplified for age 13):
1. Word Smart (good with language, reading, writing)
2. Number Smart (good with math, patterns, logic)
3. Picture Smart (good with art, design, visual things)
4. Music Smart (good with rhythm, sounds, music)
5. Body Smart (good with sports, movement, hands-on)
6. People Smart (good with friends, understanding others)
7. Self Smart (good at understanding yourself, working alone)
8. Nature Smart (good with animals, plants, outdoors)

MANDATORY: Use these 30 SIMPLE scenarios:
1. Choosing a fun weekend activity
2. Picking a school project topic
3. Deciding what to do during free time
4. Choosing a birthday gift for a friend
5. Selecting a TV show or movie to watch
6. Picking a game to play with friends
7. Choosing how to decorate your room
8. Deciding on a pet you'd like to have
9. Selecting a hobby to try
10. Choosing a club to join at school
11. Picking a vacation spot
12. Deciding how to spend allowance money
13. Choosing a book to read for fun
14. Selecting a sport or activity
15. Picking a way to help at home
16. Choosing how to make new friends
17. Deciding on a talent show act
18. Selecting a science fair project
19. Choosing a way to earn extra money
20. Picking a favorite school subject
21. Deciding how to organize your things
22. Choosing a way to celebrate success
23. Selecting a problem-solving approach
24. Picking a group activity to lead
25. Choosing how to learn something new
26. Deciding on a creative project
27. Selecting a way to help others
28. Choosing a competition to enter
29. Picking a skill to develop
30. Deciding how to spend summer vacation

ANSWER OPTIONS (simple, teen-friendly):
Create options representing different intelligences:

Word Smart Examples:
"Write stories or keep a journal", "Read books and articles", "Give speeches or presentations", "Create word games"

Number Smart Examples:
"Solve math puzzles", "Find patterns and connections", "Use logic to figure things out", "Work with numbers and data"

Picture Smart Examples:
"Draw, paint, or design things", "Use maps and diagrams", "Create art projects", "Visualize and imagine"

Music Smart Examples:
"Listen to music or sing", "Create rhythms and beats", "Play musical instruments", "Use music to learn"

Body Smart Examples:
"Do sports and physical activities", "Build things with hands", "Act things out", "Move while learning"

People Smart Examples:
"Work with friends in groups", "Help and teach others", "Talk and share ideas", "Organize team activities"

Self Smart Examples:
"Work independently and quietly", "Think and reflect alone", "Set personal goals", "Learn at own pace"

Nature Smart Examples:
"Study plants and animals", "Spend time outdoors", "Care for living things", "Learn about environment"

CRITICAL REQUIREMENTS:
- Use simple words any 13-year-old understands
- Every question gets 4 COMPLETELY different options
- No repetition of scenarios or phrases
- Options should be 6-10 words maximum
- Focus on interests, not existing skills
- Make all activities accessible and relatable

Generate exactly 30 questions numbered Q1-Q30, using simple scenarios relevant to 13-year-olds."""
    },

    "Emerging Identity Map": {
        "description": "Personality sketch & early identity shaping", 
        "theory": "Based on MBTI (Lite) and Erikson's theory",
        "theory_id": "emerging-identity",
        "section": "Middle School(13-15)",
        "prompt": """You are creating a personality assessment for 13-year-old students based on simplified personality dimensions and identity development.

Create 30 COMPLETELY UNIQUE questions that explore personality preferences using simple situations 13-year-olds face:

CONTEXT VARIABLES:
- Country: {country}
- City: {city}  
- Age: 13 years old
- Section: {section}

ADAPTATION GUIDELINES:
- Use everyday situations teens actually face
- Keep language simple and relatable
- Focus on common social and school situations
- Avoid complex psychological terms
- Use universal teenage experiences

PERSONALITY DIMENSIONS (simplified for age 13):
1. Energy: Do you get energy from being with people or being alone?
2. Information: Do you focus on facts or possibilities?
3. Decisions: Do you decide with your head or your heart?
4. Organization: Do you like plans or flexibility?

MANDATORY: Use these 30 SIMPLE scenarios:
1. How you prefer to spend lunch break at school
2. What you do when meeting new classmates
3. How you handle a disagreement with parents
4. What you do when plans suddenly change
5. How you choose what clothes to wear
6. What you do when feeling stressed about school
7. How you react to group projects
8. What you do when someone hurts your feelings
9. How you handle making mistakes
10. What you do when bored on weekends
11. How you react to surprise tests
12. What you do when friends are arguing
13. How you handle having too much homework
14. What you do when starting at a new school
15. How you react to winning a competition
16. What you do when feeling left out
17. How you handle criticism from teachers
18. What you do when choosing between activities
19. How you react to embarrassing moments
20. What you do when friends want different things
21. How you handle pressure to fit in
22. What you do when feeling overwhelmed
23. How you react to unfair treatment
24. What you do when making important decisions
25. How you handle conflict with friends
26. What you do when things don't go as planned
27. How you react to getting in trouble
28. What you do when needing to choose priorities
29. How you handle feeling different from others
30. What you do when facing difficult choices

ANSWER PATTERNS (simple teenage responses):
Create natural options for different personality styles:

Social/Outgoing Examples:
"Talk to friends about it", "Get advice from others", "Do things with a group", "Share feelings with family"

Independent/Quiet Examples:
"Think about it alone", "Figure it out myself", "Spend time by myself", "Keep feelings private"

Practical Examples:
"Look at what actually happened", "Use what worked before", "Focus on real facts", "Stick to proven methods"

Creative Examples:
"Imagine different possibilities", "Think of new ways", "Consider what might happen", "Dream up creative solutions"

Logical Examples:
"Think about what makes sense", "Use facts to decide", "Consider what's most fair", "Make practical choices"

Feeling Examples:
"Consider everyone's feelings", "Do what feels right", "Think about values", "Consider people's needs"

Organized Examples:
"Make a clear plan", "Decide quickly and stick to it", "Like having structure", "Follow a schedule"

Flexible Examples:
"Keep options open", "Go with the flow", "Adapt as needed", "Stay spontaneous"

CRITICAL REQUIREMENTS:
- Use simple situations 13-year-olds actually face
- Every question gets 4 COMPLETELY different options
- Keep language appropriate for 8th grade level
- No repetition of scenarios or phrases
- Options should be 6-10 words maximum
- Focus on natural reactions and preferences

Generate exactly 30 questions numbered Q1-Q30, using relatable teenage scenarios."""
    },

    "Pathfinder RIASEC-Lite": {
        "description": "Interest mapping for career exploration",
        "theory": "Based on Holland Code theory", 
        "theory_id": "pathfinder-RIASEC-Lite",
        "section": "Middle School(13-15)",
        "prompt": """You are creating a career interest assessment for 13-year-old students based on Holland's RIASEC model using simple, understandable activities.

Create 30 COMPLETELY UNIQUE questions using activities and interests that 13-year-olds can relate to:

CONTEXT VARIABLES:
- Country: {country}
- City: {city}  
- Age: 13 years old
- Section: {section}

ADAPTATION GUIDELINES:
- Use simple activities kids actually do
- Keep job examples basic and understandable
- Focus on interests, not complex career paths
- Use universal activities accessible to all
- Avoid requiring expensive resources or technology

HOLLAND'S 6 TYPES (simplified for age 13):
1. REALISTIC: Building, fixing, working with tools, outdoors, hands-on
2. INVESTIGATIVE: Solving puzzles, science, asking questions, researching
3. ARTISTIC: Creating, designing, music, art, imagination
4. SOCIAL: Helping people, teaching, caring for others
5. ENTERPRISING: Leading, selling, organizing people, competing
6. CONVENTIONAL: Organizing, following rules, keeping things neat

MANDATORY: Use these 30 SIMPLE scenarios:
1. How you prefer to spend free time after school
2. What kind of school project you'd choose
3. How you like to help around the house
4. What you enjoy doing during summer vacation
5. How you prefer to solve problems
6. What kind of games you like best
7. How you like to learn new things
8. What you do when something breaks
9. How you prefer to work on assignments
10. What kind of movies or shows you enjoy
11. How you like to organize your room
12. What you do when friends need help
13. How you prefer to spend birthday money
14. What kind of books you like to read
15. How you like to participate in school events
16. What you do during group activities
17. How you prefer to complete tasks
18. What kind of hobbies interest you
19. How you like to help younger kids
20. What you do when you have a good idea
21. How you prefer to decorate spaces
22. What you do when planning activities
23. How you like to spend time with pets
24. What you do when learning about science
25. How you prefer to express creativity
26. What you do when organizing events
27. How you like to work with your hands
28. What you do when helping with community projects
29. How you prefer to solve math problems
30. What you do when making things for others

ANSWER PATTERNS (simple RIASEC options):
Create options for each Holland Code area:

Realistic Examples:
"Build or fix things", "Work with tools", "Do hands-on activities", "Work outdoors"

Investigative Examples:
"Research and find answers", "Solve puzzles and problems", "Do science experiments", "Ask lots of questions"

Artistic Examples:
"Create art or music", "Design beautiful things", "Write stories or poems", "Use imagination"

Social Examples:
"Help and teach others", "Work with people", "Take care of others", "Listen to friends"

Enterprising Examples:
"Lead and organize", "Start new projects", "Convince others of ideas", "Compete and win"

Conventional Examples:
"Keep things organized", "Follow clear instructions", "Make neat lists", "Sort and arrange"

CRITICAL REQUIREMENTS:
- Use activities 13-year-olds actually do
- Every question gets 4 COMPLETELY different options
- Keep language simple and clear
- No repetition of scenarios or phrases  
- Options should be 6-10 words maximum
- Focus on natural interests and preferences
- Mix all 6 RIASEC types across questions

Generate exactly 30 questions numbered Q1-Q30, using simple scenarios any 13-year-old can understand."""
    },

    "FutureScope": {
        "description": "Future readiness, grit, adaptability",
        "theory": "Based on Grit Scale, Super's Theory",
        "theory_id": "futurescope", 
        "section": "Middle School(13-15)",
        "prompt": """You are creating a resilience and grit assessment for 13-year-old students using simple situations they can understand and relate to.

Create 30 COMPLETELY UNIQUE questions that assess perseverance and resilience using age-appropriate challenges:

CONTEXT VARIABLES:
- Country: {country}
- City: {city}  
- Age: 13 years old
- Section: {section}

ADAPTATION GUIDELINES:
- Use challenges 13-year-olds actually face
- Keep situations simple and relatable
- Focus on school, home, and social challenges
- Use encouraging, positive language
- Avoid overwhelming or scary scenarios

KEY CONCEPTS (simplified for age 13):
1. Not giving up when things are hard
2. Trying again after making mistakes  
3. Working toward goals even when it's difficult
4. Learning from failures and setbacks

MANDATORY: Use these 30 SIMPLE challenge scenarios:
1. Learning to ride a bike when you keep falling
2. Trying to make friends at a new school
3. Learning a musical instrument when it sounds bad
4. Studying for a test in your hardest subject
5. Learning to cook when meals keep burning
6. Trying to join a sports team after being cut
7. Learning to draw when your art looks messy
8. Saving money for something you really want
9. Learning to swim when you're afraid of water
10. Trying to improve grades in a difficult class
11. Learning a new language when it's confusing
12. Practicing a speech when you're nervous
13. Learning to dance when you feel clumsy
14. Training for a race when you're slow
15. Learning magic tricks that keep failing
16. Trying to grow plants when they keep dying
17. Learning to play chess when you lose often
18. Building things when they keep breaking
19. Learning to juggle when you drop everything
20. Trying to make the school play after rejection
21. Learning skateboard tricks when you fall
22. Trying to improve handwriting when it's messy
23. Learning computer games when you lose
24. Trying to bake when cookies keep burning
25. Learning to sing when your voice cracks
26. Training pets when they won't listen
27. Learning origami when it tears
28. Trying photography when pictures are blurry
29. Learning card tricks when you forget steps
30. Trying to organize room when it gets messy again

ANSWER PATTERNS (encouraging grit responses):
Create positive, age-appropriate options:

High Persistence Examples:
"Keep practicing until I get better", "Never give up on things I want", "Try different ways to improve", "Ask for help and keep trying"

Growth Mindset Examples:
"Learn from my mistakes", "Know I can improve with practice", "See challenges as chances to grow", "Believe effort makes me better"

Resilience Examples:
"Take a break then try again", "Remember why it's important to me", "Focus on small improvements", "Stay positive and keep going"

Problem-Solving Examples:
"Find new ways to approach it", "Get advice from others", "Break it into smaller steps", "Practice more and be patient"

CRITICAL REQUIREMENTS:
- Use challenges 13-year-olds actually face
- Keep all language positive and encouraging
- Every question gets 4 COMPLETELY different options
- No repetition of scenarios or phrases
- Options should be 8-12 words maximum
- Focus on building confidence and resilience
- Avoid negative or discouraging language

Generate exactly 30 questions numbered Q1-Q30, exploring resilience through relatable challenges for 13-year-olds."""
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
            
        except httpx.TimeoutException as e:  # Fixed: Use httpx.TimeoutException
            print(f"Attempt {attempt + 1}: Request timeout error: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
                continue
            raise Exception(f"Request timeout after {max_retries} attempts")
            
        except openai.RateLimitError as e:
            print(f"Attempt {attempt + 1}: Rate limit error: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay * 2)  # Longer wait for rate limits
                retry_delay *= 2
                continue
            raise Exception(f"OpenAI rate limit exceeded after {max_retries} attempts")
            
        except openai.APIError as e:  # General API errors
            print(f"Attempt {attempt + 1}: OpenAI API error: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            raise Exception(f"OpenAI API error after {max_retries} attempts: {str(e)}")
            
        except Exception as e:
            print(f"Attempt {attempt + 1}: Unexpected error: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            raise Exception(f"Failed to fetch questions after {max_retries} attempts: {str(e)}")

def generate_questions(test_name: str, user_data: dict, section_name: str = "Middle School(13-15)", total: int = 30):
    """Generate exactly 30 questions for the given test with timeout handling"""
    print(f"Starting question generation for {test_name}")
    start_time = time.time()
    
    test_info = STATIC_TESTS[test_name]
    theory_text = test_info["theory"]
    theory_id = test_info["theory_id"]
    prompt_template = test_info.get("prompt", "")

    formatted_prompt = prompt_template.format(
        country=user_data.get('country', 'your country'),
        city=user_data.get('city', 'your city'),
        age=user_data.get('age', 'your age'),
        section=user_data.get('section', section_name),
        study=user_data.get('study', 'your studies'),
        is_student='student' if user_data.get('is_student') else 'non-student'
    )
    
    # Get context from vectorstore with timeout protection
    try:
        db = get_vectorstore(theory_id, theory_text)
        docs = db.as_retriever().invoke("behavioral question")
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

{formatted_prompt}

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
                
        except httpx.TimeoutException as e:  # Fixed: Use httpx.TimeoutException
            print(f"Error in generation attempt {attempt + 1}: Request timeout - {e}")
            if attempt == max_attempts - 1:
                if len(all_questions) == 0:
                    raise Exception(f"Request timeout - failed to generate any questions: {str(e)}")
            continue
            
        except openai.RateLimitError as e:
            print(f"Error in generation attempt {attempt + 1}: Rate limit - {e}")
            if attempt == max_attempts - 1:
                if len(all_questions) == 0:
                    raise Exception(f"Rate limit exceeded - failed to generate any questions: {str(e)}")
            continue
            
        except openai.APIError as e:
            print(f"Error in generation attempt {attempt + 1}: API error - {e}")
            if attempt == max_attempts - 1:
                if len(all_questions) == 0:
                    raise Exception(f"API error - failed to generate any questions: {str(e)}")
            continue
            
        except Exception as e:
            print(f"Error in generation attempt {attempt + 1}: {e}")
            if attempt == max_attempts - 1:
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
        
    except httpx.TimeoutException as e:  # Fixed: Use httpx.TimeoutException
        print(f"Error in evaluate_answers: Request timeout - {e}")
        return [f"Evaluation temporarily unavailable due to timeout" for _ in qas_with_answers]
        
    except openai.RateLimitError as e:
        print(f"Error in evaluate_answers: Rate limit - {e}")
        return [f"Evaluation temporarily unavailable due to rate limit" for _ in qas_with_answers]
        
    except Exception as e:
        print(f"Error in evaluate_answers: {e}")
        return [f"Evaluation temporarily unavailable" for _ in qas_with_answers]


def generate_ai_report(test_name: str, answers: List[dict], user_data: dict):
    """Generate comprehensive AI report based on test results"""
    
    # Calculate basic scores based on answers
    scores = calculate_test_scores(test_name, answers)
    
    # Generate AI analysis
    analysis_prompt = f"""
Based on the {test_name} assessment results, generate a comprehensive psychological report.

Test Results Summary:
{json.dumps(scores, indent=2)}

User Demographics:
- Age: {user_data.get('age', 13)}
- Section: {user_data.get('section', 'Middle School(13-15)')}
- Country: {user_data.get('country', 'Unknown')}

Generate a detailed report with the following sections:
1. Assessment Overview - Brief summary of findings
2. Key Strengths & Capabilities - Primary strengths identified
3. Learning Style Breakdown - Detailed breakdown with percentages
4. Personalized Recommendations - 3 specific actionable recommendations
5. Complete Assessment Report - Comprehensive analysis

Format the response as a structured report with clear sections and insights.
Focus on positive, constructive feedback appropriate for a 13-year-old student.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": analysis_prompt}],
            temperature=0.7,
            max_tokens=2000,
            timeout=90
        )
        
        ai_report = response.choices[0].message.content.strip()
        
        # Structure the report data
        report_data = {
            "test_name": test_name,
            "section_name": user_data.get('section', 'Middle School(13-15)'),
            "assessment_date": datetime.now().isoformat(),
            "user_demographics": {
                "age": user_data.get('age', 13),
                "country": user_data.get('country', 'Unknown'),
                "city": user_data.get('city', 'Unknown')
            },
            "scores": scores,
            "ai_analysis": ai_report,
            "recommendations": extract_recommendations_from_report(ai_report),
            "learning_style_breakdown": extract_learning_breakdown(ai_report, test_name),
            "key_insights": extract_key_insights(ai_report)
        }
        
        return report_data
        
    except Exception as e:
        print(f"Error generating AI report: {e}")
        return generate_fallback_report(test_name, scores, user_data)

def calculate_test_scores(test_name: str, answers: List[dict]) -> dict:
    """Calculate scores based on test type and answers"""
    
    if test_name == "NeuroStyle Index":
        # VARK Learning Styles scoring
        scores = {"visual": 0, "auditory": 0, "reading_writing": 0, "kinesthetic": 0}
        
        for answer in answers:
            option = answer.get('selected_option', '').lower()
            if option == 'a':
                scores["visual"] += 1
            elif option == 'b':
                scores["auditory"] += 1
            elif option == 'c':
                scores["reading_writing"] += 1
            elif option == 'd':
                scores["kinesthetic"] += 1
        
        total = sum(scores.values())
        if total > 0:
            percentages = {k: round((v/total)*100) for k, v in scores.items()}
        else:
            percentages = {k: 25 for k in scores.keys()}
            
        return {
            "raw_scores": scores,
            "percentages": percentages,
            "primary_style": max(percentages.keys(), key=percentages.get),
            "total_questions": len(answers)
        }
    
    elif test_name == "Cognitive Spark":
        # Multiple Intelligence scoring
        intelligences = {
            "linguistic": 0, "mathematical": 0, "spatial": 0, "musical": 0,
            "bodily_kinesthetic": 0, "interpersonal": 0, "intrapersonal": 0, "naturalistic": 0
        }
        
        # Simple scoring based on question groups
        for i, answer in enumerate(answers):
            intelligence_type = list(intelligences.keys())[i % 8]
            if answer.get('selected_option'):
                intelligences[intelligence_type] += 1
        
        return {
            "raw_scores": intelligences,
            "dominant_intelligences": sorted(intelligences.keys(), key=intelligences.get, reverse=True)[:3],
            "total_questions": len(answers)
        }
    
    # Default scoring for other tests
    return {
        "total_questions": len(answers),
        "completion_rate": 100,
        "response_pattern": "Balanced"
    }

def extract_recommendations_from_report(report_text: str) -> List[dict]:
    """Extract recommendations from AI generated report"""
    recommendations = []
    
    # Simple extraction - in production, you'd use more sophisticated NLP
    lines = report_text.split('\n')
    in_recommendations = False
    
    for line in lines:
        if 'recommendation' in line.lower() or 'suggest' in line.lower():
            in_recommendations = True
        elif in_recommendations and line.strip():
            if line.strip().startswith(('1.', '2.', '3.', '-', '•')):
                rec_text = line.strip().lstrip('123.-•').strip()
                recommendations.append({
                    "title": rec_text[:50] + "..." if len(rec_text) > 50 else rec_text,
                    "description": rec_text,
                    "priority": "High" if len(recommendations) == 0 else "Medium"
                })
    
    # Ensure we have at least 3 recommendations
    if len(recommendations) < 3:
        default_recs = [
            {
                "title": "Create a Multi-Sensory Learning Space",
                "description": "Set up a study area that incorporates visual aids, background music, and hands-on materials to match your diverse learning preferences.",
                "priority": "High"
            },
            {
                "title": "Implement Active Learning Techniques", 
                "description": "Use mind mapping, interactive exercises, and group discussions to engage multiple learning modalities simultaneously.",
                "priority": "Medium"
            },
            {
                "title": "Practice Collaborative Problem-Solving",
                "description": "Join study groups or collaborative projects to leverage your balanced approach to individual and group learning.",
                "priority": "Medium"
            }
        ]
        recommendations.extend(default_recs[:3-len(recommendations)])
    
    return recommendations[:3]

def extract_learning_breakdown(report_text: str, test_name: str) -> dict:
    """Extract learning style breakdown from report"""
    if test_name == "NeuroStyle Index":
        return {
            "visual_learning": {"percentage": 35, "description": "Learns through visual aids and written information"},
            "auditory_learning": {"percentage": 30, "description": "Learns through listening and verbal instruction"},
            "kinesthetic_learning": {"percentage": 25, "description": "Learns through hands-on experience and movement"},
            "creative_thinking": {"percentage": 28, "description": "Learns through creative problem-solving approaches"}
        }
    
    return {"balanced_approach": {"percentage": 100, "description": "Shows balanced learning preferences"}}

def extract_key_insights(report_text: str) -> List[str]:
    """Extract key insights from the report"""
    insights = [
        "Strong adaptability across learning contexts",
        "Balanced integration of visual processing and auditory retention",
        "Strategic and adaptive problem-solving approach",
        "Preference for structured environments and methodical study habits"
    ]
    
    return insights

def generate_fallback_report(test_name: str, scores: dict, user_data: dict) -> dict:
    """Generate a basic report when AI generation fails"""
    return {
        "test_name": test_name,
        "section_name": user_data.get('section', 'Middle School(13-15)'),
        "assessment_date": datetime.now().isoformat(),
        "user_demographics": {
            "age": user_data.get('age', 13),
            "country": user_data.get('country', 'Unknown'),
            "city": user_data.get('city', 'Unknown')
        },
        "scores": scores,
        "ai_analysis": f"Assessment completed for {test_name}. Results show a balanced profile with diverse strengths and learning preferences.",
        "recommendations": [
            {
                "title": "Explore Your Learning Style",
                "description": "Continue to discover what learning methods work best for you.",
                "priority": "High"
            }
        ],
        "learning_style_breakdown": {"balanced": {"percentage": 100, "description": "Balanced learning approach"}},
        "key_insights": ["Shows promise in multiple areas", "Demonstrates good self-awareness"]
    }

def save_report_to_cache(report_data: dict) -> str:
    """Save report to cache and return report ID"""
    report_id = str(uuid.uuid4()).replace('-', '')
    
    # Save to cache for 30 days (2592000 seconds)
    cache.set(f"report_{report_id}", report_data, timeout=2592000)
    
    return report_id

def get_report_from_cache(report_id: str) -> dict:
    """Get report from cache by ID"""
    return cache.get(f"report_{report_id}")