import streamlit as st
import json
import openai
import os
from typing import Dict, List, Optional
from datetime import datetime
import requests
from dotenv import load_dotenv
from math import ceil

# Load environment variables
load_dotenv()

# Configure OpenAI client for SambaNova
SAMBANOVA_API_KEY = os.getenv("SAMBANOVA_API_KEY", "cf134cde-f4d2-4e6d-90b4-500e269eb286")
client = openai.OpenAI(
    api_key=SAMBANOVA_API_KEY,
    base_url="https://api.sambanova.ai/v1"
)

# Sample USA results for comparison
SAMPLE_USA_RESULTS = {
    "English": 21,
    "Mathematics": 21,
    "Reading": 21,
    "Science": 21
}

def next_question_set():
    """Generate a new set of questions and increment the set number."""
    st.session_state.question_set_number += 1
    st.session_state.questions = generate_questions(
        st.session_state.personal_data,
        st.session_state.regional_data
    )

def display_question_card(question: Dict, index: int) -> None:
    """Display an individual question card with interactive elements."""
    try:
        # Extract necessary details
        category = question.get('category', 'Unknown')
        difficulty = question.get('difficulty', 'Unknown')
        context = question.get('context', '').strip()
        question_text = question.get('question', '')
        options = question.get('options', {})

        # Start the card container but don't close it yet
        st.markdown(f"""
            <div style='
                border: 2px solid rgba(255, 255, 255, 0.8);
                border-radius: 10px;
                padding: 1.5rem;
                margin-bottom: 1rem;
                background-color: rgba(255, 255, 255, 0.1);
                height: 100%;
                display: flex;
                flex-direction: column;
            '>
                <h3>Question {index + 1}</h3>
                <p><strong>Category:</strong> {category} | 
                <strong>Difficulty:</strong> {difficulty}</p>
        """, unsafe_allow_html=True)

        # Display context if available
        if context:
            st.markdown("**Context:**")
            st.markdown(f"*{context}*")

        # Display question
        st.write(f"**{question_text}**")

        # Handle options and user selection
        if isinstance(options, dict) and options:
            formatted_options = [f"{k}: {v}" for k, v in options.items()]
            answer_key = f"answer_{index}"
            choice = st.radio("Select your answer:", formatted_options, key=answer_key)

            # Close the flex-grow div before the button
            st.markdown("</div>", unsafe_allow_html=True)

            # Create a container for the button and feedback
            st.markdown("<div style='margin-top: auto;'>", unsafe_allow_html=True)
            submit_button = RateLimitedButton(
                "Submit Answer", 
                cooldown_seconds=3, 
                key=f"submit_{index}"
            )
            if submit_button.clicked():
                correct_answer = question.get('correct_option')
                selected_letter = choice.split(":")[0] if choice else None
                is_correct = selected_letter == correct_answer
                if is_correct:
                    st.success("✅ Correct!")
                else:
                    st.error(f"❌ Incorrect. The correct answer is {correct_answer}")
                st.info(f"**Explanation:** {question.get('explanation', 'No explanation provided.')}")

                # Save response data to JSON
                save_response_to_json(category, difficulty, is_correct)

            # Close the button container
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.error("Invalid question format")

        # Close the main card div
        st.markdown("</div>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error displaying question: {str(e)}")
        st.write("Raw question data:", question)

def display_questions_grid(questions: List[Dict]) -> None:
    """Display questions in a responsive grid layout."""
    num_questions = len(questions)
    num_rows = ceil(num_questions / 2)

    for row in range(num_rows):
        col1, col2 = st.columns(2)

        first_idx = row * 2
        if first_idx < num_questions:
            with col1:
                display_question_card(questions[first_idx], first_idx)

        second_idx = row * 2 + 1
        if second_idx < num_questions:
            with col2:
                display_question_card(questions[second_idx], second_idx)

    # Add Next button after all questions
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("Next Questions ➡️", key="next_questions"):
            next_question_set()
            st.rerun()
import streamlit as st
from datetime import datetime, timedelta
import time

class RateLimitedButton:
    def __init__(self, label: str, cooldown_seconds: int = 5, key: str = None):
        """
        Initialize a rate-limited button.
        
        Args:
            label: Text to display on the button
            cooldown_seconds: Cooldown period in seconds
            key: Unique identifier for the button state
        """
        self.label = label
        self.cooldown_seconds = cooldown_seconds
        self.key = key or label.lower().replace(" ", "_")
        
        # Initialize session state variables
        if f"{self.key}_last_clicked" not in st.session_state:
            st.session_state[f"{self.key}_last_clicked"] = None
            
    def _get_remaining_cooldown(self) -> float:
        """Calculate remaining cooldown time in seconds."""
        if st.session_state[f"{self.key}_last_clicked"] is None:
            return 0
            
        elapsed = datetime.now() - st.session_state[f"{self.key}_last_clicked"]
        remaining = self.cooldown_seconds - elapsed.total_seconds()
        return max(0, remaining)
        
    def clicked(self) -> bool:
        """
        Render the button and return True if clicked (and not in cooldown).
        
        Returns:
            bool: True if button was clicked and not in cooldown
        """
        remaining_cooldown = self._get_remaining_cooldown()
        
        # Create columns for button and cooldown display
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Disable button during cooldown
            button_clicked = st.button(
                self.label,
                disabled=remaining_cooldown > 0,
                key=f"{self.key}_button"
            )
            
        with col2:
            # Show cooldown timer
            if remaining_cooldown > 0:
                st.markdown(f"⏳ {remaining_cooldown:.1f}s")
                
        # Handle button click
        if button_clicked and remaining_cooldown == 0:
            st.session_state[f"{self.key}_last_clicked"] = datetime.now()
            return True
            
        return False
def generate_questions(personal_data: Dict, regional_data: Dict) -> Optional[List[Dict]]:
    """Generate questions using the LLaMA API directly in Streamlit."""
    try:
        prompt = f"""
        Given the following test results:
        User ACT Results: {personal_data}
        Regional ACT Results: {regional_data}
        USA Median ACT Results: {SAMPLE_USA_RESULTS}

        Generate 4 ACT-style multiple choice practice questions, one for each subject, focusing on areas needing improvement.
        For each question:
        1. Include any necessary context (passages, equations, diagrams described in text, etc.) before the question
        2. Provide the actual question
        3. Include four multiple choice options (A, B, C, D)
        4. Indicate the correct answer
        5. Provide a detailed explanation
        6. Specify the category (Reading/Math/Science/English)
        7. Specify the difficulty level (Easy/Medium/Hard)

        Return the response in a valid JSON array format like this:
        [
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
        ]
        """

        response = client.chat.completions.create(
            model='Meta-Llama-3.1-8B-Instruct',
            messages=[
                {
                    "role": "system",
                    "content": "You are an educational assistant that generates ACT practice questions. Always return responses in valid JSON array format without any additional text or markdown formatting."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )

        # Get and clean the response content
        response_content = response.choices[0].message.content.strip()
        
        # Parse JSON
        try:
            questions = json.loads(response_content)
            if not isinstance(questions, list):
                st.error("API response is not a list of questions")
                return None

            return questions

        except json.JSONDecodeError as e:
            st.error(f"Failed to parse JSON: {str(e)}")
            st.write("Raw response:", response_content)
            return None

    except Exception as e:
        st.error(f"Error generating questions: {str(e)}")
        return None

def save_response_to_json(category: str, difficulty: str, is_correct: bool) -> dict:
    """Save question response data to Pinata."""
    JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySW5mb3JtYXRpb24iOnsiaWQiOiI4YmVmMTM1YS03NDY2LTQ1MjQtODhjMy00MGYzNzg2NmViZDciLCJlbWFpbCI6InNpbW9uZ2FnZTBAZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsInBpbl9wb2xpY3kiOnsicmVnaW9ucyI6W3siZGVzaXJlZFJlcGxpY2F0aW9uQ291bnQiOjEsImlkIjoiRlJBMSJ9LHsiZGVzaXJlZFJlcGxpY2F0aW9uQ291bnQiOjEsImlkIjoiTllDMSJ9XSwidmVyc2lvbiI6MX0sIm1mYV9lbmFibGVkIjpmYWxzZSwic3RhdHVzIjoiQUNUSVZFIn0sImF1dGhlbnRpY2F0aW9uVHlwZSI6InNjb3BlZEtleSIsInNjb3BlZEtleUtleSI6ImZhNjUxNWZkOTRkMDMyZGQwN2QzIiwic2NvcGVkS2V5U2VjcmV0IjoiOWUyZTRiOTE4NDVjMDA4OWE3YzM0NDdhZDVhZDJkZTAyMTdkNGM5MjExOTI2ODEyZDZmMWRkMDlmYmU2ODA4NCIsImV4cCI6MTc2MzM1NzkxNH0.zpWQXD9YWbE6BKiBavUtGyZJJkrEiZ4x0j1zxzgpmJs"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    response_data = {
        "timestamp": timestamp,
        "subject": category,
        "difficulty": difficulty,
        "correct": is_correct,
        "set_number": st.session_state.get('question_set_number', 1)
    }

    url = "https://api.pinata.cloud/pinning/pinJSONToIPFS"
    headers = {
        "Authorization": f"Bearer {JWT_TOKEN}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            json=response_data
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error uploading to Pinata: {e}")
        return {"error": str(e)}

def main():
    st.set_page_config(page_title="ACT Practice Questions", layout="wide")

    # Custom CSS for the page
    st.markdown("""
        <style>
            div.stButton > button {
                width: 100%;
            }
            .stSuccess, .stError, .stInfo {
                margin: 1rem 0;
            }
            .header {
                text-align: center;
                color: #4CAF50;
            }
            .question-card {
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: 10px;
                padding: 20px;
                margin-bottom: 20px;
            }
        </style>
    """, unsafe_allow_html=True)

    # Navigation buttons
    col1, col2 = st.columns([4, 1])  # Adjust column sizes as needed

    with col1:
        st.title("ACT Practice Question Generator")

    # Create two columns for scores input
    col1, col2 = st.columns(2)

    with col1:
        st.header("Regional Scores")
        regional_data = {
            "Mathematics": st.slider("Math (Regional)", 0, 36, 18, key="reg_math"),
            "Reading": st.slider("Reading (Regional)", 0, 36, 18, key="reg_read"),
            "Science": st.slider("Science (Regional)", 0, 36, 18, key="reg_sci"),
            "English": st.slider("English (Regional)", 0, 36, 18, key="reg_eng")
        }
        st.session_state.regional_data = regional_data

    with col2:
        st.header("Your Scores")
        personal_data = {
            "Mathematics": st.slider("Math (Personal)", 0, 36, 13, key="pers_math"),
            "Reading": st.slider("Reading (Personal)", 0, 36, 13, key="pers_read"),
            "Science": st.slider("Science (Personal)", 0, 36, 13, key="pers_sci"),
            "English": st.slider("English (Personal)", 0, 36, 13, key="pers_eng")
        }
        st.session_state.personal_data = personal_data
    generate_button = RateLimitedButton("Generate Questions", cooldown_seconds=10, key="generate")
    if generate_button.clicked():
        with st.spinner("Generating questions..."):
            questions = generate_questions(personal_data, regional_data)
            if questions:
                st.session_state.questions = questions
                st.success("Questions generated successfully!")

    # Display questions if they exist
    if 'questions' in st.session_state and st.session_state.questions:
        st.markdown("## Practice Questions")
        display_questions_grid(st.session_state.questions)

if __name__ == "__main__":
    if 'question_set_number' not in st.session_state:
        st.session_state.question_set_number = 1
    main()
