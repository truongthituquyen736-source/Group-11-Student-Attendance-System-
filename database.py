
import sqlite3
import os
import hashlib
from datetime import datetime, timedelta
import secrets
import string

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "attendance.db")

# === HÀM LẤY GIỜ VIỆT NAM (UTC+7) ===
def get_vn_time():
    return (datetime.utcnow() + timedelta(hours=7)).strftime("%Y-%m-%d %H:%M:%S")

def get_connection():
    if not os.path.exists(DB_PATH): init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON;")
    
    # 1. TẠO BẢNG
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        role TEXT NOT NULL CHECK (role IN ('ADMIN','TEACHER','STUDENT')),
        is_active INTEGER NOT NULL DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS password_resets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        token TEXT NOT NULL UNIQUE,
        expires_at DATETIME NOT NULL,
        used INTEGER NOT NULL DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS teachers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL UNIQUE,
        teacher_code TEXT NOT NULL UNIQUE,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS classes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        class_code TEXT NOT NULL UNIQUE,
        class_name TEXT NOT NULL,
        homeroom_teacher_id INTEGER,
        is_active INTEGER NOT NULL DEFAULT 1,
        FOREIGN KEY (homeroom_teacher_id) REFERENCES teachers(id)
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL UNIQUE,
        student_code TEXT NOT NULL UNIQUE,
        gender TEXT CHECK (gender IN ('M','F','O')),
        class_id INTEGER,
        note TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (class_id) REFERENCES classes(id)
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject_code TEXT NOT NULL UNIQUE,
        subject_name TEXT NOT NULL
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS class_subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        class_id INTEGER NOT NULL,
        subject_id INTEGER NOT NULL,
        teacher_id INTEGER NOT NULL,
        UNIQUE (class_id, subject_id),
        FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE,
        FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
        FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS Enrollment (
        EnrollmentID INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        class_id INTEGER,
        enrollment_date DATE,
        status TEXT CHECK (status IN ('Active', 'Canceled')),
        FOREIGN KEY (student_id) REFERENCES students(id),
        FOREIGN KEY (class_id) REFERENCES classes(id)
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS attendance_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        class_subject_id INTEGER NOT NULL,
        session_code TEXT NOT NULL UNIQUE,
        date DATE NOT NULL,
        start_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        end_time DATETIME,
        status TEXT NOT NULL CHECK (status IN ('ACTIVE','CLOSED')),
        close_at DATETIME,
        created_by INTEGER NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (class_subject_id) REFERENCES class_subjects(id) ON DELETE CASCADE,
        FOREIGN KEY (created_by) REFERENCES teachers(id)
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS Attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL,
        student_id INTEGER NOT NULL,
        status TEXT NOT NULL CHECK (status IN ('PRESENT','ABSENT','ABSENT_EXCUSED','LATE')),
        note TEXT,
        marked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME,
        updated_by INTEGER,
        UNIQUE (session_id, student_id),
        FOREIGN KEY (session_id) REFERENCES attendance_sessions(id) ON DELETE CASCADE,
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
        FOREIGN KEY (updated_by) REFERENCES teachers(id)
    )""")
    conn.close()

# --- HÀM HỖ TRỢ ---
def row_to_dict(row): return dict(row) if row else None
def rows_to_list(rows): return [row_to_dict(r) for r in rows]

# --- TRUY VẤN CƠ BẢN ---
def get_user_by_username(username: str):
    conn = get_connection()
    try:
        cur = conn.execute("SELECT * FROM users WHERE username = ? AND is_active = 1", (username,))
        return row_to_dict(cur.fetchone())
    finally: conn.close()

def get_user_by_email(email: str):
    conn = get_connection()
    try:
        cur = conn.execute("SELECT * FROM users WHERE email = ? AND is_active = 1", (email,))
        return row_to_dict(cur.fetchone())
    finally: conn.close()

# --- QUÊN MẬT KHẨU & ĐỔI MK ---
def request_password_reset(email: str):
    user = get_user_by_email(email)
    if not user: return None
    token = ''.join(secrets.choice(string.digits) for _ in range(6))
    expires = (datetime.utcnow() + timedelta(hours=7, minutes=15)).strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection()
    try:
        conn.execute("INSERT INTO password_resets (user_id, token, expires_at) VALUES (?, ?, ?)", (user["id"], token, expires))
        conn.commit()
        return token
    finally: conn.close()

def reset_password_with_token(token, new_pass_hash):
    conn = get_connection()
    try:
        now_vn = get_vn_time()
        cur = conn.execute(f"SELECT user_id FROM password_resets WHERE token = ? AND used = 0 AND expires_at > '{now_vn}'", (token,))
        row = cur.fetchone()
        if not row: return False
        
        user_id = row[0]
        conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_pass_hash, user_id))
        conn.execute("UPDATE password_resets SET used = 1 WHERE token = ?", (token,))
        conn.commit()
        return True
    except: return False
    finally: conn.close()

def update_password(user_id, new_password_hash):
    conn = get_connection()
    try:
        conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_password_hash, user_id))
        conn.commit()
        return True
    except: return False
    finally: conn.close()

# --- LẤY DỮ LIỆU ---
def get_teacher_by_user_id(user_id: int):
    conn = get_connection()
    try:
        cur = conn.execute("SELECT t.*, u.full_name FROM teachers t JOIN users u ON u.id = t.user_id WHERE t.user_id = ?", (user_id,))
        return row_to_dict(cur.fetchone())
    finally: conn.close()

def get_student_by_user_id(user_id: int):
    conn = get_connection()
    try:
        cur = conn.execute("SELECT s.*, u.full_name FROM students s JOIN users u ON u.id = s.user_id WHERE s.user_id = ?", (user_id,))
        return row_to_dict(cur.fetchone())
    finally: conn.close()

def get_classes_for_teacher(teacher_id: int):
    conn = get_connection()
    try:
        cur = conn.execute("""
            SELECT cs.id AS class_subject_id, c.id AS class_id, c.class_code, c.class_name,
                   s.id AS subject_id, s.subject_code, s.subject_name
            FROM class_subjects cs
            JOIN classes c ON c.id = cs.class_id
            JOIN subjects s ON s.id = cs.subject_id
            WHERE cs.teacher_id = ?
        """, (teacher_id,))
        return rows_to_list(cur.fetchall())
    finally: conn.close()

def get_students_in_class(class_id: int):
    conn = get_connection()
    try:
        cur = conn.execute("""
            SELECT s.id AS student_id, s.student_code, u.full_name, s.gender, u.email
            FROM students s JOIN users u ON u.id = s.user_id
            WHERE s.class_id = ?
        """, (class_id,))
        return rows_to_list(cur.fetchall())
    finally: conn.close()

# --- XỬ LÝ ĐIỂM DANH ---
def create_attendance_session(class_subject_id, session_code, date_str, created_by):
    conn = get_connection()
    try:
        now_vn = get_vn_time()
        cur = conn.execute(f"""
            INSERT INTO attendance_sessions (class_subject_id, session_code, date, status, created_by, start_time, created_at)
            VALUES (?, ?, ?, 'ACTIVE', ?, '{now_vn}', '{now_vn}')
        """, (class_subject_id, session_code, date_str, created_by))
        conn.commit()
        return cur.lastrowid
    finally: conn.close()

def get_open_session_for_class_subject(class_subject_id):
    conn = get_connection()
    try:
        cur = conn.execute("SELECT * FROM attendance_sessions WHERE class_subject_id = ? AND status = 'ACTIVE'", (class_subject_id,))
        return row_to_dict(cur.fetchone())
    finally: conn.close()

def close_attendance_session(session_id):
    conn = get_connection()
    try:
        now_vn = get_vn_time()
        conn.execute(f"UPDATE attendance_sessions SET status = 'CLOSED', end_time = '{now_vn}' WHERE id = ?", (session_id,))
        conn.commit()
    finally: conn.close()

def upsert_attendance_record(session_id, student_id, status, note, updated_by):
    conn = get_connection()
    try:
        now_vn = get_vn_time()
        conn.execute(f"""
            INSERT OR REPLACE INTO Attendance (session_id, student_id, status, note, marked_at, updated_at, updated_by)
            VALUES (?, ?, ?, ?, '{now_vn}', '{now_vn}', ?)
        """, (session_id, student_id, status, note, updated_by))
        conn.commit()
    finally: conn.close()

def get_attendance_records_for_session(session_id):
    conn = get_connection()
    try:
        cur = conn.execute("""
            SELECT ar.*, s.student_code, u.full_name
            FROM Attendance ar
            JOIN students s ON s.id = ar.student_id
            JOIN users u ON u.id = s.user_id
            WHERE ar.session_id = ?
        """, (session_id,))
        return rows_to_list(cur.fetchall())
    finally: conn.close()

def get_open_sessions_for_student(student_id):
    conn = get_connection()
    try:
        cur = conn.execute("""
            SELECT s.*, c.class_code, sub.subject_name
            FROM attendance_sessions s
            JOIN class_subjects cs ON s.class_subject_id = cs.id
            JOIN classes c ON cs.class_id = c.id
            JOIN subjects sub ON cs.subject_id = sub.id
            JOIN Enrollment e ON e.class_id = c.id
            WHERE e.student_id = ? AND s.status = 'ACTIVE'
        """, (student_id,))
        return rows_to_list(cur.fetchall())
    finally: conn.close()

def student_mark_attendance(student_id, session_id, status="PRESENT", note=None):
    conn = get_connection()
    try:
        now_vn = get_vn_time()
        conn.execute(f"""
            INSERT OR REPLACE INTO Attendance (session_id, student_id, status, note, marked_at)
            VALUES (?, ?, ?, ?, '{now_vn}')
        """, (session_id, student_id, status, note))
        conn.commit()
    finally: conn.close()

def get_student_history(student_id):
    conn = get_connection()
    try:
        cur = conn.execute("""
            SELECT a.status, a.marked_at, a.note, s.session_code, s.date, sub.subject_name
            FROM Attendance a
            JOIN attendance_sessions s ON a.session_id = s.id
            JOIN class_subjects cs ON s.class_subject_id = cs.id
            JOIN subjects sub ON cs.subject_id = sub.id
            WHERE a.student_id = ?
            ORDER BY s.date DESC
        """, (student_id,))
        return rows_to_list(cur.fetchall())
    finally: conn.close()

# --- ADMIN MANAGEMENT ---
def get_all_users():
    conn = get_connection()
    try:
        cur = conn.execute("SELECT id, username, full_name, role, email FROM users ORDER BY id DESC")
        return rows_to_list(cur.fetchall())
    finally: conn.close()

def create_user_full(username, password_hash, full_name, email, role):
    conn = get_connection()
    try:
        cur = conn.execute("INSERT INTO users (username, password_hash, full_name, email, role) VALUES (?, ?, ?, ?, ?)",
                     (username, password_hash, full_name, email, role))
        user_id = cur.lastrowid
        if role == 'TEACHER':
            code = f"GV{user_id:03d}"
            conn.execute("INSERT INTO teachers (user_id, teacher_code) VALUES (?, ?)", (user_id, code))
        elif role == 'STUDENT':
            code = f"SV{user_id:03d}"
            conn.execute("INSERT INTO students (user_id, student_code, gender, class_id) VALUES (?, ?, 'M', NULL)", (user_id, code))
        conn.commit()
        return True, "Tạo thành công"
    except Exception as e:
        return False, str(e)
    finally: conn.close()

def delete_user(user_id):
    conn = get_connection()
    try:
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
    finally: conn.close()

def get_school_attendance_report(start_date=None, end_date=None):
    conn = get_connection()
    try:
        query = """
            SELECT c.class_code, c.class_name, 
                   COUNT(DISTINCT s.id) AS total_students,
                   COUNT(DISTINCT asess.id) AS total_sessions,
                   SUM(CASE WHEN ar.status = 'PRESENT' THEN 1 ELSE 0 END) AS present_count,
                   SUM(CASE WHEN ar.status LIKE 'ABSENT%' THEN 1 ELSE 0 END) AS absent_count,
                   SUM(CASE WHEN ar.status = 'LATE' THEN 1 ELSE 0 END) AS late_count
            FROM classes c
            LEFT JOIN students s ON s.class_id = c.id
            LEFT JOIN class_subjects cs ON cs.class_id = c.id
            LEFT JOIN attendance_sessions asess ON asess.class_subject_id = cs.id AND asess.status = 'CLOSED'
            LEFT JOIN Attendance ar ON ar.session_id = asess.id
        """
        params = []
        if start_date:
            query += " AND asess.date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND asess.date <= ?"
            params.append(end_date)
        query += " GROUP BY c.id"
        cur = conn.execute(query, params)
        return rows_to_list(cur.fetchall())
    finally: conn.close()

def get_all_teachers():
    conn = get_connection()
    try:
        cur = conn.execute("SELECT t.id, t.teacher_code, u.full_name FROM teachers t JOIN users u ON u.id = t.user_id")
        return rows_to_list(cur.fetchall())
    finally: conn.close()

def get_all_classes():
    conn = get_connection()
    try:
        cur = conn.execute("""
            SELECT c.*, u.full_name as teacher_name 
            FROM classes c 
            LEFT JOIN teachers t ON c.homeroom_teacher_id = t.id 
            LEFT JOIN users u ON t.user_id = u.id
        """)
        return rows_to_list(cur.fetchall())
    finally: conn.close()

def create_class(code, name, teacher_id):
    conn = get_connection()
    try:
        conn.execute("INSERT INTO classes (class_code, class_name, homeroom_teacher_id) VALUES (?, ?, ?)", (code, name, teacher_id))
        conn.commit()
        return True, ""
    except Exception as e: return False, str(e)
    finally: conn.close()

def delete_class(class_id):
    conn = get_connection()
    try:
        conn.execute("DELETE FROM classes WHERE id = ?", (class_id,))
        conn.commit()
    finally: conn.close()
