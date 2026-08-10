import sqlite3
from datetime import datetime
from config import Config

def get_db():
    conn = sqlite3.connect(Config.DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()

    # ---------- Admin Table ----------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS admin (
            admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'admin'
        )
    """)

    # ---------- Users Table ----------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            department TEXT,
            awareness_score INTEGER DEFAULT 0,
            risk_level TEXT DEFAULT 'Medium',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ---------- Campaign Table ----------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS campaign (
            campaign_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            scenario TEXT,
            created_by INTEGER,
            status TEXT DEFAULT 'active',
            date_created TEXT DEFAULT CURRENT_TIMESTAMP,
            scheduled_date TEXT,
            template_id INTEGER
        )
    """)

    # ---------- Simulation_Response Table ----------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS simulation_response (
            response_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            campaign_id INTEGER,
            email_opened INTEGER DEFAULT 0,
            link_clicked INTEGER DEFAULT 0,
            reported INTEGER DEFAULT 0,
            page_visited INTEGER DEFAULT 0,
            quiz_completed INTEGER DEFAULT 0,
            score INTEGER DEFAULT 0,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ---------- Training Table ----------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS training (
            training_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT,
            category TEXT
        )
    """)

    # ---------- Quiz_Result Table ----------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS quiz_result (
            result_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            quiz_score INTEGER,
            completion_date TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ---------- Supporting: Email Template ----------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS email_template (
            template_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            subject TEXT,
            sender TEXT,
            content TEXT,
            suspicious TEXT,
            awareness TEXT
        )
    """)

# ---------- Supporting: Training Progress ----------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS training_progress (
            progress_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            training_id INTEGER,
            completed_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, training_id)
        )
    """)

    # ---------- Supporting: Certificates ----------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS certificates (
            certificate_id TEXT PRIMARY KEY,
            user_id INTEGER,
            issued_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id)
        )
    """)

    # ---------- Supporting: Quiz Questions ----------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS quiz_questions (
            question_id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT,
            options TEXT,
            correct_index INTEGER,
            category TEXT,
            difficulty TEXT DEFAULT 'Medium',
            active INTEGER DEFAULT 1,
            explanation TEXT
        )
    """)

    # Migration for existing databases: add new columns if missing
    cols = [r[1] for r in cur.execute("PRAGMA table_info(quiz_questions)").fetchall()]
    if "difficulty" not in cols:
        cur.execute("ALTER TABLE quiz_questions ADD COLUMN difficulty TEXT DEFAULT 'Medium'")
    if "active" not in cols:
        cur.execute("ALTER TABLE quiz_questions ADD COLUMN active INTEGER DEFAULT 1")
    if "explanation" not in cols:
        cur.execute("ALTER TABLE quiz_questions ADD COLUMN explanation TEXT")

    # ---------- Supporting: Notifications ----------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT,
            message TEXT,
            type TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ---------- Supporting: User Activity Log ----------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS activity_log (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT,
            campaign_id INTEGER,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
