# utils/db.py
# Database connection helper

import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG


def get_connection():
    """
    Create and return a MySQL database connection.
    Returns None if connection fails.
    """
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"[DB Error] Failed to connect: {e}")
        return None


def execute_query(query, params=None, fetch=False, fetchone=False):
    """
    Execute a SQL query.
    
    Parameters:
        query   : SQL query string
        params  : tuple or list of parameters (optional)
        fetch   : True → return all rows
        fetchone: True → return single row
    
    Returns:
        - For SELECT: list of dicts / single dict / None
        - For INSERT/UPDATE/DELETE: True on success, False on failure
    """
    connection = get_connection()
    if not connection:
        return None

    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, params or ())

        if fetchone:
            result = cursor.fetchone()
        elif fetch:
            result = cursor.fetchall()
        else:
            connection.commit()
            result = True

        return result

    except Error as e:
        print(f"[DB Error] Query failed: {e}")
        if connection:
            connection.rollback()
        return None

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def get_all_students():
    """Return list of all students (id, name, roll_no)"""
    query = "SELECT student_id, name, roll_no, class FROM students ORDER BY name"
    return execute_query(query, fetch=True) or []


def insert_student(name, roll_no, class_name=None, email=None):
    """Insert a new student. Returns True on success."""
    query = """
        INSERT INTO students (name, roll_no, class, email)
        VALUES (%s, %s, %s, %s)
    """
    return execute_query(query, (name, roll_no, class_name, email))


def insert_marks(student_id, subject, marks):
    """Insert marks for a subject. Returns True on success."""
    query = """
        INSERT INTO marks (student_id, subject, marks)
        VALUES (%s, %s, %s)
    """
    return execute_query(query, (student_id, subject, marks))