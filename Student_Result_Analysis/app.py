# app.py
from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
from mysql.connector import Error
import pandas as pd
import matplotlib
matplotlib.use('Agg')          # important for servers without display
import matplotlib.pyplot as plt
import os
from config import DB_CONFIG, SECRET_KEY

app = Flask(__name__)
app.secret_key = SECRET_KEY

# Ensure static/images folder exists for graphs
os.makedirs('static/images', exist_ok=True)


def get_db_connection():
    """Create and return a MySQL connection"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None


def calculate_grade(average):
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


@app.route('/')
def index():
    conn = get_db_connection()
    if not conn:
        flash("Database connection failed!", "danger")
        return render_template('index.html', total_students=0, pass_percentage=0)

    cursor = conn.cursor(dictionary=True)

    # Total students
    cursor.execute("SELECT COUNT(*) AS total FROM students")
    total_students = cursor.fetchone()['total']

    # Pass percentage calculation
    query = """
        SELECT s.student_id, AVG(m.marks) AS avg_marks
        FROM students s
        LEFT JOIN marks m ON s.student_id = m.student_id
        GROUP BY s.student_id
    """
    cursor.execute(query)
    results = cursor.fetchall()

    if results:
        passed = sum(1 for r in results if r['avg_marks'] is not None and r['avg_marks'] >= 40)
        pass_percentage = round((passed / len(results)) * 100, 2)
    else:
        pass_percentage = 0

    cursor.close()
    conn.close()

    return render_template('index.html',
                           total_students=total_students,
                           pass_percentage=pass_percentage)


@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        name = request.form['name'].strip()
        roll_no = request.form['roll_no'].strip()
        class_name = request.form['class'].strip()
        email = request.form['email'].strip()

        if not name or not roll_no:
            flash("Name and Roll No are required!", "warning")
            return redirect(url_for('add_student'))

        conn = get_db_connection()
        if not conn:
            flash("Database connection failed!", "danger")
            return redirect(url_for('add_student'))

        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO students (name, roll_no, class, email) VALUES (%s, %s, %s, %s)",
                (name, roll_no, class_name, email)
            )
            conn.commit()
            flash("Student added successfully!", "success")
        except Error as e:
            flash(f"Error: {e}", "danger")
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('add_student'))

    return render_template('add_student.html')


@app.route('/add_marks', methods=['GET', 'POST'])
def add_marks():
    conn = get_db_connection()
    if not conn:
        flash("Database connection failed!", "danger")
        return render_template('add_marks.html', students=[])

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT student_id, name, roll_no FROM students ORDER BY name")
    students = cursor.fetchall()

    if request.method == 'POST':
        student_id = request.form['student_id']
        subjects = ['Mathematics', 'Science', 'English', 'History', 'Computer']
        marks_list = []

        for subject in subjects:
            mark = request.form.get(subject)
            if mark:
                try:
                    mark = int(mark)
                    if 0 <= mark <= 100:
                        marks_list.append((student_id, subject, mark))
                except ValueError:
                    continue

        if marks_list:
            try:
                cursor.executemany(
                    "INSERT INTO marks (student_id, subject, marks) VALUES (%s, %s, %s)",
                    marks_list
                )
                conn.commit()
                flash("Marks added successfully!", "success")
            except Error as e:
                flash(f"Error: {e}", "danger")
        else:
            flash("Please enter valid marks!", "warning")

        cursor.close()
        conn.close()
        return redirect(url_for('add_marks'))

    cursor.close()
    conn.close()
    return render_template('add_marks.html', students=students)


@app.route('/view_results')
def view_results():
    conn = get_db_connection()
    if not conn:
        flash("Database connection failed!", "danger")
        return render_template('view_results.html', results=[])

    query = """
        SELECT s.student_id, s.name, s.roll_no, s.class,
               GROUP_CONCAT(CONCAT(m.subject, ':', m.marks) SEPARATOR ', ') AS subjects,
               SUM(m.marks) AS total,
               AVG(m.marks) AS average
        FROM students s
        LEFT JOIN marks m ON s.student_id = m.student_id
        GROUP BY s.student_id, s.name, s.roll_no, s.class
        ORDER BY s.name
    """
    df = pd.read_sql(query, conn)
    conn.close()

    results = []
    for _, row in df.iterrows():
        avg = row['average'] if pd.notna(row['average']) else 0
        results.append({
            'name': row['name'],
            'roll_no': row['roll_no'],
            'class': row['class'],
            'subjects': row['subjects'] if pd.notna(row['subjects']) else 'No marks',
            'total': int(row['total']) if pd.notna(row['total']) else 0,
            'average': round(avg, 2),
            'grade': calculate_grade(avg)
        })

    return render_template('view_results.html', results=results)


@app.route('/analysis')
def analysis():
    conn = get_db_connection()
    if not conn:
        flash("Database connection failed!", "danger")
        return render_template('analysis.html', topper=None, pass_percentage=0)

    # Load all marks
    query = """
        SELECT s.name, s.roll_no, s.class, m.subject, m.marks
        FROM students s
        JOIN marks m ON s.student_id = m.student_id
    """
    df = pd.read_sql(query, conn)
    conn.close()

    if df.empty:
        return render_template('analysis.html', topper=None, pass_percentage=0,
                               subject_avg={}, graph_exists=False)

    # Subject-wise average
    subject_avg = df.groupby('subject')['marks'].mean().round(2).to_dict()

    # Student-wise average for topper and pass %
    student_avg = df.groupby(['name', 'roll_no', 'class'])['marks'].mean().reset_index()
    student_avg.columns = ['name', 'roll_no', 'class', 'average']

    # Topper
    topper_row = student_avg.loc[student_avg['average'].idxmax()]
    topper = {
        'name': topper_row['name'],
        'roll_no': topper_row['roll_no'],
        'class': topper_row['class'],
        'average': round(topper_row['average'], 2)
    }

    # Pass percentage
    passed = (student_avg['average'] >= 40).sum()
    pass_percentage = round((passed / len(student_avg)) * 100, 2)

    # Generate subject-wise bar chart
    plt.figure(figsize=(10, 5))
    subjects = list(subject_avg.keys())
    averages = list(subject_avg.values())
    bars = plt.bar(subjects, averages, color=['#4CAF50', '#2196F3', '#FF9800', '#9C27B0', '#F44336'])
    plt.title('Subject-wise Average Marks', fontsize=14, fontweight='bold')
    plt.xlabel('Subjects')
    plt.ylabel('Average Marks')
    plt.ylim(0, 100)
    plt.xticks(rotation=15)

    for bar, avg in zip(bars, averages):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                 f'{avg}', ha='center', va='bottom', fontsize=10)

    plt.tight_layout()
    graph_path = 'static/images/subject_avg.png'
    plt.savefig(graph_path)
    plt.close()

    return render_template('analysis.html',
                           topper=topper,
                           pass_percentage=pass_percentage,
                           subject_avg=subject_avg,
                           graph_exists=True)


if __name__ == '__main__':
    app.run(debug=True)