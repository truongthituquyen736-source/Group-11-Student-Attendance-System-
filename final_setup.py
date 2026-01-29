import os
import sqlite3
import hashlib
from datetime import datetime, timedelta

# --- CẤU HÌNH ĐƯỜNG DẪN ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "attendance.db")
GUI_PATH = os.path.join(BASE_DIR, "gui.py")
DATABASE_PY_PATH = os.path.join(BASE_DIR, "database.py")

# ==============================================================================
# PHẦN 1: NỘI DUNG DATABASE.PY (GỐC + FIX GIỜ VN + QUÊN MẬT KHẨU)
# ==============================================================================
db_content = r'''
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
'''

# ==============================================================================
# PHẦN 2: NỘI DUNG GUI.PY (TIẾNG VIỆT + FIX SCROLLBAR + FIX QUÊN MẬT KHẨU)
# ==============================================================================
gui_content = r'''
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import database as db
from auth import hash_password, verify_password, validate_email, validate_required
from datetime import datetime

class BaseDashboard:
    def __init__(self, root, user):
        self.root = root
        self.user = user
        self.content_frame = None
        self.create_sidebar()
    
    def create_sidebar(self):
        sidebar = tk.Frame(self.root, bg="#1976D2", width=220)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        
        tk.Label(sidebar, text="HỆ THỐNG\nĐIỂM DANH", font=("Segoe UI", 14, "bold"), bg="#1976D2", fg="white").pack(pady=20)
        tk.Label(sidebar, text=f"Xin chào,\n{self.user['full_name']}", font=("Segoe UI", 10), bg="#1976D2", fg="white").pack(pady=10)
        
        menu_frame = tk.Frame(sidebar, bg="#1976D2")
        menu_frame.pack(pady=20, fill="both", expand=True)
        
        self.menu_items = self.get_menu_items()
        for key, text, color in self.menu_items:
            tk.Button(menu_frame, text=text, bg=color, fg="white", font=("Segoe UI", 10, "bold"),
                      command=lambda k=key: self.switch_view(k), height=2, relief="flat").pack(fill="x", pady=2, padx=10)
        
        tk.Button(sidebar, text="Đổi mật khẩu", bg="#0288D1", fg="white", font=("Segoe UI", 10),
                  command=self.change_password_dialog).pack(side="bottom", fill="x", pady=5, padx=10)

        tk.Button(sidebar, text="Đăng xuất", bg="#D32F2F", fg="white", font=("Segoe UI", 10),
                command=self.logout).pack(side="bottom", fill="x", pady=20, padx=10)
    
    def get_menu_items(self): return []
    
    def switch_view(self, view_key):
        if self.content_frame: self.content_frame.destroy()
        self.content_frame = tk.Frame(self.root, bg="white")
        self.content_frame.pack(side="right", fill="both", expand=True, padx=20, pady=20)
        
        view_method = getattr(self, f"render_{view_key}_view", None)
        if view_method: view_method()
        else: tk.Label(self.content_frame, text="Chức năng đang phát triển...", font=("Segoe UI", 14), bg="white").pack(pady=50)
    
    def create_scrolled_treeview(self, parent, columns):
        frame = tk.Frame(parent)
        frame.pack(fill="both", expand=True, pady=5)
        ysb = ttk.Scrollbar(frame, orient="vertical")
        ysb.pack(side="right", fill="y")
        xsb = ttk.Scrollbar(frame, orient="horizontal")
        xsb.pack(side="bottom", fill="x")
        tree = ttk.Treeview(frame, columns=columns, show="headings", 
                            yscrollcommand=ysb.set, xscrollcommand=xsb.set)
        ysb.config(command=tree.yview); xsb.config(command=tree.xview)
        tree.pack(side="left", fill="both", expand=True)
        for c in columns:
            tree.heading(c, text=c); tree.column(c, width=150, minwidth=100)
        return tree

    def change_password_dialog(self):
        win = tk.Toplevel(self.root); win.title("Đổi mật khẩu"); win.geometry("300x200")
        tk.Label(win, text="Mật khẩu cũ:").pack(pady=5)
        e_old = tk.Entry(win, show="*"); e_old.pack()
        tk.Label(win, text="Mật khẩu mới:").pack(pady=5)
        e_new = tk.Entry(win, show="*"); e_new.pack()
        
        def save():
            if not verify_password(e_old.get(), self.user["password_hash"]):
                messagebox.showerror("Lỗi", "Mật khẩu cũ không đúng"); return
            if len(e_new.get()) < 6:
                messagebox.showerror("Lỗi", "Mật khẩu mới phải >= 6 ký tự"); return
            
            if db.update_password(self.user["id"], hash_password(e_new.get())):
                messagebox.showinfo("Thành công", "Đổi mật khẩu thành công!"); win.destroy()
            else: messagebox.showerror("Lỗi", "Không thể cập nhật")
        
        tk.Button(win, text="Lưu", command=save, bg="#28a745", fg="white").pack(pady=15)

    def logout(self):
        if messagebox.askyesno("Đăng xuất", "Bạn có chắc muốn đăng xuất?"):
            self.root.destroy(); import main; main.main()

class AdminDashboard(BaseDashboard):
    def get_menu_items(self):
        return [("users", "Quản lý Người dùng", "#7B1FA2"), ("classes", "Quản lý Lớp học", "#7B1FA2"), ("report", "Báo cáo Tổng hợp", "#E64A19")]
    
    def render_users_view(self):
        tk.Label(self.content_frame, text="QUẢN LÝ NGƯỜI DÙNG", font=("Segoe UI", 16, "bold"), fg="#7B1FA2", bg="white").pack(pady=10)
        f = tk.LabelFrame(self.content_frame, text="Thêm mới", bg="white"); f.pack(fill="x")
        entries = {}
        for i, (lbl, key) in enumerate([("User:",0), ("Tên:",1), ("Email:",2)]):
            tk.Label(f, text=lbl, bg="white").grid(row=0, column=i*2)
            e = tk.Entry(f); e.grid(row=0, column=i*2+1); entries[key] = e
        tk.Label(f, text="Role:", bg="white").grid(row=0, column=6)
        cb = ttk.Combobox(f, values=["STUDENT", "TEACHER", "ADMIN"], width=8); cb.current(0); cb.grid(row=0, column=7)
        def add():
            s, m = db.create_user_full(entries[0].get(), hash_password("123456"), entries[1].get(), entries[2].get(), cb.get())
            if s: messagebox.showinfo("OK", "Đã tạo. Pass: 123456"); load()
            else: messagebox.showerror("Err", m)
        tk.Button(f, text="Thêm", command=add, bg="green", fg="white").grid(row=0, column=8, padx=10)
        
        cols = ("ID", "Tên ĐN", "Họ Tên", "Email", "Vai Trò")
        tree = self.create_scrolled_treeview(self.content_frame, cols)
        def load():
            for i in tree.get_children(): tree.delete(i)
            for u in db.get_all_users(): tree.insert("", "end", values=list(u.values()))
        load()
        def delete():
            if not tree.selection(): return
            if messagebox.askyesno("Xóa", "Chắc chắn xóa?"): db.delete_user(tree.item(tree.selection()[0], "values")[0]); load()
        tk.Button(self.content_frame, text="Xóa", command=delete, bg="red", fg="white").pack(pady=5)

    def render_classes_view(self):
        tk.Label(self.content_frame, text="QUẢN LÝ LỚP HỌC", font=("Segoe UI", 16, "bold"), fg="#7B1FA2", bg="white").pack(pady=10)
        f = tk.LabelFrame(self.content_frame, text="Thêm lớp", bg="white"); f.pack(fill="x")
        tk.Label(f, text="Mã Lớp:", bg="white").grid(row=0, column=0)
        e_code = tk.Entry(f); e_code.grid(row=0, column=1)
        tk.Label(f, text="Tên Lớp:", bg="white").grid(row=0, column=2)
        e_name = tk.Entry(f); e_name.grid(row=0, column=3)
        teachers = db.get_all_teachers(); t_vals = [f"{t['id']} - {t['full_name']}" for t in teachers]
        tk.Label(f, text="GVCN:", bg="white").grid(row=0, column=4)
        cb_t = ttk.Combobox(f, values=t_vals); cb_t.grid(row=0, column=5)
        def add():
            if not e_code.get() or not cb_t.get(): return
            tid = cb_t.get().split(" - ")[0]
            s, m = db.create_class(e_code.get(), e_name.get(), tid)
            if s: messagebox.showinfo("OK", "Thêm lớp thành công"); load()
            else: messagebox.showerror("Err", m)
        tk.Button(f, text="Thêm", command=add, bg="green", fg="white").grid(row=0, column=6, padx=10)
        
        tree = self.create_scrolled_treeview(self.content_frame, ("ID","Mã","Tên","GVCN"))
        def load():
            for i in tree.get_children(): tree.delete(i)
            for c in db.get_all_classes(): tree.insert("", "end", values=(c['id'], c['class_code'], c['class_name'], c['teacher_name']))
        load()
        def delete():
            if tree.selection(): db.delete_class(tree.item(tree.selection()[0], "values")[0]); load()
        tk.Button(self.content_frame, text="Xóa Lớp", command=delete, bg="red", fg="white").pack()

    def render_report_view(self):
        tk.Label(self.content_frame, text="BÁO CÁO TỔNG HỢP", font=("Segoe UI", 16, "bold"), bg="white", fg="#E64A19").pack(pady=10)
        
        today = datetime.now()
        start_of_month = today.replace(day=1).strftime("%Y-%m-%d")
        today_str = today.strftime("%Y-%m-%d")

        filter_frame = tk.Frame(self.content_frame, bg="white")
        filter_frame.pack(pady=5)
        tk.Label(filter_frame, text="Từ:", bg="white").pack(side="left")
        from_entry = tk.Entry(filter_frame, width=12); from_entry.insert(0, start_of_month); from_entry.pack(side="left", padx=5)
        tk.Label(filter_frame, text="Đến:", bg="white").pack(side="left")
        to_entry = tk.Entry(filter_frame, width=12); to_entry.insert(0, today_str); to_entry.pack(side="left", padx=5)

        cols = ("Lớp", "Tên Lớp", "Sĩ số", "Tổng buổi", "Đi học", "Vắng", "Muộn")
        tree = self.create_scrolled_treeview(self.content_frame, cols)

        def load_report():
            for i in tree.get_children(): tree.delete(i)
            data = db.get_school_attendance_report(from_entry.get(), to_entry.get())
            for r in data: tree.insert("", "end", values=list(r.values()))
            
        tk.Button(filter_frame, text="Xem", command=load_report, bg="#E64A19", fg="white").pack(side="left", padx=10)
        load_report()

class TeacherDashboard(BaseDashboard):
    def get_menu_items(self): return [("attendance", "Quản lý Điểm danh", "#388E3C")]
    def render_attendance_view(self):
        tk.Label(self.content_frame, text="QUẢN LÝ ĐIỂM DANH", font=("Segoe UI", 16, "bold"), bg="white", fg="#388E3C").pack(pady=10)
        teacher_info = db.get_teacher_by_user_id(self.user["id"])
        if not teacher_info: tk.Label(self.content_frame, text="Lỗi: Chưa cấp quyền Giáo viên", fg="red").pack(); return
        self.classes = db.get_classes_for_teacher(teacher_info["id"])
        if not self.classes: tk.Label(self.content_frame, text="Giáo viên chưa được phân công lớp nào.", bg="white").pack(); return

        frame_top = tk.Frame(self.content_frame, bg="white"); frame_top.pack(fill="x", padx=20)
        self.cb_class = ttk.Combobox(frame_top, values=[f"{c['class_code']} - {c['subject_name']}" for c in self.classes], width=40, state="readonly")
        self.cb_class.current(0); self.cb_class.pack(side="left", padx=5)
        tk.Button(frame_top, text="Tải Dữ Liệu", bg="#1976D2", fg="white", command=self.load_session).pack(side="left")
        
        self.frame_ss = tk.Frame(self.content_frame, bg="white", pady=10); self.frame_ss.pack(fill="x", padx=20)
        self.lbl_stt = tk.Label(self.frame_ss, text="...", font=("Segoe UI", 10, "bold"), bg="white"); self.lbl_stt.pack(side="left")
        self.btn_open = tk.Button(self.frame_ss, text="Mở Buổi Học Mới", bg="#28a745", fg="white", command=self.open_ss)
        self.btn_close = tk.Button(self.frame_ss, text="Đóng Buổi Học", bg="#d32f2f", fg="white", command=self.close_ss)

        self.tree = self.create_scrolled_treeview(self.content_frame, ("ID","Mã","Tên","TT","Ghi chú"))
        self.tree.column("ID", width=0, stretch=False)
        self.tree.bind("<Double-1>", self.edit_att)

    def get_cid(self): return self.classes[self.cb_class.current()]["class_subject_id"]
    def load_session(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        self.curr_ss = db.get_open_session_for_class_subject(self.get_cid())
        if self.curr_ss:
            self.lbl_stt.config(text=f"Đang mở: {self.curr_ss['session_code']} (Ngày: {self.curr_ss['date']})", fg="green")
            self.btn_open.pack_forget(); self.btn_close.pack(side="right")
            recs = {r['student_id']: r for r in db.get_attendance_records_for_session(self.curr_ss['id'])}
        else:
            self.lbl_stt.config(text="Chưa có buổi học nào mở.", fg="#555")
            self.btn_close.pack_forget(); self.btn_open.pack(side="right"); recs = {}
        for s in db.get_students_in_class(self.classes[self.cb_class.current()]['class_id']):
            r = recs.get(s['student_id'])
            self.tree.insert("", "end", values=(s['student_id'], s['student_code'], s['full_name'], r['status'] if r else "---", r['note'] if r else ""))
    def open_ss(self):
        try:
            now_str = datetime.now().strftime('%Y-%m-%d')
            code = f"{self.classes[self.cb_class.current()]['subject_code']}_{now_str}"
            db.create_attendance_session(self.get_cid(), code, now_str, self.user["id"]); self.load_session()
            messagebox.showinfo("Thành công", f"Đã mở buổi học ngày {now_str}")
        except Exception as e: messagebox.showerror("Lỗi", f"Lỗi (Có thể đã mở rồi): {str(e)}")
    def close_ss(self):
        if messagebox.askyesno("Đóng", "Kết thúc buổi học?"): db.close_attendance_session(self.curr_ss['id']); self.load_session()
    def edit_att(self, event):
        if not self.curr_ss: return
        item = self.tree.selection(); 
        if not item: return
        vals = self.tree.item(item, "values")
        win = tk.Toplevel(self.root); win.title(f"Điểm danh: {vals[2]}")
        v = tk.StringVar(value=vals[3] if vals[3] != "---" else "PRESENT")
        tk.Radiobutton(win, text="Có mặt", variable=v, value="PRESENT").pack()
        tk.Radiobutton(win, text="Vắng", variable=v, value="ABSENT").pack()
        def save():
            tid = db.get_teacher_by_user_id(self.user["id"])["id"]
            db.upsert_attendance_record(self.curr_ss['id'], vals[0], v.get(), "", tid); self.load_session(); win.destroy()
        tk.Button(win, text="Lưu", command=save).pack()

class StudentDashboard(BaseDashboard):
    def get_menu_items(self): return [("attend", "Tự Điểm Danh", "#28a745"), ("history", "Lịch Sử", "#F57C00")]
    def render_attend_view(self):
        tk.Label(self.content_frame, text="ĐIỂM DANH HÔM NAY", font=("Segoe UI", 16, "bold"), bg="white").pack(pady=10)
        s_info = db.get_student_by_user_id(self.user["id"])
        if not s_info: return
        sessions = db.get_open_sessions_for_student(s_info['id'])
        if not sessions: tk.Label(self.content_frame, text="Không có buổi học nào đang mở.", bg="white").pack(); return
        for s in sessions:
            f = tk.Frame(self.content_frame, bg="#f8f9fa", bd=1, relief="solid"); f.pack(fill="x", padx=20, pady=5)
            tk.Label(f, text=f"{s['subject_name']} | {s['date']}", bg="#f8f9fa", font=("Segoe UI", 10, "bold")).pack(anchor="w")
            def mark(sid=s['id'], stid=s_info['id']):
                try: db.student_mark_attendance(stid, sid, "PRESENT", ""); messagebox.showinfo("OK", "Điểm danh thành công!")
                except Exception as e: messagebox.showerror("Lỗi", str(e))
            tk.Button(f, text="CÓ MẶT NGAY", bg="#28a745", fg="white", command=mark).pack(pady=5)
    def render_history_view(self):
        tk.Label(self.content_frame, text="LỊCH SỬ ĐIỂM DANH", font=("Segoe UI", 16, "bold"), bg="white", fg="#F57C00").pack(pady=10)
        cols = ("Ngày", "Môn Học", "Trạng Thái", "Ghi Chú")
        tree = self.create_scrolled_treeview(self.content_frame, cols)
        s_info = db.get_student_by_user_id(self.user["id"])
        if s_info:
            for h in db.get_student_history(s_info['id']): tree.insert("", "end", values=(h['date'], h['subject_name'], h['status'], h['note']))

class LoginScreen:
    def __init__(self, root):
        self.root = root
        f = tk.Frame(root, bg="white"); f.pack(expand=True)
        tk.Label(f, text="ĐĂNG NHẬP HỆ THỐNG", font=("Segoe UI", 20, "bold"), bg="white", fg="#1976D2").pack(pady=20)
        tk.Label(f, text="Tên đăng nhập:", bg="white").pack(anchor="w")
        self.eu = tk.Entry(f, width=30); self.eu.pack(pady=5)
        tk.Label(f, text="Mật khẩu:", bg="white").pack(anchor="w")
        self.ep = tk.Entry(f, width=30, show="*"); self.ep.pack(pady=5)
        self.ep.bind("<Return>", lambda e: self.login())
        
        btn_frame = tk.Frame(f, bg="white"); btn_frame.pack(pady=25)
        tk.Button(btn_frame, text="Đăng nhập", command=self.login, bg="#1976D2", fg="white", width=15).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Quên mật khẩu?", command=self.forgot_pw, bg="#757575", fg="white").pack(side="left", padx=5)

    def login(self):
        u = db.get_user_by_username(self.eu.get())
        if u and verify_password(self.ep.get(), u['password_hash']):
            self.root.winfo_children()[0].destroy()
            if u['role'] == "ADMIN": AdminDashboard(self.root, u)
            elif u['role'] == "TEACHER": TeacherDashboard(self.root, u)
            else: StudentDashboard(self.root, u)
        else: messagebox.showerror("Lỗi", "Sai tên đăng nhập hoặc mật khẩu")

    def forgot_pw(self):
        email = simpledialog.askstring("Quên mật khẩu", "Nhập email của bạn:")
        if not email: return
        token = db.request_password_reset(email)
        if token:
            messagebox.showinfo("Email gửi đi (Giả lập)", f"Mã Reset Token của bạn là: {token}\n\n(Hãy nhớ mã này để nhập ở bước sau)")
            self.open_reset_dialog()
        else:
            messagebox.showerror("Lỗi", "Email này không tồn tại trong hệ thống!")

    def open_reset_dialog(self):
        win = tk.Toplevel(self.root); win.title("Đặt lại mật khẩu"); win.geometry("350x250")
        tk.Label(win, text="Nhập mã Reset Token:", font=("Segoe UI", 10)).pack(pady=5)
        e_token = tk.Entry(win, width=30); e_token.pack(pady=5)
        tk.Label(win, text="Nhập mật khẩu mới:", font=("Segoe UI", 10)).pack(pady=5)
        e_pass = tk.Entry(win, width=30, show="*"); e_pass.pack(pady=5)
        
        def submit():
            token = e_token.get().strip(); new_pass = e_pass.get().strip()
            if not token or not new_pass: messagebox.showerror("Lỗi", "Vui lòng nhập đủ thông tin"); return
            if db.reset_password_with_token(token, hash_password(new_pass)):
                messagebox.showinfo("Thành công", "Mật khẩu đã được thay đổi! Hãy đăng nhập lại."); win.destroy()
            else: messagebox.showerror("Lỗi", "Mã Token không đúng hoặc đã hết hạn!")
        tk.Button(win, text="Xác nhận", command=submit, bg="#28a745", fg="white").pack(pady=20)
'''

# ==============================================================================
# PHẦN 3: GHI FILE VÀ RESET DB
# ==============================================================================
def write_file(path, content):
    print(f">>> Đang cập nhật: {path}...")
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print("    [OK] Thành công.")
    except Exception as e:
        print(f"    [FAIL] Lỗi: {e}")

def reset_db_to_vietnamese():
    print(">>> Đang khôi phục Database Tiếng Việt & Tài khoản chuẩn...")
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH) # Xóa DB cũ đi để tạo lại từ đầu
            print("    [OK] Đã xóa DB cũ.")
        except: pass
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON;")
    
    # --- COPY LOGIC TỪ init_db() ---
    
    sql_tables = """
    CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL, full_name TEXT NOT NULL, email TEXT NOT NULL UNIQUE, role TEXT NOT NULL, is_active INTEGER DEFAULT 1, created_at DATETIME DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS password_resets (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, token TEXT, expires_at DATETIME, used INTEGER DEFAULT 0, created_at DATETIME, FOREIGN KEY(user_id) REFERENCES users(id));
    CREATE TABLE IF NOT EXISTS teachers (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, teacher_code TEXT, FOREIGN KEY(user_id) REFERENCES users(id));
    CREATE TABLE IF NOT EXISTS classes (id INTEGER PRIMARY KEY AUTOINCREMENT, class_code TEXT, class_name TEXT, homeroom_teacher_id INTEGER, is_active INTEGER DEFAULT 1, FOREIGN KEY(homeroom_teacher_id) REFERENCES teachers(id));
    CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, student_code TEXT, gender TEXT, class_id INTEGER, note TEXT, FOREIGN KEY(user_id) REFERENCES users(id), FOREIGN KEY(class_id) REFERENCES classes(id));
    CREATE TABLE IF NOT EXISTS subjects (id INTEGER PRIMARY KEY AUTOINCREMENT, subject_code TEXT, subject_name TEXT);
    CREATE TABLE IF NOT EXISTS class_subjects (id INTEGER PRIMARY KEY AUTOINCREMENT, class_id INTEGER, subject_id INTEGER, teacher_id INTEGER, UNIQUE(class_id, subject_id), FOREIGN KEY(class_id) REFERENCES classes(id), FOREIGN KEY(subject_id) REFERENCES subjects(id), FOREIGN KEY(teacher_id) REFERENCES teachers(id));
    CREATE TABLE IF NOT EXISTS Enrollment (EnrollmentID INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, class_id INTEGER, enrollment_date DATE, status TEXT, FOREIGN KEY(student_id) REFERENCES students(id), FOREIGN KEY(class_id) REFERENCES classes(id));
    CREATE TABLE IF NOT EXISTS attendance_sessions (id INTEGER PRIMARY KEY AUTOINCREMENT, class_subject_id INTEGER, session_code TEXT, date DATE, start_time DATETIME, end_time DATETIME, status TEXT, close_at DATETIME, created_by INTEGER, created_at DATETIME, FOREIGN KEY(class_subject_id) REFERENCES class_subjects(id), FOREIGN KEY(created_by) REFERENCES teachers(id));
    CREATE TABLE IF NOT EXISTS Attendance (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id INTEGER, student_id INTEGER, status TEXT, note TEXT, marked_at DATETIME, updated_at DATETIME, updated_by INTEGER, UNIQUE(session_id, student_id), FOREIGN KEY(session_id) REFERENCES attendance_sessions(id), FOREIGN KEY(student_id) REFERENCES students(id));
    """
    cur.executescript(sql_tables)
    
    # TẠO USER CHUẨN (MẬT KHẨU: student123, teacher123, admin123)
    p_admin = hashlib.sha256('admin123'.encode()).hexdigest()
    p_teacher = hashlib.sha256('teacher123'.encode()).hexdigest()
    p_student = hashlib.sha256('student123'.encode()).hexdigest()

    cur.execute("INSERT INTO users (username, password_hash, full_name, email, role) VALUES (?,?,?,?,?)", ('admin', p_admin, 'Quản Trị Viên', 'admin@example.com', 'ADMIN'))
    cur.execute("INSERT INTO users (username, password_hash, full_name, email, role) VALUES (?,?,?,?,?)", ('t_giang', p_teacher, 'Thầy Giảng', 'teacher@example.com', 'TEACHER'))
    cur.execute("INSERT INTO users (username, password_hash, full_name, email, role) VALUES (?,?,?,?,?)", ('sv001', p_student, 'Nguyễn Văn A', 'sv001@example.com', 'STUDENT'))
    
    cur.execute("INSERT INTO teachers (user_id, teacher_code) VALUES (2, 'GV001')")
    cur.execute("INSERT INTO classes (class_code, class_name, homeroom_teacher_id) VALUES ('CNPM01', 'Lớp CNPM 01', 1)")
    cur.execute("INSERT INTO students (user_id, student_code, gender, class_id) VALUES (3, 'S001', 'M', 1)")
    
    cur.execute("INSERT INTO subjects (subject_code, subject_name) VALUES ('CNPM', 'Công Nghệ Phần Mềm')")
    cur.execute("INSERT INTO class_subjects (class_id, subject_id, teacher_id) VALUES (1, 1, 1)")
    
    # --- SỬA LỖI HIỂN THỊ (Ghi danh + Tạo Session) ---
    print(">>> Đang thực hiện Fix hiển thị (Enrollment + Session)...")
    # 1. Ghi danh (ID sinh viên = 1, Lớp = 1)
    cur.execute("INSERT INTO Enrollment (student_id, class_id, enrollment_date, status) VALUES (1, 1, '2025-01-01', 'Active')")
    
    # 2. Tạo Buổi học HÔM NAY (Múi giờ VN)
    today = datetime.now().strftime("%Y-%m-%d")
    now_vn = (datetime.utcnow() + timedelta(hours=7))
    today_str = now_vn.strftime("%Y-%m-%d")
    time_str = now_vn.strftime("%Y-%m-%d %H:%M:%S")

    # Kiểm tra xem đã có buổi học hôm nay chưa, nếu chưa thì tạo
    cur.execute("SELECT id FROM attendance_sessions WHERE date = ? AND class_subject_id = 1", (today_str,))
    if not cur.fetchone():
        session_code = f"FIX_AUTO_{today_str}"
        cur.execute(f"""
            INSERT INTO attendance_sessions (class_subject_id, session_code, date, status, created_by, start_time, created_at)
            VALUES (1, ?, ?, 'ACTIVE', 1, ?, ?)
        """, (session_code, today_str, time_str, time_str))
        print(f"    [OK] Đã tạo buổi học ngày {today_str}.")
    else:
        print(f"    [INFO] Buổi học ngày {today_str} đã tồn tại.")
    
    conn.commit()
    conn.close()
    print("    [OK] Dữ liệu đã được nạp chuẩn.")

if __name__ == "__main__":
    write_file(DATABASE_PY_PATH, db_content)
    write_file(GUI_PATH, gui_content)
    reset_db_to_vietnamese()
    
    print("-------------------------------------------------------")
    print("✅ ĐÃ GỘP FILE VÀ CÀI ĐẶT THÀNH CÔNG (Final Setup)!")
    print("-------------------------------------------------------")
    print("1. Mã nguồn: Đã cập nhật database.py và gui.py (Tiếng Việt).")
    print("2. Database: Đã reset sạch sẽ và nạp dữ liệu mẫu.")
    print("3. Tính năng: Đã tự động GHI DANH và TẠO BUỔI HỌC hôm nay.")
    print("-------------------------------------------------------")
    print("👉 Hãy chạy lại 'python3 main.py' ngay!")
    print("👉 Tài khoản Sinh Viên: sv001 / student123")
    print("-------------------------------------------------------")