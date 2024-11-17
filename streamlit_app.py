import streamlit as st
import json
import openai
import os
from typing import Dict, List, Optional
from datetime import datetime
import requests
from dotenv import load_dotenv

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
        """

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
        questions = json.loads(cleaned_content)
        
        return questions

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

    # Prepare to upload to Pinata
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

def display_question_card(question: Dict, index: int) -> None:
    """Display an individual question card with interactive elements."""
    try:
        category = question.get('category', 'Unknown')
        difficulty = question.get('difficulty', 'Unknown')
        context = question.get('context', '').strip()
        question_text = question.get('question', '')
        options = question.get('options', {})

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
            </div>
        """, unsafe_allow_html=True)

        if context:
            st.markdown("**Context:**")
            st.markdown(f"*{context}*")

        st.write(f"**{question_text}**")

        if isinstance(options, dict) and options:
            formatted_options = [f"{k}: {v}" for k, v in options.items()]
            answer_key = f"answer_{index}"
            choice = st.radio("Select your answer:", formatted_options, key=answer_key)

            if st.button("Submit Answer", key=f"submit_{index}"):
                correct_answer = question.get('correct_option')
                selected_letter = choice.split(":")[0] if choice else None
                is_correct = selected_letter == correct_answer

                if is_correct:
                    st.success("✅ Correct!")
                else:
                    st.error(f"❌ Incorrect. The correct answer is {correct_answer}")
                st.info(f"**Explanation:** {question.get('explanation', 'No explanation provided.')}")

                save_response_to_json(category, difficulty, is_correct)

def main():
    st.set_page_config(page_title="ACT Practice Questions", layout="wide")

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

    with col2:
        st.header("Your Scores")
        personal_data = {
            "Mathematics": st.slider("Math (Personal)", 0, 36, 13, key="pers_math"),
            "Reading": st.slider("Reading (Personal)", 0, 36, 13, key="pers_read"),
            "Science": st.slider("Science (Personal)", 0, 36, 13, key="pers_sci"),
            "English": st.slider("English (Personal)", 0, 36, 13, key="pers_eng")
        }

    if st.button("Generate Questions", type="primary"):
        with st.spinner("Generating questions..."):
            questions = generate_questions(personal_data, regional_data)
            if questions:
                st.session_state.questions = questions
                st.success("Questions generated successfully!")

    # Display questions if they exist
    if 'questions' in st.session_state and st.session_state.questions:
        st.markdown("## Practice Questions")
        for i, question in enumerate(st.session_state.questions):
            display_question_card(question, i)

if __name__ == "__main__":
    if 'question_set_number' not in st.session_state:
        st.session_state.question_set_number = 1
    main()
