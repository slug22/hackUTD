import streamlit as st
import requests
import json
from typing import Dict, List, Optional
from math import ceil
from datetime import datetime
import os


from app import generate_questions

# Initialize session state for questions and current page
if 'questions' not in st.session_state:
    st.session_state.questions = []

if 'current_page' not in st.session_state:
    st.session_state.current_page = 'main'


def save_response_to_json(category: str, difficulty: str, is_correct: bool) -> None:
    """Save question response data to a JSON file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    response_data = {
        "timestamp": timestamp,
        "subject": category,
        "difficulty": difficulty,
        "correct": is_correct
    }

    # Create 'data' directory if it doesn't exist
    if not os.path.exists('data'):
        os.makedirs('data')

    filename = 'data/question_responses.json'

    # Read existing data
    try:
        with open(filename, 'r') as f:
            responses = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        responses = []

    # Append new response
    responses.append(response_data)

    # Write updated data back to file
    with open(filename, 'w') as f:
        json.dump(responses, f, indent=4)


def display_question_card(question: Dict, index: int) -> None:
    """Display an individual question card with interactive elements."""
    try:
        # Extract necessary details
        category = question.get('category', 'Unknown')
        difficulty = question.get('difficulty', 'Unknown')
        context = question.get('context', '').strip()
        question_text = question.get('question', '')
        options = question.get('options', {})

        # Create a card layout for the question
        st.markdown(f"""
            <div style='
                border: 2px solid rgba(255, 255, 255, 0.8);
                border-radius: 10px;
                padding: 1.5rem;
                margin-bottom: 1rem;
                background-color: rgba(255, 255, 255, 0.1);
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

            # Submit button
            if st.button("Submit Answer", key=f"submit_{index}"):
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
        else:
            st.error("Invalid question format")

        # Close the div after all content is added
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


def generate_questions(personal_data: Dict, regional_data: Dict) -> Optional[List[Dict]]:
    """Make API call to generate questions."""
    try:
        response = requests.post(
            "http://localhost:5000/generate-questions",
            json={
                "user_results": personal_data,
                "regional_results": regional_data
            },
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            return response.json().get('questions', [])
        else:
            st.error(f"API Error: {response.json().get('message', 'Unknown error')}")
            return None

    except requests.exceptions.ConnectionError:
        st.error("Could not connect to the backend server. Please make sure it's running.")
        return None
    except Exception as e:
        st.error(f"Error generating questions: {str(e)}")
        return None



def main():
    """Main application logic."""
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

    with col2:
        # Add navigation button to Analytics page
        if st.button("📈 Analytics"):
            st.switch_page("pages/Analytics.py")  # Updated path

    # Rest of your main page code remains the same...
    if st.session_state.current_page == 'main':
        # Create two columns for scores input
        col1, col2 = st.columns(2)

        with col1:
            st.header("Regional Scores")
            regional_data = {
                "Mathematics": st.slider("Math", 0, 36, 18),
                "Reading": st.slider("Reading", 0, 36, 18),
                "Science": st.slider("Science", 0, 36, 18),
                "English": st.slider("English", 0, 36, 18)
            }

        with col2:
            st.header("Your Scores")
            personal_data = {
                "Mathematics": st.slider("Math", 0, 36, 13),
                "Reading": st.slider("Reading", 0, 36, 13),
                "Science": st.slider("Science", 0, 36, 13),
                "English": st.slider("English", 0, 36, 13)
            }

        # Generate questions button
        if st.button("Generate Questions", type="primary"):
            with st.spinner("Generating questions..."):
                questions = generate_questions(personal_data, regional_data)
                if questions:
                    st.session_state.questions = questions
                    st.success("Questions generated successfully!")

        # Display questions if they exist
        if st.session_state.questions:
            st.markdown("## Practice Questions")
            display_questions_grid(st.session_state.questions)

            if st.button("Reset All Answers"):
                with st.spinner("Generating questions..."):
                    questions = generate_questions(personal_data, regional_data)
                    if questions:
                        st.session_state.questions = questions
                        st.success("Questions generated successfully!")

    # Backend status in sidebar
    try:
        health_response = requests.get("http://localhost:5000/health")
        if health_response.status_code == 200:
            st.sidebar.success("Backend: Connected")
        else:
            st.sidebar.error("Backend: Error")
    except Exception as e:
        print(e)
        st.sidebar.error("Backend: Not Connected")


if __name__ == "__main__":
    main()