"""Seed script - populates demo data for the CyberSec Dashboard.

Run: python seed.py
"""
import sqlite3
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from auth import hash_password
from models import init_db

init_db()

conn = sqlite3.connect(Config.DATABASE)
cur = conn.cursor()

def table_count(table):
    return cur.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

# ------------------------- ADMIN -------------------------
if table_count("admin") == 0:
    cur.execute(
        "INSERT INTO admin (name, email, password_hash, role) VALUES (?,?,?,?)",
        ("Security Admin", "admin@cybersec.com", hash_password("admin123"), "admin")
    )
    print("+ Admin created: admin@cybersec.com / admin123")

# ------------------------- USERS -------------------------
if table_count("users") == 0:
    demo_users = [
        ("Alice Johnson", "alice@example.com", "CompSci", 92, "Low"),
        ("Bob Smith", "bob@example.com", "Business", 45, "High"),
        ("Carol White", "carol@example.com", "Engineering", 78, "Medium"),
        ("David Brown", "david@example.com", "CompSci", 35, "High"),
        ("Eve Davis", "eve@example.com", "Marketing", 85, "Low"),
        ("Frank Miller", "frank@example.com", "Engineering", 60, "Medium"),
        ("Grace Wilson", "grace@example.com", "HR", 95, "Low"),
        ("Henry Moore", "henry@example.com", "Business", 25, "High"),
    ]
    for u in demo_users:
        cur.execute(
            "INSERT INTO users (name, email, password_hash, department, awareness_score, risk_level) VALUES (?,?,?,?,?,?)",
            (u[0], u[1], hash_password("user123"), u[2], u[3], u[4])
        )
    print(f"+ {len(demo_users)} users created (password: user123)")

# ------------------------- TRAINING -------------------------
if table_count("training") == 0:
    training = [
        ("How Phishing Works", "Phishing is a cyberattack where attackers impersonate trusted entities to steal credentials, money, or data. Emails often create urgency or fear to trigger quick action.", "Awareness"),
        ("How to Identify Fake Emails", "Check the sender address, look for generic greetings, grammar errors, mismatched URLs, and unexpected attachments or links. Never act under time pressure.", "Detection"),
        ("Suspicious URL Detection", "Hover over links to preview the true destination. Look for misspelled domains (e.g., amaz0n.com), extra subdomains, or URL shorteners that hide the real address.", "Detection"),
        ("Social Engineering Methods", "Attackers exploit human psychology: authority, urgency, scarcity, and trust. Verify unusual requests through a second channel before acting.", "Security"),
        ("Password Security Practices", "Use long, unique passwords, a password manager, and never reuse credentials across sites. Change passwords immediately if a breach is suspected.", "Security"),
        ("Multi-Factor Authentication", "MFA adds a second verification step (SMS, authenticator app, biometrics). It blocks most automated account takeover attacks even when passwords leak.", "Security"),
    ]
    for t in training:
        cur.execute("INSERT INTO training (title, content, category) VALUES (?,?,?)", t)
    print(f"+ {len(training)} training modules created")

# ------------------------- TEMPLATES -------------------------
if table_count("email_template") == 0:
    templates = [
        ("Fake Password Expiry", "IMPORTANT: Your password will expire in 24 hours",
         "no-reply@secure-verify.net",
         "Dear user, Your account password is about to expire. Click the link below to keep your current password and avoid account suspension. <a href='http://secure-verify.net/reset'>Reset Password</a>",
         "Unknown sender domain, urgent language, generic greeting, suspicious link destination",
         "Legitimate companies never ask you to click a link to keep a password. Always navigate directly to the official site."),
        ("Fake Account Verification", "Action Required: Verify Your Account Now",
         "support@acc-verify.org",
         "Dear customer, We detected unusual activity on your account. Verify your identity immediately or your account will be suspended. <a href='http://acc-verify.org/verify'>Verify Account</a>",
         "Threat of suspension, fake domain, mismatched sender, urgency",
         "Verify by contacting official support. Never click links in unsolicited verification emails."),
        ("Fake Security Alert", "Security Alert: Unusual Login Attempt",
         "security@alert-notify.com",
         "A new device tried to access your account from an unknown location. If this wasn't you, log in to secure your account: <a href='http://alert-notify.com/login'>Secure Account</a>",
         "Unexpected alert, unknown domain, asks to log in via link",
         "Real security alerts come from the service you use. Check the sender domain and log in through the official app."),
        ("Fake Reward Notification", "Congratulations! You've Won a $500 Gift Card",
         "prizes@reward-center.com",
         "You have been selected to receive a $500 gift card! Claim your reward within 24 hours by entering your details. <a href='http://reward-center.com/claim'>Claim Reward</a>",
         "Too-good-to-be-true prize, limited time, asks for personal details",
         "Unsolicited prizes are a common phishing lure. Legitimate rewards never require you to pay or share credentials."),
    ]
    for t in templates:
        cur.execute("INSERT INTO email_template (name, subject, sender, content, suspicious, awareness) VALUES (?,?,?,?,?,?)", t)
    print(f"+ {len(templates)} email templates created")

# ------------------------- CAMPAIGNS -------------------------
if table_count("campaign") == 0:
    campaigns = [
        ("Q1 Phishing Simulation", "Quarterly password-expiry phishing drill", "Fake password expiry notification", 1, "active", "2025-01-15", 1),
        ("Account Verification Drill", "Account verification simulation for new hires", "Fake account verification email", 1, "active", "2025-02-01", 2),
        ("Security Alert Test", "Test user response to security alert emails", "Fake security alert message", 1, "inactive", "2025-02-20", 3),
        ("Reward Scam Simulation", "Reward-based phishing awareness campaign", "Fake reward notification", 1, "active", "2025-03-05", 4),
    ]
    for c in campaigns:
        cur.execute(
            "INSERT INTO campaign (title, description, scenario, created_by, status, scheduled_date, template_id) VALUES (?,?,?,?,?,?,?)",
            c
        )
    print(f"+ {len(campaigns)} campaigns created")

# ------------------------- SIMULATION RESPONSES -------------------------
if table_count("simulation_response") == 0:
    responses = [
        # user_id, campaign_id, opened, clicked, reported, page, quiz, score
        (1, 1, 1, 0, 1, 1, 1, 100),
        (2, 1, 1, 1, 0, 1, 0, 30),
        (3, 1, 1, 0, 1, 1, 1, 100),
        (4, 1, 1, 1, 0, 0, 0, 30),
        (5, 2, 1, 0, 1, 1, 1, 100),
        (6, 2, 1, 1, 0, 1, 1, 30),
        (7, 2, 1, 0, 1, 1, 1, 100),
        (8, 2, 1, 1, 0, 0, 0, 30),
        (1, 3, 1, 0, 1, 1, 1, 100),
        (2, 3, 1, 1, 0, 1, 0, 30),
        (3, 3, 1, 0, 1, 1, 1, 100),
        (5, 3, 1, 0, 1, 1, 1, 100),
        (6, 3, 1, 1, 0, 0, 0, 30),
        (7, 3, 1, 0, 1, 1, 1, 100),
        (4, 4, 1, 1, 0, 1, 0, 30),
        (8, 4, 1, 1, 0, 0, 0, 30),
        (3, 4, 1, 0, 1, 1, 1, 100),
        (5, 4, 1, 0, 1, 1, 1, 100),
    ]
    for r in responses:
        cur.execute(
            "INSERT INTO simulation_response (user_id, campaign_id, email_opened, link_clicked, reported, page_visited, quiz_completed, score) VALUES (?,?,?,?,?,?,?,?)",
            r
        )
    print(f"+ {len(responses)} simulation responses created")

# ------------------------- QUIZ QUESTIONS -------------------------
if table_count("quiz_questions") == 0:
    questions = [
        # question, options, correct_index, category, difficulty, active, explanation
        ("You receive an urgent email asking you to verify your account. What should you do?",
         '["Click immediately","Check sender identity","Share password","Ignore security warnings"]', 1, "Email Analysis", "Easy", 1,
         "Always verify the sender and navigate to the official site directly instead of clicking links."),
        ("An email offers a free gift card if you enter your bank details. This is likely...",
         '["A legitimate reward","A phishing scam","An official promotion","A harmless survey"]', 1, "Scenario", "Easy", 1,
         "Unsolicited prizes asking for bank details are classic phishing lures."),
        ("What does 'hovering over a link' before clicking help you see?",
         '["The email sender","The true destination URL","The email subject","The recipient count"]', 1, "URL Detection", "Easy", 1,
         "Hovering reveals the real URL, helping you spot misspelled or fake domains."),
        ("Which of these sender addresses is most suspicious?",
         '["support@microsoft.com","support@micros0ft-security.com","help@yourbank.com","no-reply@paypal.com"]', 1, "Email Analysis", "Medium", 1,
         "Typosquatted domains like micros0ft-security.com are a red flag for phishing."),
        ("You receive a call from 'IT' asking for your password to fix an issue. You should...",
         '["Give the password","Ask for ID and call back the official number","Verify your email","Ignore and disconnect"]', 1, "Social Engineering", "Medium", 1,
         "Legitimate IT staff will never ask for your password. Verify through official channels."),
        ("What is the best defense against account takeover?",
         '["Using the same password everywhere","Multi-factor authentication","Sharing passwords with IT","Writing passwords on sticky notes"]', 1, "MFA", "Medium", 1,
         "MFA adds a second verification step that blocks most unauthorized access."),
        ("A friend's email asks for gift cards urgently. What is a safe action?",
         '["Send gift cards","Call your friend to verify","Reply with your card number","Click the link in the email"]', 1, "Scenario", "Hard", 1,
         "Urgent requests for money are often social engineering. Verify via a separate channel."),
        ("Which element is a common phishing indicator?",
         '["Professional greeting with your name","Grammar errors and urgent threats","Official company logo","Correct sender domain"]', 1, "Detection", "Medium", 1,
         "Grammar errors, threats, and urgency are common signs of a phishing email."),
        ("A link in an email points to http://secure-login-bank.com. What is this?",
         '["A secure official link","A suspicious fake domain","A safe bookmark","An official shortcut"]', 1, "URL Detection", "Medium", 1,
         "Unknown subdomains and unusual top-level domains are strong phishing indicators."),
        ("You receive a text claiming your package is held and asks for a fee. This is...",
         '["A legitimate delivery notice","Smishing (SMS phishing)","An official courier request","A harmless ad"]', 1, "Scenario", "Easy", 0,
         "Text-based phishing (smishing) pressures you to pay or share info urgently."),
    ]
    for q in questions:
        cur.execute(
            "INSERT INTO quiz_questions (question, options, correct_index, category, difficulty, active, explanation) VALUES (?,?,?,?,?,?,?)",
            q
        )
    print(f"+ {len(questions)} quiz questions created")
else:
    # Update existing rows with difficulty/active/explanation defaults if missing
    quiz_cols = [r[1] for r in cur.execute("PRAGMA table_info(quiz_questions)").fetchall()]
    if "difficulty" not in quiz_cols:
        cur.execute("ALTER TABLE quiz_questions ADD COLUMN difficulty TEXT DEFAULT 'Medium'")
    if "active" not in quiz_cols:
        cur.execute("ALTER TABLE quiz_questions ADD COLUMN active INTEGER DEFAULT 1")
    if "explanation" not in quiz_cols:
        cur.execute("ALTER TABLE quiz_questions ADD COLUMN explanation TEXT")
    cur.execute("UPDATE quiz_questions SET difficulty='Medium' WHERE difficulty IS NULL OR difficulty=''")
    cur.execute("UPDATE quiz_questions SET active=1 WHERE active IS NULL")
    print(f"+ Updating existing quiz questions with new fields")

# ------------------------- NOTIFICATIONS -------------------------
if table_count("notifications") == 0:
    notes = [
        (None, "New Training Available", "New module: 'Suspicious URL Detection' is now available in your training center.", "training"),
        (None, "Simulation Announcement", "A new phishing simulation campaign has been scheduled. Stay alert!", "simulation"),
        (None, "Security Tip", "Always verify the sender's full email address before clicking links.", "tip"),
        (None, "Security Alert", "Beware of calls asking for your password. Your IT team will never ask for it.", "alert"),
    ]
    for n in notes:
        cur.execute("INSERT INTO notifications (user_id, title, message, type) VALUES (?,?,?,?)", n)
    print(f"+ {len(notes)} notifications created")

# ------------------------- ACTIVITY LOG -------------------------
if table_count("activity_log") == 0:
    logs = [
        (1, "email_opened", 1), (1, "reported", 1), (1, "quiz_completed", 1),
        (2, "email_opened", 1), (2, "link_clicked", 1),
        (3, "email_opened", 1), (3, "reported", 1),
        (5, "email_opened", 2), (5, "reported", 2),
        (7, "email_opened", 2), (7, "reported", 2),
    ]
    for l in logs:
        cur.execute("INSERT INTO activity_log (user_id, action, campaign_id) VALUES (?,?,?)", l)
    print(f"+ {len(logs)} activity logs created")

conn.commit()
conn.close()
print("\n✔ Seed complete. Database: cybersec.db")
print("  Admin login : admin@cybersec.com / admin123")
print("  User login  : alice@example.com / user123")

