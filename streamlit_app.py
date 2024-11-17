import streamlit as st
import requests
import json
from typing import Dict, List, Optional
from math import ceil
from datetime import datetime
import os

from app import generate_questions

# Initialize session state
if 'questions' not in st.session_state:
    st.session_state.questions = []
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'main'
if 'question_set_number' not in st.session_state:
    st.session_state.question_set_number = 1

# Enhanced CSS styling
st.set_page_config(page_title="ACT Practice Questions", layout="wide")
st.markdown("""
    <style>
        /* Main layout and typography */
        .main {
            padding: 2rem;
        }
        h1, h2, h3 {
            color: #5180c9;
            font-weight: 600;
        }

        /* Custom container styling */
        .css-1d391kg {
            padding: 2rem 1rem;
        }

        /* Score input containers */
        .scores-container {
            background-color: rgba(31, 111, 235, 0.05);
            border-radius: 10px;
            padding: 1.5rem;
            margin-bottom: 2rem;
        }

        /* Button styling */
        div.stButton > button {
            width: 100%;
            height: 3rem;
            background: linear-gradient(90deg, #5180c9 0%, #2ea5ff 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        div.stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(31, 111, 235, 0.2);
        }

        /* Question card styling */
        .question-card {
            background: linear-gradient(145deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.1) 100%);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 2rem;
            margin-bottom: 1.5rem;
            backdrop-filter: blur(10px);
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        }

        /* Radio button styling */
        .stRadio > label {
            font-weight: 500;
            color: #e6edf3;
        }

        /* Alert/message styling */
        .stAlert {
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
        }
        .stSuccess {
            background-color: rgba(46, 160, 67, 0.1);
            border: 1px solid rgba(46, 160, 67, 0.2);
        }
        .stError {
            background-color: rgba(248, 81, 73, 0.1);
            border: 1px solid rgba(248, 81, 73, 0.2);
        }
        .stInfo {
            background-color: rgba(31, 111, 235, 0.1);
            border: 1px solid rgba(31, 111, 235, 0.2);
        }

        /* Slider styling */
        .stSlider > div > div > div {
           
        }
        .stSlider > div > div > div > div {
            background-color: #ffffff;
        }

        /* Analytics button styling */
        .analytics-button {
            background-color: #238636;
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 6px;
            text-decoration: none;
            display: inline-block;
            transition: all 0.2s ease;
        }
        .analytics-button:hover {
            background-color: #2ea043;
        }
    </style>
""", unsafe_allow_html=True)


def display_question_card(question: Dict, index: int) -> None:
    """Display an enhanced question card with wider centered feedback."""
    try:
        st.markdown(f"""
            <div class="question-card">
                <h3 style="margin-bottom: 1rem;">Question {index + 1}</h3>
                <div style="display: flex; gap: 1rem; margin-bottom: 1rem;">
                    <span class="badge" style="background-color: rgba(31, 111, 235, 0.1); color: #1f6feb; padding: 0.3rem 0.8rem; border-radius: 1rem;">
                        {question.get('category', 'Unknown')}
                    </span>
                    <span class="badge" style="background-color: rgba(46, 160, 67, 0.1); color: #2ea043; padding: 0.3rem 0.8rem; border-radius: 1rem;">
                        {question.get('difficulty', 'Unknown')}
                    </span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Question content container - made wider
        st.markdown("""
            <div style="max-width: 800px; margin: 0 auto;">
        """, unsafe_allow_html=True)

        context = question.get('context', '').strip()
        if context:
            st.markdown(f"""
                <div style="background-color: rgba(255, 255, 255, 0.05); padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
                    <strong>Context:</strong><br>
                    <em>{context}</em>
                </div>
            """, unsafe_allow_html=True)

        st.markdown(f"**{question.get('question', '')}**")

        options = question.get('options', {})
        if isinstance(options, dict) and options:
            formatted_options = [f"{k}: {v}" for k, v in options.items()]
            answer_key = f"answer_{index}"

            # Container for radio buttons
            with st.container():
                choice = st.radio("Select your answer:", formatted_options, key=answer_key)

            # Close the question content container
            st.markdown("</div>", unsafe_allow_html=True)

            # Wider columns for submit button
            col1, col2, col3 = st.columns([1, 4, 1])
            with col2:
                if st.button("Submit Answer", key=f"submit_{index}"):
                    correct_answer = question.get('correct_option')
                    selected_letter = choice.split(":")[0] if choice else None
                    is_correct = selected_letter == correct_answer


                    # Result and correct answer - wider
                    if is_correct:
                        st.success("✅ Correct!")
                    else:
                        st.error(f"❌ Incorrect")
                        st.markdown(f"""
                            <div style="
                                width: 120%;
                                margin: 1rem auto;
                                padding: 0.75rem;
                                background-color: rgba(31, 111, 235, 0.05);
                                border-radius: 8px;
                                border: 1px solid rgba(31, 111, 235, 0.1);">
                                <strong>Correct Answer:</strong> {correct_answer}
                            </div>
                        """, unsafe_allow_html=True)

                    # Explanation section - wider
                    st.markdown("""
                        <div style="
                            width: 120%;
                            margin: 1rem auto;
                            padding: 1.5rem;
                            background-color: rgba(31, 111, 235, 0.05);
                            border-radius: 8px;
                            border: 1px solid rgba(31, 111, 235, 0.1);
                            text-align: left;">
                            <strong>Explanation:</strong><br><br>
                            {}
                        </div>
                    """.format(question.get('explanation', 'No explanation provided.')), unsafe_allow_html=True)

                    # Close the feedback container
                    st.markdown("</div>", unsafe_allow_html=True)

                    save_response_to_json(question.get('category', 'Unknown'),
                                       question.get('difficulty', 'Unknown'),
                                       is_correct)

    except Exception as e:
        st.error(f"Error displaying question: {str(e)}")
        st.write("Raw question data:", question)

def display_questions_grid(questions: List[Dict]) -> None:
    """Display questions in a responsive grid layout with enhanced spacing."""
    num_questions = len(questions)
    num_rows = ceil(num_questions / 2)

    # Add some spacing before questions
    st.markdown("<br>", unsafe_allow_html=True)

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
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("Next Questions ➡️", key="next_questions"):
            next_question_set()
            st.rerun()


def save_response_to_json(category: str, difficulty: str, is_correct: bool) -> dict:
    """
    Save question response data to a JSON file and upload to Pinata.
    Returns the Pinata upload response.
    """
    # Your JWT token
    JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySW5mb3JtYXRpb24iOnsiaWQiOiI4YmVmMTM1YS03NDY2LTQ1MjQtODhjMy00MGYzNzg2NmViZDciLCJlbWFpbCI6InNpbW9uZ2FnZTBAZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsInBpbl9wb2xpY3kiOnsicmVnaW9ucyI6W3siZGVzaXJlZFJlcGxpY2F0aW9uQ291bnQiOjEsImlkIjoiRlJBMSJ9LHsiZGVzaXJlZFJlcGxpY2F0aW9uQ291bnQiOjEsImlkIjoiTllDMSJ9XSwidmVyc2lvbiI6MX0sIm1mYV9lbmFibGVkIjpmYWxzZSwic3RhdHVzIjoiQUNUSVZFIn0sImF1dGhlbnRpY2F0aW9uVHlwZSI6InNjb3BlZEtleSIsInNjb3BlZEtleUtleSI6ImZhNjUxNWZkOTRkMDMyZGQwN2QzIiwic2NvcGVkS2V5U2VjcmV0IjoiOWUyZTRiOTE4NDVjMDA4OWE3YzM0NDdhZDVhZDJkZTAyMTdkNGM5MjExOTI2ODEyZDZmMWRkMDlmYmU2ODA4NCIsImV4cCI6MTc2MzM1NzkxNH0.zpWQXD9YWbE6BKiBavUtGyZJJkrEiZ4x0j1zxzgpmJs"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    response_data = {
        "timestamp": timestamp,
        "subject": category,
        "difficulty": difficulty,
        "correct": is_correct,
        "set_number": st.session_state.question_set_number
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

    # Write updated data to file
    with open(filename, 'w') as f:
        json.dump(responses, f, indent=4)

    # Prepare to upload to Pinata
    url = "https://api.pinata.cloud/pinning/pinFileToIPFS"

    headers = {
        "Authorization": f"Bearer {JWT_TOKEN}"
    }

    # Create the file payload
    files = {
        'file': ('question_responses.json', open(filename, 'rb'), 'application/json')
    }

    # Add metadata
    payload = {
        'pinataMetadata': {
            'name': 'question_responses.json',
            'keyvalues': {
                'timestamp': timestamp
            }
        }
    }

    try:
        response = requests.post(
            url,
            files=files,
            headers=headers,
            data={'pinataMetadata': json.dumps(payload['pinataMetadata'])}
        )
        response.raise_for_status()

        print(f"File uploaded successfully to Pinata. CID: {response.json().get('IpfsHash')}")
        with open(filename, 'w') as f:
            json.dump([], f)
        return response.json()

    except Exception as e:
        print(f"Error uploading to Pinata: {e}")
        return {"error": str(e)}
    finally:
        files['file'][1].close()


def next_question_set():
    """Generate a new set of questions and increment the set number."""
    st.session_state.question_set_number += 1
    st.session_state.questions = generate_questions(
        st.session_state.personal_data,
        st.session_state.regional_data
    )


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
    """Enhanced main application logic with improved layout."""
    # Header section with navigation
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title("📚 ACT Practice Question Generator")
    with col2:
        st.markdown("""
            <div style="text-align: right; padding-top: 1rem;">
                <a href="pages/Analytics.py" class="analytics-button">
                    📈 Analytics
                </a>
            </div>
        """, unsafe_allow_html=True)

    if st.session_state.current_page == 'main':
        # Score input section
        st.markdown("""
            <div class="scores-container">
                <h2 style="margin-bottom: 1.5rem;">Score Information</h2>
            </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 📊 Regional Scores")
            regional_data = {
                "Mathematics": st.slider("Math", 0, 36, 18, key="reg_math"),
                "Reading": st.slider("Reading", 0, 36, 18, key="reg_read"),
                "Science": st.slider("Science", 0, 36, 18, key="reg_sci"),
                "English": st.slider("English", 0, 36, 18, key="reg_eng")
            }
            st.session_state.regional_data = regional_data

        with col2:
            st.markdown("### 🎯 Your Scores")
            personal_data = {
                "Mathematics": st.slider("Math", 0, 36, 13, key="per_math"),
                "Reading": st.slider("Reading", 0, 36, 13, key="per_read"),
                "Science": st.slider("Science", 0, 36, 13, key="per_sci"),
                "English": st.slider("English", 0, 36, 13, key="per_eng")
            }
            st.session_state.personal_data = personal_data

        # Generate questions button
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🎲 Generate Questions", type="primary"):
            with st.spinner("Creating your personalized questions..."):
                questions = generate_questions(personal_data, regional_data)
                if questions:
                    st.session_state.questions = questions
                    st.success("✨ Questions generated successfully!")

        # Display questions
        if st.session_state.questions:
            st.markdown("## 📝 Practice Questions")
            display_questions_grid(st.session_state.questions)

    # Backend status in sidebar with improved styling
    with st.sidebar:
        st.markdown("### System Status")
        try:
            health_response = requests.get("http://localhost:5000/health")
            if health_response.status_code == 200:
                st.markdown("""
                    <div style="background-color: rgba(46, 160, 67, 0.1); padding: 0.8rem; border-radius: 8px; display: flex; align-items: center;">
                        <span style="color: #2ea043; margin-right: 0.5rem;">●</span>
                        Backend: Connected
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                    <div style="background-color: rgba(248, 81, 73, 0.1); padding: 0.8rem; border-radius: 8px; display: flex; align-items: center;">
                        <span style="color: #f85149; margin-right: 0.5rem;">●</span>
                        Backend: Error
                    </div>
                """, unsafe_allow_html=True)
        except Exception as e:
            st.markdown("""
                <div style="background-color: rgba(248, 81, 73, 0.1); padding: 0.8rem; border-radius: 8px; display: flex; align-items: center;">
                    <span style="color: #f85149; margin-right: 0.5rem;">●</span>
                    Backend: Not Connected
                </div>
            """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()