# config.py
# Database configuration

DB_CONFIG = {
    'host': 'localhost',
    'user': 'khalique3006',          # change if your MySQL username is different
    'password': 'Khalique@3006',  # leave empty if no password
    'database': 'student_result_db'
}

# Secret key for Flask (change this in production)
SECRET_KEY = 'your-secret-key-change-this'


# CREATE DATABASE student_result_db;
# USE student_result_db;

# CREATE TABLE students (
#     student_id INT AUTO_INCREMENT PRIMARY KEY,
#     name VARCHAR(100) NOT NULL,
#     roll_no VARCHAR(20) UNIQUE NOT NULL,
#     class VARCHAR(20),
#     email VARCHAR(100),
#     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
# );

# CREATE TABLE marks (
#     mark_id INT AUTO_INCREMENT PRIMARY KEY,
#     student_id INT,
#     subject VARCHAR(50) NOT NULL,
#     marks INT CHECK (marks BETWEEN 0 AND 100),
#     FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE
# );