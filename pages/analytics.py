import streamlit as st
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import requests


def load_initial_scores():
    """Load initial personal scores from the session state."""
    try:
        if 'personal_scores' in st.session_state:
            return st.session_state.personal_scores
        return {
            'Mathematics': 13,
            'Reading': 13,
            'Science': 13,
            'English': 13
        }
    except Exception:
        return {
            'Mathematics': 13,
            'Reading': 13,
            'Science': 13,
            'English': 13
        }


def initialize_subject_scores(questions_data: List[Dict]) -> List[Dict]:
    """
    Initialize subject scores for each question using load_initial_scores.

    Args:
        questions_data (List[Dict]): List of questions from Pinata

    Returns:
        List[Dict]: Questions with initialized subject scores
    """
    initial_scores = load_initial_scores()

    for question in questions_data:
        subject = question.get('subject', '')
        # Map subject to initial scores key if needed
        subject_map = {
            'Math': 'Mathematics',
            'Science': 'Science',
            'Reading': 'Reading',
            'English': 'English'
        }
        mapped_subject = subject_map.get(subject, subject)

        # Initialize subject_scores with initial score if it exists
        if mapped_subject in initial_scores:
            question['subject_scores'] = [initial_scores[mapped_subject]]
        else:
            # Default to 13 if subject not found
            question['subject_scores'] = [13]

    return questions_data


def get_pinata_questions(jwt_token: str) -> List[Dict]:
    """
    Retrieve and process questions from Pinata.

    Args:
        jwt_token (str): Pinata JWT token

    Returns:
        List[Dict]: Processed and deduplicated questions with progression data
    """
    url = "https://api.pinata.cloud/data/pinList?status=pinned"
    headers = {
        "Authorization": f"Bearer {jwt_token}"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        pinned_files = response.json()

        sorted_files = sorted(
            pinned_files.get('rows', []),
            key=lambda x: x.get('date_pinned', ''),
            reverse=True
        )

        last_files = sorted_files[:25]  # Get last 25 files for more data points
        all_questions = []

        for row in last_files:
            cid = row.get('ipfs_pin_hash')
            content = get_file_content(cid)
            if content:
                if isinstance(content, list):
                    all_questions.extend(content)
                elif isinstance(content, dict):
                    all_questions.append(content)

        # Process and deduplicate questions
        processed_questions = process_and_deduplicate_questions(all_questions)
        return processed_questions

    except Exception as e:
        print(f"Error getting pinned questions: {e}")
        return []


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


from typing import List, Dict
import math


def calculate_subject_growth(questions_data: List[Dict]) -> List[Dict]:
    """
    Calculate subject growth scores based on correctness.

    Args:
        questions (List[Dict]): Processed questions with progression data

    Returns:
        Dict[str, List[float]]: Subject progression data
    """
    progression = {}

    for q in questions:
        subject = q['subject']
        if subject not in progression:
            progression[subject] = []

        # Add all scores to progression
        progression[subject].extend(q['subject_scores'])

    return progression


def process_and_deduplicate_questions(questions_data: List[Dict]) -> List[Dict]:
    """
    Process questions data to handle timestamps and remove duplicates.
    Sorts by timestamp and combines progression data.

    Args:
        questions_data (List[Dict]): Raw questions data from Pinata

    Returns:
        List[Dict]: Processed and deduplicated questions with progression data
    """
    # Convert to proper format and sort by timestamp
    processed_questions = []
    for q in questions_data:
        try:
            processed_q = {
                'timestamp': q.get('timestamp', datetime.now().isoformat()),
                'subject': q.get('subject', ''),
                'difficulty': q.get('difficulty', 'medium'),
                'is_correct': q.get('correct', False),
                'set_number': q.get('set_number', 1)
            }
            processed_questions.append(processed_q)
        except Exception as e:
            print(f"Error processing question: {e}")
            continue

    # Sort by timestamp
    processed_questions.sort(key=lambda x: x['timestamp'])

    # Group by subject to maintain progression
    subject_progressions = {}
    for q in processed_questions:
        subject = q['subject']
        if subject not in subject_progressions:
            subject_progressions[subject] = {
                'questions': [],
                'scores': []
            }
        subject_progressions[subject]['questions'].append(q)

    # Initialize and calculate progression for each subject
    final_questions = []
    for subject, data in subject_progressions.items():
        questions = data['questions']
        initial_score = load_initial_scores().get(subject, 13)
        current_score = initial_score

        for q in questions:
            q['subject_scores'] = [current_score]  # Start with current score
            new_score = calculate_single_question_growth(q, current_score)
            q['subject_scores'].append(new_score)  # Add new score
            current_score = new_score  # Update current score for next question
            final_questions.append(q)

    return final_questions


def calculate_single_question_growth(question: Dict, current_score: float) -> float:
    """
    Calculate growth for a single question based on current score.

    Args:
        question (Dict): Question data
        current_score (float): Current score before this question

    Returns:
        float: New score after this question
    """
    difficulty_map = {
        'easy': 0.1,
        'medium': 0.2,
        'hard': 0.3
    }
    difficulty_multiplier = difficulty_map.get(question['difficulty'].lower(), 0.2)

    growth_factor = 1 + (-(35 / current_score)) if current_score != 0 else 0
    score_change = growth_factor * difficulty_multiplier * current_score

    if question['is_correct']:
        new_score = round(current_score + score_change, 2)
    else:
        new_score = round(current_score - score_change, 2)

    return max(0, new_score)

def analyze_progression(questions: List[Dict]) -> Dict[str, List[float]]:
    """
    Analyze progression for each subject using sequential test numbers.

    Args:
        questions (List[Dict]): Processed questions with progression data

    Returns:
        Dict[str, List[float]]: Subject progression data with scores
    """
    progression = {}

    # Sort questions by timestamp first
    sorted_questions = sorted(questions, key=lambda x: datetime.fromisoformat(x['timestamp'].replace('Z', '+00:00')))

    for q in sorted_questions:
        subject = q['subject']
        if subject not in progression:
            progression[subject] = []

        # Add only the final score from each question
        if 'subject_scores' in q and q['subject_scores']:
            progression[subject].append(q['subject_scores'][-1])

    return progression


def create_progression_graph(progression_data: Dict[str, List[float]]):
    """
    Create a Streamlit line graph showing progression by test number.

    Args:
        progression_data (Dict[str, List[float]]): Progression data with scores
    """
    if not progression_data:
        st.warning("No progression data available to display.")
        return

    # Convert progression data to DataFrame with test numbers
    all_data = []
    for subject, scores in progression_data.items():
        for test_num, score in enumerate(scores, 1):  # Start numbering from 1
            all_data.append({
                'Subject': subject,
                'Test Number': test_num,
                'Score': score
            })

    df = pd.DataFrame(all_data)

    if df.empty:
        st.warning("No data points to display.")
        return

    # Create the line chart with test numbers on x-axis
    chart_data = df.pivot(index='Test Number', columns='Subject', values='Score')
    st.line_chart(chart_data)


def main():
    st.title("Subject Progression Analysis")

    sample_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySW5mb3JtYXRpb24iOnsiaWQiOiI4YmVmMTM1YS03NDY2LTQ1MjQtODhjMy00MGYzNzg2NmViZDciLCJlbWFpbCI6InNpbW9uZ2FnZTBAZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsInBpbl9wb2xpY3kiOnsicmVnaW9ucyI6W3siZGVzaXJlZFJlcGxpY2F0aW9uQ291bnQiOjEsImlkIjoiRlJBMSJ9LHsiZGVzaXJlZFJlcGxpY2F0aW9uQ291bnQiOjEsImlkIjoiTllDMSJ9XSwidmVyc2lvbiI6MX0sIm1mYV9lbmFibGVkIjpmYWxzZSwic3RhdHVzIjoiQUNUSVZFIn0sImF1dGhlbnRpY2F0aW9uVHlwZSI6InNjb3BlZEtleSIsInNjb3BlZEtleUtleSI6ImZhNjUxNWZkOTRkMDMyZGQwN2QzIiwic2NvcGVkS2V5U2VjcmV0IjoiOWUyZTRiOTE4NDVjMDA4OWE3YzM0NDdhZDVhZDJkZTAyMTdkNGM5MjExOTI2ODEyZDZmMWRkMDlmYmU2ODA4NCIsImV4cCI6MTc2MzM1NzkxNH0.zpWQXD9YWbE6BKiBavUtGyZJJkrEiZ4x0j1zxzgpmJs"
    questions = get_pinata_questions(sample_token)

    # Get progression data
    progression = analyze_progression(questions)

    # Display the graph
    st.subheader("Subject Score Progression by Test Number")
    create_progression_graph(progression)

    # Display statistics below the graph
    st.subheader("Progression Statistics")

    # Create fixed number of columns (4 for the 4 subjects)
    cols = st.columns(4)

    # Map subjects to column indices
    subject_order = ['Mathematics', 'Science', 'Reading', 'English']

    # Display metrics in the columns
    for idx, subject in enumerate(subject_order):
        with cols[idx]:
            if subject in progression and progression[subject]:
                scores = progression[subject]
                if scores:
                    st.metric(
                        label=subject,
                        value=f"{scores[-1]:.1f}",
                        delta=f"{scores[-1] - scores[0]:.1f}"
                    )
                    st.caption(f"Total Tests: {len(scores)}")
            else:
                st.metric(
                    label=subject,
                    value="0",
                    delta="0"
                )
                st.caption("No data available")


if __name__ == "__main__":
    st.set_page_config(
        page_title="Subject Progression",
        page_icon="📈",
        layout="wide"
    )
    main()