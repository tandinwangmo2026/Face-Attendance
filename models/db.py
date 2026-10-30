import sqlite3
import os

# This creates the database file in the main folder
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database.db')

def get_db():
    # Opens the connection to the database
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    # Creates the tables if they don't exist
    conn = get_db()
    c = conn.cursor()

    # Table 1: Admins (for login)
    c.execute('''CREATE TABLE IF NOT EXISTS admins (
        admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )''')

    # Table 2: Students (with face encoding)
    c.execute('''CREATE TABLE IF NOT EXISTS students (
        student_id INTEGER PRIMARY KEY AUTOINCREMENT,
        enrollment_no TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        department TEXT NOT NULL,
        face_encoding TEXT,
        image_path TEXT
    )''')

    # Table 3: Attendance records
    c.execute('''CREATE TABLE IF NOT EXISTS attendance (
        attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
        enrollment_no TEXT NOT NULL,
        subject_code TEXT,
        attendance_date TEXT NOT NULL,
        status TEXT DEFAULT 'Present'
    )''')

    # Create default admin: username 'admin', password 'admin123'
    c.execute("INSERT OR IGNORE INTO admins (username, password) VALUES ('admin', 'admin123')")
    
    conn.commit()
    conn.close()
    print("✅ Database initialized successfully!")