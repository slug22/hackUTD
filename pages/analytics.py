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
            'Mathematics': 13,  # Default values if not set
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

def calculate_subject_progress(responses):
    """
    Calculate cumulative progress for each subject based on difficulty.
    Returns a DataFrame suitable for st.line_chart
    Points system:
    - Hard: +1.0
    - Medium: +0.5
    - Easy: +0.25
    """
    initial_scores = load_initial_scores()

    # Initialize dictionary to store progress for each subject
    subject_progress = {
        'Math': [initial_scores['Mathematics']],
        'Reading': [initial_scores['Reading']],
        'Science': [initial_scores['Science']],
        'English': [initial_scores['English']]
    }

    # Define points for each difficulty level
    difficulty_points = {
        'Hard': 1.0,
        'Medium': 0.5,
        'Easy': 0.25
    }

    # Sort responses by timestamp
    sorted_responses = sorted(responses, key=lambda x: datetime.strptime(x['timestamp'], "%Y-%m-%d %H:%M:%S"))

    # Calculate cumulative progress
    for response in sorted_responses:
        subject = response['subject']
        if subject in subject_progress:
            # Only add points if the answer was correct
            if response['correct']:
                points = difficulty_points.get(response['difficulty'], 0)
                new_value = subject_progress[subject][-1] + points
                subject_progress[subject].append(new_value)
            else:
                # If incorrect, maintain the same value
                subject_progress[subject].append(subject_progress[subject][-1])

    # Convert to DataFrame for st.line_chart
    # Find the maximum length among all subjects
    max_len = max(len(values) for values in subject_progress.values())

    # Pad shorter lists with their last value
    for subject in subject_progress:
        current_len = len(subject_progress[subject])
        if current_len < max_len:
            last_value = subject_progress[subject][-1]
            subject_progress[subject].extend([last_value] * (max_len - current_len))

    # Create DataFrame
    df = pd.DataFrame(subject_progress)

    return df


def get_subject_statistics(responses):
    """Calculate statistics for each subject."""
    stats = {}
    for subject in ['Math', 'Reading', 'Science', 'English']:
        subject_responses = [r for r in responses if r['subject'] == subject]
        total = len(subject_responses)
        if total > 0:
            correct = sum(1 for r in subject_responses if r['correct'])
            accuracy = (correct / total * 100)
            stats[subject] = {
                'total': total,
                'correct': correct,
                'accuracy': accuracy
            }
        else:
            stats[subject] = {'total': 0, 'correct': 0, 'accuracy': 0}
    return stats


def main():
    st.markdown("# Learning Analytics")

    # Add navigation button back to main page
    if st.sidebar.button("← Back to Question Generator"):
        st.switch_page("main.py")

    # Load and process data
    responses = load_question_responses()

    if not responses:
        st.warning("No question response data available yet. Complete some questions to see your progress!")
        return

    # Calculate progress and statistics
    progress_df = calculate_subject_progress(responses)
    subject_stats = get_subject_statistics(responses)

    # Display the progress chart
    st.markdown("### Learning Progress Over Time")
    st.line_chart(progress_df)

    st.markdown("""
    **Points System:**
    - Hard Questions: 1.0 points
    - Medium Questions: 0.5 points
    - Easy Questions: 0.25 points
    """)

    # Display overall statistics
    st.markdown("### Overall Performance")
    total_questions = len(responses)
    correct_answers = sum(1 for r in responses if r['correct'])

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Questions", total_questions)
    with col2:
        st.metric("Correct Answers", correct_answers)
    with col3:
        accuracy = (correct_answers / total_questions * 100) if total_questions > 0 else 0
        st.metric("Overall Accuracy", f"{accuracy:.1f}%")
    with col4:
        # Find subject with highest accuracy
        best_subject = max(subject_stats.items(),
                           key=lambda x: x[1]['accuracy'] if x[1]['total'] > 0 else -1)
        st.metric("Strongest Subject",
                  f"{best_subject[0]} ({best_subject[1]['accuracy']:.1f}%)"
                  if best_subject[1]['total'] > 0 else "N/A")

    # Display subject-wise statistics
    st.markdown("### Subject-wise Performance")
    subject_cols = st.columns(4)

    for subject, col in zip(subject_stats.keys(), subject_cols):
        with col:
            st.markdown(f"**{subject}**")
            stats = subject_stats[subject]
            st.write(f"Questions: {stats['total']}")
            st.write(f"Correct: {stats['correct']}")
            st.write(f"Accuracy: {stats['accuracy']:.1f}%")

    # Display recent activity
    st.markdown("### Recent Activity")
    if responses:
        recent_df = pd.DataFrame(responses[-5:])  # Last 5 responses
        recent_df['timestamp'] = pd.to_datetime(recent_df['timestamp'])
        recent_df = recent_df[['timestamp', 'subject', 'difficulty', 'correct']]
        recent_df = recent_df.sort_values('timestamp', ascending=False)
        st.dataframe(recent_df, use_container_width=True)


if __name__ == "__main__":
    st.set_page_config(
        page_title="Subject Progression",
        page_icon="📈",
        layout="wide"
    )
    main()
