from flask import Flask, request, jsonify, render_template_string
import os
import openai
import json
import logging
import requests
from typing import Dict, List
from dotenv import load_dotenv
import time
import functools
import logging
from typing import Callable, Any
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FunctionTimer:
    _timing_stats = defaultdict(lambda: {"calls": 0, "total_time": 0, "avg_time": 0, "min_time": float('inf'), "max_time": 0})
    
    @classmethod
    def timer(cls, func: Callable) -> Callable:
        """
        Decorator to measure and log function execution time
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                end_time = time.time()
                execution_time = end_time - start_time
                
                # Update statistics
                stats = cls._timing_stats[func.__name__]
                stats["calls"] += 1
                stats["total_time"] += execution_time
                stats["avg_time"] = stats["total_time"] / stats["calls"]
                stats["min_time"] = min(stats["min_time"], execution_time)
                stats["max_time"] = max(stats["max_time"], execution_time)
                
                logger.info(
                    f"Function '{func.__name__}' executed in {execution_time:.4f} seconds. "
                    f"Avg: {stats['avg_time']:.4f}s, "
                    f"Min: {stats['min_time']:.4f}s, "
                    f"Max: {stats['max_time']:.4f}s, "
                    f"Calls: {stats['calls']}"
                )
        
        return wrapper
    
    @classmethod
    def get_stats(cls) -> dict:
        """
        Return all collected timing statistics
        """
        return dict(cls._timing_stats)
    
    @classmethod
    def print_stats(cls) -> None:
        """
        Print a summary of all function timing statistics
        """
        logger.info("\n=== Function Timing Statistics ===")
        for func_name, stats in cls._timing_stats.items():
            logger.info(
                f"\nFunction: {func_name}\n"
                f"Total calls: {stats['calls']}\n"
                f"Total time: {stats['total_time']:.4f}s\n"
                f"Average time: {stats['avg_time']:.4f}s\n"
                f"Min time: {stats['min_time']:.4f}s\n"
                f"Max time: {stats['max_time']:.4f}s"
            )
#from files import upload_question()

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)



# Configure OpenAI client for SambaNova

SAMBANOVA_API_KEY = os.getenv("SAMBANOVA_API_KEY", "cf134cde-f4d2-4e6d-90b4-500e269eb286")
client = openai.OpenAI(
    api_key=SAMBANOVA_API_KEY,
    base_url="https://api.sambanova.ai/v1"
)

# # Sample test data
# SAMPLE_USER_RESULTS = {
#     "English": 20,
#     "Mathematics": 11,
#     "Reading": 11,
#     "Science": 19
# }

# SAMPLE_REGIONAL_RESULTS = {
#     "English": 15,
#     "Mathematics": 15,
#     "Reading": 15,
#     "Science": 15
# }

SAMPLE_USA_RESULTS = {
    "English": 21,
    "Mathematics": 21,
    "Reading": 21,
    "Science": 21
}
# Add this HTML_TEMPLATE constant right after the sample data constants and before the functions

from datetime import datetime, timedelta
from typing import List, Dict, Optional
import requests

@FunctionTimer.timer
def get_pinata_questions(jwt_token: str) -> List[Dict]:
    """
    Retrieve the last 3 pinned questions from Pinata.

    Args:
        jwt_token (str): Pinata JWT token

    Returns:
        List[Dict]: List of question data from the last 3 pinned files
    """
    # API endpoint for getting pinned files
    url = "https://api.pinata.cloud/data/pinList?status=pinned"

    headers = {
        "Authorization": f"Bearer {jwt_token}"
    }

    try:
        # Get list of pinned files
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        pinned_files = response.json()

        # Sort pinned files by pin timestamp (assuming 'date_pinned' exists)
        sorted_files = sorted(
            pinned_files.get('rows', []),
            key=lambda x: x.get('date_pinned', ''),
            reverse=True
        )

        # Get the last 3 pinned files
        last_three_files = sorted_files[:3]

        all_questions = []

        # Iterate through the last 3 pinned files
        for row in last_three_files:
            cid = row.get('ipfs_pin_hash')

            # Get content of each file
            content = get_file_content(cid)
            if content:
                # If content is a list, extend all_questions
                if isinstance(content, list):
                    all_questions.extend(content)
                # If content is a single question dict, append it
                elif isinstance(content, dict):
                    all_questions.append(content)

        return all_questions

    except Exception as e:
        print(f"Error getting pinned questions: {e}")
        return []

@FunctionTimer.timer
def get_file_content(cid: str) -> Optional[Dict]:
    """
    Get content of a specific file by CID.

    Args:
        cid (str): The IPFS CID of the file

    Returns:
        Optional[Dict]: The file content as JSON if successful, None if failed
    """
    url = f"https://gateway.pinata.cloud/ipfs/{cid}"

    try:
        response = requests.get(url)
        response.raise_for_status()

        # Try to parse as JSON
        try:
            print("clutch")
            print(response.json())
            return response.json()
        except ValueError:
            print(f"File {cid} is not valid JSON")
            return None

    except Exception as e:
        print(f"Error getting file content for {cid}: {e}")
        return None
@FunctionTimer.timer
def generate_questions(user_results: Dict, regional_results: Dict) -> List[Dict]:
    jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySW5mb3JtYXRpb24iOnsiaWQiOiI4YmVmMTM1YS03NDY2LTQ1MjQtODhjMy00MGYzNzg2NmViZDciLCJlbWFpbCI6InNpbW9uZ2FnZTBAZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsInBpbl9wb2xpY3kiOnsicmVnaW9ucyI6W3siZGVzaXJlZFJlcGxpY2F0aW9uQ291bnQiOjEsImlkIjoiRlJBMSJ9LHsiZGVzaXJlZFJlcGxpY2F0aW9uQ291bnQiOjEsImlkIjoiTllDMSJ9XSwidmVyc2lvbiI6MX0sIm1mYV9lbmFibGVkIjpmYWxzZSwic3RhdHVzIjoiQUNUSVZFIn0sImF1dGhlbnRpY2F0aW9uVHlwZSI6InNjb3BlZEtleSIsInNjb3BlZEtleUtleSI6ImZhNjUxNWZkOTRkMDMyZGQwN2QzIiwic2NvcGVkS2V5U2VjcmV0IjoiOWUyZTRiOTE4NDVjMDA4OWE3YzM0NDdhZDVhZDJkZTAyMTdkNGM5MjExOTI2ODEyZDZmMWRkMDlmYmU2ODA4NCIsImV4cCI6MTc2MzM1NzkxNH0.zpWQXD9YWbE6BKiBavUtGyZJJkrEiZ4x0j1zxzgpmJs"


    questions_answered = get_pinata_questions(jwt_token)
    """
    Generate and parse ACT practice questions based on test results using LLaMA API
    """
    prompt = f"""
    Given the following test results:
    User ACT Results: {user_results}
    Regional ACT Results: {regional_results}
    USA Median ACT Results: {SAMPLE_USA_RESULTS}

    Questions Previously Asnwered: {questions_answered}

    Generate 4 ACT-style multiple choice practice questions, one for each subject, focusing on areas needing improvement.
    For each question:
    1. Include any necessary context (passages, equations, diagrams described in text, etc.) before the question
    2. Provide the actual question
    3. Include four multiple choice options (A, B, C, D)
    4. Indicate the correct answer
    5. Provide a detailed explanation
    6. Specify the category (Reading/Math/Science/English)
    7. Specify the difficulty level (Easy/Medium/Hard)

    Format each question as JSON with the following structure:
    {{
        "context": "Any necessary passage, equation, or background information...",
        "question": "question text",
        "options": {{
            "A": "first option",
            "B": "second option",
            "C": "third option",
            "D": "fourth option"
        }},
        "correct_option": "A",
        "explanation": "explanation text",
        "category": "subject category",
        "difficulty": "difficulty level"
    }}

    For Reading and English questions, ALWAYS include a relevant passage in the context.
    For Math questions, include any necessary equations or diagrams described in text.
    For Science questions, include any relevant data, graphs described in text, or experimental setup.

    Return all questions in a JSON array. Make sure distractors (incorrect options) are plausible 
    but clearly incorrect to a knowledgeable test-taker. Include common misconceptions as distractors.
    The correct answer should be randomly distributed among A, B, C, and D across questions.
    """

    try:
        logger.debug(f"Sending request to API with user_results: {user_results}")
        response = client.chat.completions.create(
            model='Meta-Llama-3.1-8B-Instruct',
            messages=[
                {
                    "role": "system",
                    "content": "You are an educational assistant that generates targeted practice questions based on weaknesses and test performance analysis. Return responses in JSON format. Always include necessary context for questions."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )

        # Extract and clean response content
        response_content = response.choices[0].message.content
        cleaned_content = response_content
        if "```json" in cleaned_content:
            cleaned_content = cleaned_content.split("```json")[1]
        if "```" in cleaned_content:
            cleaned_content = cleaned_content.split("```")[0]

        cleaned_content = cleaned_content.strip()

        # Parse and validate questions
        try:
            questions = json.loads(cleaned_content)
            validated_questions = []
            required_fields = {"context", "question", "options", "correct_option", "explanation", "category",
                               "difficulty"}

            for q in questions:
                if all(field in q for field in required_fields):
                    if isinstance(q["options"], dict) and all(opt in q["options"] for opt in ["A", "B", "C", "D"]):
                        # Ensure context is not empty for Reading/English questions
                        if q["category"] in ["Reading", "English"] and not q["context"].strip():
                            logger.warning(f"Skipping question with empty context: {q}")
                            continue
                        validated_questions.append(q)
                    else:
                        logger.warning(f"Invalid options format in question: {q}")
                else:
                    logger.warning(f"Skipping invalid question format: {q}")

            if not validated_questions:
                logger.info("No valid questions found, attempting unstructured parsing")
                return parse_unstructured_response(cleaned_content)

            return validated_questions

        except json.JSONDecodeError as e:
            logger.warning(f"JSON parsing failed: {e}")
            return parse_unstructured_response(cleaned_content)

    except Exception as e:
        logger.error(f"Error generating questions: {e}")
        return [{"error": str(e),
                 "context": "Error occurred",
                 "question": "Error generating question",
                 "options": {"A": "N/A", "B": "N/A", "C": "N/A", "D": "N/A"},
                 "correct_option": "A",
                 "explanation": str(e),
                 "category": "Error",
                 "difficulty": "N/A"}]

@FunctionTimer.timer
def parse_unstructured_response(response_text: str) -> List[Dict]:
    """
    Enhanced fallback parser for unstructured text responses
    """
    logger.debug(f"Parsing unstructured response: {response_text}")
    questions = []
    current_question = {}
    current_options = {}

    lines = response_text.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue

        logger.debug(f"Processing line: {line}")

        if any(line.lower().startswith(start) for start in ['q:', 'question:', 'problem:']):
            if current_question and current_question.get('question'):
                current_question['options'] = current_options
                questions.append(current_question)
            current_question = {
                "question": line.split(':', 1)[1].strip(),
                "options": {},
                "correct_option": "A",
                "explanation": "",
                "category": "Unknown",
                "difficulty": "Medium"
            }
            current_options = {}
        elif line.startswith('A)') or line.startswith('A.'):
            current_options["A"] = line.split(')', 1)[1].strip() if ')' in line else line.split('.', 1)[1].strip()
        elif line.startswith('B)') or line.startswith('B.'):
            current_options["B"] = line.split(')', 1)[1].strip() if ')' in line else line.split('.', 1)[1].strip()
        elif line.startswith('C)') or line.startswith('C.'):
            current_options["C"] = line.split(')', 1)[1].strip() if ')' in line else line.split('.', 1)[1].strip()
        elif line.startswith('D)') or line.startswith('D.'):
            current_options["D"] = line.split(')', 1)[1].strip() if ')' in line else line.split('.', 1)[1].strip()
        elif line.lower().startswith('correct:') or line.lower().startswith('answer:'):
            answer_text = line.split(':', 1)[1].strip()
            if answer_text.upper() in ['A', 'B', 'C', 'D']:
                current_question["correct_option"] = answer_text.upper()
        elif line.lower().startswith('explanation:'):
            current_question["explanation"] = line.split(':', 1)[1].strip()
        elif line.lower().startswith('category:'):
            current_question["category"] = line.split(':', 1)[1].strip()
        elif line.lower().startswith('difficulty:'):
            current_question["difficulty"] = line.split(':', 1)[1].strip()

    # Add the last question if exists
    if current_question and current_question.get('question'):
        current_question['options'] = current_options
        questions.append(current_question)

    logger.debug(f"Parsed questions: {questions}")
    return questions if questions else [{"question": "Failed to generate questions",
                                         "options": {"A": "N/A", "B": "N/A", "C": "N/A", "D": "N/A"},
                                         "correct_option": "A",
                                         "explanation": "The API response format was unexpected",
                                         "category": "Error", "difficulty": "N/A"}]


# @app.route('/')
# def test_interface():
#     """Test interface endpoint"""
#     return render_template_string(HTML_TEMPLATE)


# @app.route('/test-sample', methods=['POST'])
# def test_with_sample():
#     """Test endpoint using sample data"""
#     try:
#         logger.info("Generating questions with sample data")
#         questions = generate_questions(SAMPLE_USER_RESULTS, SAMPLE_REGIONAL_RESULTS)
#         logger.debug(f"Generated questions: {questions}")
#         # Properly format the result as JSON string
#         result = json.dumps(questions, indent=2)
#         return render_template_string(HTML_TEMPLATE, result=result)
#     except Exception as e:
#         logger.error(f"Error in test_with_sample: {e}")
#         error_response = [{"error": str(e), "question": "Error occurred", "answer": "N/A",
#                            "explanation": str(e), "category": "Error", "difficulty": "N/A"}]
#         return render_template_string(HTML_TEMPLATE, result=json.dumps(error_response, indent=2))


# @app.route('/test-custom', methods=['POST'])
# def test_with_custom():
#     """Test endpoint using custom data"""
#     try:
#         # Safely parse JSON instead of using eval
#         user_results = json.loads(request.form['user_results'])
#         regional_results = json.loads(request.form['regional_results'])
#         questions = generate_questions(user_results, regional_results)
#         return render_template_string(HTML_TEMPLATE, result=json.dumps(questions, indent=2))
#     except Exception as e:
#         logger.error(f"Error in test_with_custom: {e}")
#         error_response = [{"error": str(e), "question": "Error occurred", "answer": "N/A",
#                            "explanation": str(e), "category": "Error", "difficulty": "N/A"}]
#         return render_template_string(HTML_TEMPLATE, result=json.dumps(error_response, indent=2))


@app.route('/generate-questions', methods=['POST'])
@FunctionTimer.timer
def create_questions():
    """API endpoint to generate questions"""
    try:
        data = request.get_json()

        if not data or 'user_results' not in data or 'regional_results' not in data:
            return jsonify({
                'error': 'Missing required fields. Please provide user_results and regional_results.'
            }), 400

        questions = generate_questions(
            data['user_results'],
            data['regional_results']
        )

        return jsonify({
            'status': 'success',
            'questions': questions
        })
    except Exception as e:
        logger.error(f"Error in create_questions: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/health', methods=['GET'])
@FunctionTimer.timer
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})


if __name__ == '__main__':
    app.run(debug=True)
    FunctionTimer.print_stats()
