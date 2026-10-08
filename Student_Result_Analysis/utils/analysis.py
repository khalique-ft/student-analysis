# utils/analysis.py
# Analysis functions using Pandas, NumPy and Matplotlib

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Required for non-GUI environments
import matplotlib.pyplot as plt
import os
from utils.db import get_connection


def calculate_grade(average):
    """Return grade based on average marks"""
    if average is None or np.isnan(average):
        return 'N/A'
    if average >= 90:
        return 'A+'
    elif average >= 80:
        return 'A'
    elif average >= 70:
        return 'B'
    elif average >= 60:
        return 'C'
    elif average >= 40:
        return 'D'
    else:
        return 'F'


def get_results_dataframe():
    """
    Fetch student marks and return a pandas DataFrame
    with total, average and grade calculated.
    """
    connection = get_connection()
    if not connection:
        return pd.DataFrame()

    query = """
        SELECT 
            s.student_id,
            s.name,
            s.roll_no,
            s.class,
            m.subject,
            m.marks
        FROM students s
        LEFT JOIN marks m ON s.student_id = m.student_id
    """
    df = pd.read_sql(query, connection)
    connection.close()
    return df


def get_student_summary():
    """
    Returns a list of dictionaries containing:
    name, roll_no, class, subjects, total, average, grade
    """
    df = get_results_dataframe()
    if df.empty:
        return []

    # Group by student
    summary = df.groupby(['student_id', 'name', 'roll_no', 'class']).agg({
        'marks': ['sum', 'mean'],
        'subject': lambda x: ', '.join(
            [f"{subj}:{mark}" for subj, mark in zip(x, df.loc[x.index, 'marks']) if pd.notna(subj)]
        )
    }).reset_index()

    # Flatten multi-index columns
    summary.columns = ['student_id', 'name', 'roll_no', 'class', 'total', 'average', 'subjects']

    results = []
    for _, row in summary.iterrows():
        avg = row['average'] if pd.notna(row['average']) else 0
        results.append({
            'name': row['name'],
            'roll_no': row['roll_no'],
            'class': row['class'] if pd.notna(row['class']) else '-',
            'subjects': row['subjects'] if row['subjects'] else 'No marks',
            'total': int(row['total']) if pd.notna(row['total']) else 0,
            'average': round(avg, 2),
            'grade': calculate_grade(avg)
        })
    return results


def get_subject_average():
    """Return dictionary of subject-wise average marks"""
    df = get_results_dataframe()
    if df.empty or df['marks'].isna().all():
        return {}

    subject_avg = df.groupby('subject')['marks'].mean().round(2)
    return subject_avg.to_dict()


def get_topper():
    """Return topper details as a dictionary"""
    df = get_results_dataframe()
    if df.empty or df['marks'].isna().all():
        return None

    student_avg = df.groupby(['name', 'roll_no', 'class'])['marks'].mean().reset_index()
    student_avg.columns = ['name', 'roll_no', 'class', 'average']

    topper_row = student_avg.loc[student_avg['average'].idxmax()]
    return {
        'name': topper_row['name'],
        'roll_no': topper_row['roll_no'],
        'class': topper_row['class'] if pd.notna(topper_row['class']) else '-',
        'average': round(topper_row['average'], 2)
    }


def get_pass_percentage(pass_mark=40):
    """Calculate overall pass percentage"""
    df = get_results_dataframe()
    if df.empty or df['marks'].isna().all():
        return 0.0

    student_avg = df.groupby('student_id')['marks'].mean()
    total_students = len(student_avg)
    passed = (student_avg >= pass_mark).sum()

    return round((passed / total_students) * 100, 2)


def generate_subject_graph(save_path='static/images/subject_avg.png'):
    """
    Generate a bar chart of subject-wise average marks
    and save it as an image.
    Returns True if graph was created successfully.
    """
    subject_avg = get_subject_average()
    if not subject_avg:
        return False

    # Ensure directory exists
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    subjects = list(subject_avg.keys())
    averages = list(subject_avg.values())

    plt.figure(figsize=(10, 5))
    colors = ['#4CAF50', '#2196F3', '#FF9800', '#9C27B0', '#F44336', '#00BCD4']
    bars = plt.bar(subjects, averages, color=colors[:len(subjects)])

    plt.title('Subject-wise Average Marks', fontsize=14, fontweight='bold')
    plt.xlabel('Subjects')
    plt.ylabel('Average Marks')
    plt.ylim(0, 100)
    plt.xticks(rotation=15)

    # Add value labels on bars
    for bar, avg in zip(bars, averages):
        plt.text(bar.get_x() + bar.get_width() / 2,
                 bar.get_height() + 1.5,
                 f'{avg}',
                 ha='center', va='bottom', fontsize=10)

    plt.tight_layout()
    plt.savefig(save_path, dpi=100)
    plt.close()
    return True