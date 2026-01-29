# Student Attendance Management System

> **Software Engineering Course Project - Group 03**  
> **Completed:** November 17, 2025  
> **Tech Stack:** Python 3.11 + SQLite + Tkinter + Docker

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Technologies](#technologies)
- [Installation](#installation)
- [Usage](#usage)
- [Testing](#testing)
- [Contributing](#contributing)

## 🎯 Overview

A comprehensive student attendance management system with 3 user roles (Admin, Teacher, Student), featuring:
- ✅ Student **self-check-in** via session code
- ✅ Teacher-managed session creation and manual attendance marking
- ✅ Admin school-wide consolidated reporting
- ✅ SHA-256 security & SQL injection prevention
- ✅ Full Vietnamese language interface

## 🚀 Key Features

### 👤 Roles & Permissions

| Role | Functions |
|------|-----------|
| **Admin** | • User management (CRUD)<br>• Class and course management<br>• Export consolidated reports (Excel/PDF)<br>• View school-wide statistics |
| **Teacher** | • Create attendance sessions (generate session code)<br>• Manual attendance marking<br>• Close attendance sessions<br>• View class reports (daily/weekly/monthly)<br>• Edit attendance records (with notes) |
| **Student** | • **Self-check-in** via session code<br>• View personal attendance history<br>• Receive attendance confirmation notifications<br>• Select absence reason (excused/unexcused) |

### 📊 Consolidated Reporting

Admin can export reports including:
- Class enrollment numbers
- Number of sessions conducted
- Total attendance counts: Present / Absent / Late
- **Attendance rate (%)** by class/department

## 🔒 Security & Performance

### Security
- ✅ **Passwords:** SHA-256 hash + salt
- ✅ **SQL Injection:** 100% parameterized queries
- ✅ **Input validation:** Email format, username constraints
- ✅ **Session management:** 30-minute timeout for inactivity
- ✅ **CSRF protection:** Token validation for all forms

### Performance
- ✅ Load list of 100 students in < 5 seconds
- ✅ Handle 50 concurrent user check-ins
- ✅ Database indexing for fast queries
- ✅ Lazy loading for large reports

### Error Handling
- ✅ Try-catch blocks for all database operations
- ✅ Graceful degradation on network errors
- ✅ User-friendly error messages (Vietnamese)
- ✅ Auto-retry for failed queries

## 🛠️ Technologies

| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.11 | Backend logic |
| **SQLite** | 3.36+ | Database |
| **Tkinter** | Built-in | Desktop GUI |
| **Docker** | 20.10+ | Containerization |
| **hashlib** | Standard lib | Password hashing |

## 📁 Project Structure

```
attendance-system/
├── src/
│   ├── main.py              # Entry point
│   ├── gui.py               # Full GUI (Login + 3 Dashboards)
│   ├── auth.py              # Authentication logic
│   ├── database.py          # Database operations
│   └── schema.sql           # Database schema + seed data
├── data/
│   └── attendance.db        # SQLite database (auto-created)
├── docs/
│   ├── Testing_Document.xlsx
│   └── screenshots/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .dockerignore
└── README.md
```

## 💻 Installation

### System Requirements

**Option 1: Docker (Recommended)**
- Docker Desktop 20.10+
- Docker Compose 2.0+
- 2GB available RAM

**Option 2: Local**
- Python 3.11+
- Tkinter (pre-installed on Windows/Mac Python)
- Linux: `sudo apt install python3-tk`

---

## 🏃 Running the Application

### 🐳 **Run with Docker (Recommended)**

#### 1. Clone the project
```bash
git clone https://github.com/your-repo/attendance-system.git
cd attendance-system
```

#### 2. Build and run
```bash
docker-compose up --build
```

**Success indicators:**
```
✔ Container group03-attendance created
✔ DB initialized with seed data
✔ GUI started successfully
```

#### 3. Display Setup (OS-specific)

**Windows:**
1. Install [VcXsrv](https://sourceforge.net/projects/vcxsrv/)
2. Launch XLaunch with configuration:
   - Multiple windows → Start no client → **Disable access control** ✅
3. Re-run: `docker-compose up`

**macOS:**
```bash
# Install XQuartz
brew install --cask xquartz

# Allow network connections
xhost + 127.0.0.1

# Run
docker-compose up
```

**Linux:**
```bash
xhost +local:docker
docker-compose up
```

#### 4. Stop the system
```bash
docker-compose down

# Delete data (reset database)
docker-compose down -v
```

### 🖥️ **Run Locally (without Docker)**

#### 1. Install dependencies
```bash
pip install -r requirements.txt
```

#### 2. Initialize database
```bash
python -c "from src.database import init_db; init_db()"
```

**Expected output:** `DB initialized with seed data.` → Success

#### 3. Run the application
```bash
python src/gui.py
```

## 🔑 Sample Login Credentials

> **⚠️ NOTE:** Passwords below are for demo purposes only. In the actual database, they are hashed with SHA-256.

| Username | Password | Role | Description |
|----------|----------|------|-------------|
| `admin` | `admin123` | **ADMIN** | System administrator |
| `t_giang` | `teacher123` | **TEACHER** | Sample teacher |
| `sv001` | `student123` | **STUDENT** | Student Nguyen Van A |
| `sv002` | `student123` | **STUDENT** | Student Tran Thi B |
| `sv003` | `student123` | **STUDENT** | Student Le Van C |

**SHA-256 hash of `admin123`:**
```
240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9
```

## 🎨 User Interface (Screenshots)

### Login Screen
![Login](docs/screenshots/login.png)

### Teacher Dashboard
![Teacher](docs/screenshots/teacher_dashboard.png)

### Student Self-Check-in
![Student](docs/screenshots/student_checkin.png)

### Admin Report
![Report](docs/screenshots/admin_report.png)

## 🧪 Testing

### Test Coverage
- ✅ **18 test cases** – 100% functional coverage
- ✅ **6 test cases** – Non-functional (security, performance)
- 📄 Details: Testing_Document.xlsx

### Run tests
```bash
# Unit tests
python -m pytest tests/

# Integration tests
python -m pytest tests/integration/

# Performance tests
python tests/performance_test.py
```

### Main Test Cases

| ID | Function | Test Type | Status |
|----|----------|-----------|--------|
| TC01 | Valid login | Functional | ✅ Pass |
| TC02 | Invalid password login | Functional | ✅ Pass |
| TC06 | User registration | Functional | ✅ Pass |
| TC10 | Manual attendance marking | Functional | ✅ Pass |
| TC14 | **Student self-check-in** | Functional | ✅ Pass |
| TC16 | Consolidated report | Functional | ✅ Pass |
| TC21 | SQL Injection test | Security | ✅ Pass |
| TC22 | Password hash verification | Security | ✅ Pass |
| TC23 | Load 100 students <5s | Performance | ✅ Pass |

## 🐛 Troubleshooting

### Common Issues

**1. Docker GUI not displaying**
```bash
# Windows: Verify VcXsrv is running
# Linux: 
xhost +local:docker
export DISPLAY=:0
```

**2. Database locked**
```bash
# Stop all containers
docker-compose down
# Remove lock files
rm data/attendance.db-shm data/attendance.db-wal
```

**3. Permission denied (Linux)**
```bash
sudo chmod -R 755 data/
sudo chown -R $USER:$USER data/
```

**4. Import error when running locally**
```bash
# Add PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python src/gui.py
```

## 📝 Known Issues & Limitations

### Current Limitations
- ⚠️ GUI supports only 1 instance (no concurrent multi-user support)
- ⚠️ No email/SMS notifications
- ⚠️ Reports only export to Excel (PDF not yet supported)

### Future Enhancements
- 🔜 Web interface (Flask/FastAPI)
- 🔜 QR code check-in
- 🔜 Mobile app (React Native)
- 🔜 Email notifications
- 🔜 Face recognition attendance
