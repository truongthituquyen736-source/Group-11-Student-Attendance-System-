-- schema.sql
PRAGMA foreign_keys = ON;

-- 1. USERS
CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    full_name       TEXT NOT NULL,
    email           TEXT NOT NULL UNIQUE,
    role            TEXT NOT NULL CHECK (role IN ('ADMIN','TEACHER','STUDENT')),
    is_active       INTEGER NOT NULL DEFAULT 1,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 2. PASSWORD RESETS
CREATE TABLE IF NOT EXISTS password_resets (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    token           TEXT NOT NULL UNIQUE,
    expires_at      DATETIME NOT NULL,
    used            INTEGER NOT NULL DEFAULT 0,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 3. TEACHERS
CREATE TABLE IF NOT EXISTS teachers (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL UNIQUE,
    teacher_code    TEXT NOT NULL UNIQUE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 4. LECTURER
CREATE TABLE IF NOT EXISTS Lecturer (
    LecturerID      INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER UNIQUE,
    Name            VARCHAR(100),
    Email           VARCHAR(100),
    Phone           VARCHAR(20),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 5. CLASSES
CREATE TABLE IF NOT EXISTS classes (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    class_code              TEXT NOT NULL UNIQUE,
    class_name              TEXT NOT NULL,
    homeroom_teacher_id     INTEGER,
    is_active               INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (homeroom_teacher_id) REFERENCES teachers(id)
);

-- 6. COURSE
CREATE TABLE IF NOT EXISTS Course (
    CourseID        INTEGER PRIMARY KEY AUTOINCREMENT,
    CourseName      VARCHAR(100),
    Credit          INT
);

-- 7. STUDENTS
CREATE TABLE IF NOT EXISTS students (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL UNIQUE,
    student_code    TEXT NOT NULL UNIQUE,
    gender          TEXT CHECK (gender IN ('M','F','O')),
    class_id        INTEGER,
    note            TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (class_id) REFERENCES classes(id)
);

-- 8. SUBJECTS
CREATE TABLE IF NOT EXISTS subjects (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_code    TEXT NOT NULL UNIQUE,
    subject_name    TEXT NOT NULL
);

-- 9. CLASS_SUBJECTS
CREATE TABLE IF NOT EXISTS class_subjects (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    class_id        INTEGER NOT NULL,
    subject_id      INTEGER NOT NULL,
    teacher_id      INTEGER NOT NULL,
    UNIQUE (class_id, subject_id),
    FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
    FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE
);

-- 10. ENROLLMENT
CREATE TABLE IF NOT EXISTS Enrollment (
    EnrollmentID    INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id      INTEGER,
    class_id        INTEGER,
    enrollment_date DATE,
    status          TEXT CHECK (status IN ('Active', 'Canceled')),
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (class_id) REFERENCES classes(id)
);

-- 11. ATTENDANCE_SESSIONS
CREATE TABLE IF NOT EXISTS attendance_sessions (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    class_subject_id    INTEGER NOT NULL,
    session_code        TEXT NOT NULL UNIQUE,
    date                DATE NOT NULL,
    start_time          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    end_time            DATETIME,
    status              TEXT NOT NULL CHECK (status IN ('ACTIVE','CLOSED')),
    close_at            DATETIME,
    created_by          INTEGER NOT NULL,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (class_subject_id) REFERENCES class_subjects(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES teachers(id)
);

-- 12. ATTENDANCE_RECORDS
CREATE TABLE IF NOT EXISTS Attendance (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      INTEGER NOT NULL,
    student_id      INTEGER NOT NULL,
    status          TEXT NOT NULL CHECK (status IN ('PRESENT','ABSENT','ABSENT_EXCUSED','LATE')),
    note            TEXT,
    marked_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME,
    updated_by      INTEGER,
    UNIQUE (session_id, student_id),
    FOREIGN KEY (session_id) REFERENCES attendance_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (updated_by) REFERENCES teachers(id)
);

-- 13. SEED DATA (ĐÃ MÃ HÓA PASSWORD)
INSERT INTO users (username, password_hash, full_name, email, role) VALUES
    ('admin',       '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9',     'Quản trị viên',        'admin@example.com',    'ADMIN'),
    ('t_giang',     '01a34a810b10e3092289f6608935c106579998495034c5464195b060d4b85771',   'Thầy Giảng',           'teacher@example.com',  'TEACHER'),
    ('sv001',       '5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5',   'Nguyễn Văn A',         'sv001@example.com',    'STUDENT'),
    ('sv002',       '5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5',   'Trần Thị B',           'sv002@example.com',    'STUDENT'),
    ('sv003',       '5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5',   'Lê Văn C',             'sv003@example.com',    'STUDENT');

INSERT INTO teachers (user_id, teacher_code) VALUES (2, 'GV001');
INSERT INTO Lecturer (user_id, Name, Email, Phone) VALUES (2, 'Thầy Giảng', 'teacher@example.com', '0123456789');

INSERT INTO classes (class_code, class_name, homeroom_teacher_id) VALUES
    ('CNPM01', 'Lớp CNPM 01', 1);

INSERT INTO students (user_id, student_code, gender, class_id, note) VALUES
    (3, 'S001', 'M', 1, NULL),
    (4, 'S002', 'F', 1, NULL),
    (5, 'S003', 'M', 1, NULL);

INSERT INTO Course (CourseName, Credit) VALUES ('Công nghệ phần mềm', 3);
INSERT INTO subjects (subject_code, subject_name) VALUES ('CNPM', 'Công nghệ phần mềm');

INSERT INTO class_subjects (class_id, subject_id, teacher_id) VALUES (1, 1, 1);

INSERT INTO Enrollment (student_id, class_id, enrollment_date, status) VALUES
    (1, 1, '2025-09-01', 'Active'),
    (2, 1, '2025-09-01', 'Active'),
    (3, 1, '2025-09-01', 'Active');

INSERT INTO attendance_sessions (class_subject_id, session_code, date, status, created_by)
VALUES (1, 'CNPM01_2025-11-16', '2025-11-16', 'ACTIVE', 1);

INSERT INTO Attendance (session_id, student_id, status, note) VALUES
    (1, 1, 'PRESENT', NULL),
    (1, 2, 'PRESENT', NULL),
    (1, 3, 'ABSENT', 'Ốm');