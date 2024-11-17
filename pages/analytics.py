import streamlit as st
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import requests

def load_initial_scores():
    """Load initial personal scores from the session state."""
    return {
        'Mathematics': 13,
        'Reading': 13,
        'Science': 13,
        'English': 13
    }

def get_pinata_questions(jwt_token: str) -> List[Dict]:
    """Retrieve questions from Pinata."""
    url = "https://api.pinata.cloud/data/pinList?status=pinned"
    headers = {"Authorization": f"Bearer {jwt_token}"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        pinned_files = response.json()

        sorted_files = sorted(
            pinned_files.get('rows', []),
            key=lambda x: x.get('date_pinned', ''),
            reverse=True
        )

        all_questions = []
        for row in sorted_files:  # Remove the 25 file limit to get all data
            cid = row.get('ipfs_pin_hash')
            content = get_file_content(cid)
            if content:
                if isinstance(content, list):
                    all_questions.extend(content)
                elif isinstance(content, dict):
                    all_questions.append(content)

        return process_questions(all_questions)

    except Exception as e:
        print(f"Error getting pinned questions: {e}")
        return []

def get_file_content(cid: str) -> Optional[Dict]:
    """Get content of a file by CID."""
    url = f"https://gateway.pinata.cloud/ipfs/{cid}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error getting file content for {cid}: {e}")
        return None
def calculate_score_change(question: Dict, current_score: float) -> float:
    """
    Calculate score change based on question difficulty and correctness.
    Returns positive value for correct answers, negative for wrong answers.
    """
    difficulty_map = {
        'easy': 0.1,
        'medium': 0.2,
        'hard': 0.3
    }
    difficulty_multiplier = difficulty_map.get(question.get('difficulty', '').lower(), 0.2)
    
    # Base change calculation
    growth_factor = 1 + ((abs(18-current_score)/175)) if current_score > 0 else 1
    base_change = growth_factor * difficulty_multiplier * current_score
    
    # Explicitly handle correct vs incorrect
    if question.get('correct', False):
        return base_change  # Positive change for correct answer
    else:
        return -base_change  # Negative change for wrong answer
def process_questions(questions: List[Dict]) -> List[Dict]:
    """Process questions and track score progression."""
    # Standardize subject names
    subject_map = {
        'Math': 'Mathematics',
        'English': 'English',
        'Science': 'Science',
        'Reading': 'Reading'
    }
    
    # Initialize scores for each subject
    current_scores = load_initial_scores()
    subject_progressions = {subject: [score] for subject, score in current_scores.items()}
    
    processed_questions = []
    
    # Sort questions by timestamp
    sorted_questions = sorted(
        questions,
        key=lambda x: x.get('timestamp', datetime.now().isoformat())
    )
    
    # Process each question and track score changes
    for q in sorted_questions:
        try:
            # Skip if missing critical data
            if not q.get('subject') or not isinstance(q.get('correct'), bool):
                continue
                
            # Map subject name
            subject = subject_map.get(q.get('subject'), q.get('subject'))
            if subject not in current_scores:
                continue
                
            # Calculate new score
            current_score = current_scores[subject]
            score_change = calculate_score_change(q, current_score)
            new_score = max(0, round(current_score + score_change, 2))
            
            # Update tracking
            current_scores[subject] = new_score
            subject_progressions[subject].append(new_score)
            
            # Store processed question with progression data
            processed_q = {
                'timestamp': q.get('timestamp', datetime.now().isoformat()),
                'subject': subject,
                'difficulty': q.get('difficulty', 'medium'),
                'correct': q.get('correct', False),
                'previous_score': current_score,
                'new_score': new_score,
                'score_change': score_change,
                'subject_progression': list(subject_progressions[subject])  # Include full progression
            }
            
            processed_questions.append(processed_q)
            
        except Exception as e:
            print(f"Error processing question: {e}")
            continue
            
    return processed_questions

def create_progression_graph(questions: List[Dict]):
    """Create progression graph showing all score changes."""
    if not questions:
        st.warning("No questions data available to display.")
        return
        
    # Prepare data for visualization
    data_points = []
    for subject in ['Mathematics', 'Reading', 'Science', 'English']:
        progression = []
        current_score = load_initial_scores()[subject]
        progression.append({'Question': 0, 'Score': current_score, 'Subject': subject})
        
        subject_questions = [q for q in questions if q['subject'] == subject]
        for i, q in enumerate(subject_questions, 1):
            progression.append({
                'Question': i,
                'Score': q['new_score'],
                'Subject': subject
            })
            
        data_points.extend(progression)
    
    # Create DataFrame and plot
    df = pd.DataFrame(data_points)
    if not df.empty:
        chart_data = df.pivot(index='Question', columns='Subject', values='Score')
        st.line_chart(chart_data)

def main():
    st.title("Subject Progression Analysis")
    
    sample_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySW5mb3JtYXRpb24iOnsiaWQiOiI4YmVmMTM1YS03NDY2LTQ1MjQtODhjMy00MGYzNzg2NmViZDciLCJlbWFpbCI6InNpbW9uZ2FnZTBAZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsInBpbl9wb2xpY3kiOnsicmVnaW9ucyI6W3siZGVzaXJlZFJlcGxpY2F0aW9uQ291bnQiOjEsImlkIjoiRlJBMSJ9LHsiZGVzaXJlZFJlcGxpY2F0aW9uQ291bnQiOjEsImlkIjoiTllDMSJ9XSwidmVyc2lvbiI6MX0sIm1mYV9lbmFibGVkIjpmYWxzZSwic3RhdHVzIjoiQUNUSVZFIn0sImF1dGhlbnRpY2F0aW9uVHlwZSI6InNjb3BlZEtleSIsInNjb3BlZEtleUtleSI6ImZhNjUxNWZkOTRkMDMyZGQwN2QzIiwic2NvcGVkS2V5U2VjcmV0IjoiOWUyZTRiOTE4NDVjMDA4OWE3YzM0NDdhZDVhZDJkZTAyMTdkNGM5MjExOTI2ODEyZDZmMWRkMDlmYmU2ODA4NCIsImV4cCI6MTc2MzM1NzkxNH0.zpWQXD9YWbE6BKiBavUtGyZJJkrEiZ4x0j1zxzgpmJs"
    
    # Get and process questions
    questions = get_pinata_questions(sample_token)
    
    # Display graph
    st.subheader("Subject Score Progression")
    create_progression_graph(questions)
    
    # Display statistics
    st.subheader("Current Statistics")
    cols = st.columns(4)
    
    # Group questions by subject
    subject_stats = {}
    for subject in ['Mathematics', 'Reading', 'Science', 'English']:
        subject_qs = [q for q in questions if q['subject'] == subject]
        if subject_qs:
            initial_score = load_initial_scores()[subject]
            final_score = subject_qs[-1]['new_score'] if subject_qs else initial_score
            subject_stats[subject] = {
                'current_score': final_score,
                'change': final_score - initial_score,
                'questions_count': len(subject_qs)
            }
        else:
            subject_stats[subject] = {
                'current_score': load_initial_scores()[subject],
                'change': 0,
                'questions_count': 0
            }
    
    # Display metrics
    for idx, subject in enumerate(['Mathematics', 'Reading', 'Science', 'English']):
        stats = subject_stats[subject]
        with cols[idx]:
            st.metric(
                label=subject,
                value=f"{stats['current_score']:.1f}",
                delta=f"{stats['change']:.1f}"
            )
            st.caption(f"Questions Answered: {stats['questions_count']}")

if __name__ == "__main__":
    st.set_page_config(
        page_title="Subject Progression",
        page_icon="📈",
        layout="wide"
    )
    main()