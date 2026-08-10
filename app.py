import json
import io
import csv
from flask import Flask, request, jsonify, send_from_directory
from config import Config
from models import init_db, get_db, now
from auth import token_required, admin_required, create_token, hash_password, verify_password

app = Flask(__name__, static_folder=None)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

init_db()

# ------------------------------------------------------------------
# Static frontend serving
# ------------------------------------------------------------------
@app.route("/")
def index():
    return send_from_directory(Config.FRONTEND_DIR, "login.html")

@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(Config.FRONTEND_DIR, path)

# ------------------------------------------------------------------
# AUTH
# ------------------------------------------------------------------
@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    admin = get_db().execute("SELECT * FROM admin WHERE email=?", (email,)).fetchone()
    if admin and verify_password(password, admin["password_hash"]):
        token = create_token(admin["admin_id"], "admin")
        return jsonify({"token": token, "role": "admin", "name": admin["name"]})

    user = get_db().execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    if user and verify_password(password, user["password_hash"]):
        token = create_token(user["user_id"], "user")
        return jsonify({"token": token, "role": "user", "name": user["name"], "user_id": user["user_id"]})

    return jsonify({"error": "Invalid credentials"}), 401

@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json()
    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    department = data.get("department", "").strip()

    if not name or not email or not password:
        return jsonify({"error": "All fields required"}), 400

    conn = get_db()
    exists = conn.execute("SELECT user_id FROM users WHERE email=?", (email,)).fetchone()
    if exists:
        return jsonify({"error": "Email already registered"}), 400

    conn.execute(
        "INSERT INTO users (name, email, password_hash, department, awareness_score, risk_level) VALUES (?,?,?,?,?,?)",
        (name, email, hash_password(password), department, 0, "Medium")
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "User registered successfully"}), 201

@app.route("/api/auth/me", methods=["GET"])
@token_required
def me():
    conn = get_db()
    if request.user_role == "admin":
        row = conn.execute("SELECT admin_id, name, email, role FROM admin WHERE admin_id=?", (request.user_id,)).fetchone()
    else:
        row = conn.execute("SELECT user_id, name, email, department, awareness_score, risk_level FROM users WHERE user_id=?", (request.user_id,)).fetchone()
    conn.close()
    return jsonify(dict(row) if row else {})

# ------------------------------------------------------------------
# DASHBOARD OVERVIEW (ADMIN)
# ------------------------------------------------------------------
@app.route("/api/admin/overview", methods=["GET"])
@admin_required
def admin_overview():
    conn = get_db()
    total_users = conn.execute("SELECT COUNT(*) c FROM users").fetchone()["c"]
    total_campaigns = conn.execute("SELECT COUNT(*) c FROM campaign").fetchone()["c"]
    total_emails = conn.execute("SELECT COUNT(*) c FROM simulation_response").fetchone()["c"]
    total_responses = conn.execute("SELECT COUNT(*) c FROM simulation_response WHERE link_clicked=1 OR reported=1 OR email_opened=1").fetchone()["c"]
    avg_score = conn.execute("SELECT AVG(awareness_score) a FROM users").fetchone()["a"] or 0
    high_risk = conn.execute("SELECT COUNT(*) c FROM users WHERE risk_level='High'").fetchone()["c"]

    # awareness graph data over time
    rows = conn.execute("""
        SELECT date(timestamp) d, AVG(score) s FROM simulation_response GROUP BY d ORDER BY d
    """).fetchall()
    awareness_trend = [{"date": r["d"], "score": round(r["s"], 1)} for r in rows]

    # risk distribution
    risk_dist = {
        "low": conn.execute("SELECT COUNT(*) c FROM users WHERE risk_level='Low'").fetchone()["c"],
        "medium": conn.execute("SELECT COUNT(*) c FROM users WHERE risk_level='Medium'").fetchone()["c"],
        "high": conn.execute("SELECT COUNT(*) c FROM users WHERE risk_level='High'").fetchone()["c"],
    }

    # responses by status for simulation stats
    opened = conn.execute("SELECT COUNT(*) c FROM simulation_response WHERE email_opened=1").fetchone()["c"]
    clicked = conn.execute("SELECT COUNT(*) c FROM simulation_response WHERE link_clicked=1").fetchone()["c"]
    reported = conn.execute("SELECT COUNT(*) c FROM simulation_response WHERE reported=1").fetchone()["c"]

    # monthly activity
    monthly = conn.execute("""
        SELECT strftime('%Y-%m', timestamp) m, COUNT(*) c FROM simulation_response GROUP BY m ORDER BY m
    """).fetchall()
    monthly_activity = [{"month": r["m"], "count": r["c"]} for r in monthly]

    # recent activities
    recent = conn.execute("""
        SELECT action, timestamp FROM activity_log ORDER BY log_id DESC LIMIT 8
    """).fetchall()

    conn.close()
    return jsonify({
        "total_users": total_users,
        "total_campaigns": total_campaigns,
        "total_emails": total_emails,
        "total_responses": total_responses,
        "awareness_percentage": round(avg_score, 1),
        "high_risk_users": high_risk,
        "awareness_trend": awareness_trend,
        "risk_distribution": risk_dist,
        "simulation_stats": {"opened": opened, "clicked": clicked, "reported": reported},
        "monthly_activity": monthly_activity,
        "recent_activities": [dict(r) for r in recent],
    })

# ------------------------------------------------------------------
# USER MANAGEMENT
# ------------------------------------------------------------------
@app.route("/api/admin/users", methods=["GET"])
@admin_required
def admin_users():
    conn = get_db()
    rows = conn.execute("SELECT user_id, name, email, department, awareness_score, risk_level, created_at FROM users ORDER BY user_id").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/admin/users", methods=["POST"])
@admin_required
def admin_add_user():
    data = request.get_json()
    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "password123")
    department = data.get("department", "").strip()
    role = data.get("role", "user")

    if not name or not email:
        return jsonify({"error": "Name and email required"}), 400

    conn = get_db()
    exists = conn.execute("SELECT user_id FROM users WHERE email=?", (email,)).fetchone()
    if exists:
        return jsonify({"error": "Email already exists"}), 400

    conn.execute(
        "INSERT INTO users (name, email, password_hash, department, awareness_score, risk_level) VALUES (?,?,?,?,?,?)",
        (name, email, hash_password(password), department, 0, "Medium")
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "User added"}), 201

@app.route("/api/admin/users/<int:user_id>", methods=["PUT"])
@admin_required
def admin_update_user(user_id):
    data = request.get_json()
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
    if not user:
        return jsonify({"error": "User not found"}), 404

    conn.execute(
        "UPDATE users SET name=?, department=?, awareness_score=?, risk_level=? WHERE user_id=?",
        (
            data.get("name", user["name"]),
            data.get("department", user["department"]),
            data.get("awareness_score", user["awareness_score"]),
            data.get("risk_level", user["risk_level"]),
            user_id,
        )
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "User updated"})

@app.route("/api/admin/users/<int:user_id>", methods=["DELETE"])
@admin_required
def admin_delete_user(user_id):
    conn = get_db()
    conn.execute("DELETE FROM users WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "User deleted"})

@app.route("/api/admin/users/import", methods=["POST"])
@admin_required
def admin_import_users():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file uploaded"}), 400
    content = file.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(content))
    conn = get_db()
    added = 0
    skipped = 0
    for row in reader:
        email = (row.get("email") or "").strip().lower()
        name = (row.get("name") or "").strip()
        department = (row.get("department") or "").strip()
        if not email or not name:
            skipped += 1
            continue
        exists = conn.execute("SELECT user_id FROM users WHERE email=?", (email,)).fetchone()
        if exists:
            skipped += 1
            continue
        conn.execute(
            "INSERT INTO users (name, email, password_hash, department, awareness_score, risk_level) VALUES (?,?,?,?,?,?)",
            (name, email, hash_password("password123"), department, 0, "Medium")
        )
        added += 1
    conn.commit()
    conn.close()
    return jsonify({"message": f"Imported {added} users, skipped {skipped}"})

# ------------------------------------------------------------------
# CAMPAIGNS
# ------------------------------------------------------------------
@app.route("/api/admin/campaigns", methods=["GET"])
@admin_required
def admin_campaigns():
    conn = get_db()
    rows = conn.execute("SELECT * FROM campaign ORDER BY campaign_id DESC").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/admin/campaigns", methods=["POST"])
@admin_required
def admin_create_campaign():
    data = request.get_json()
    conn = get_db()
    conn.execute(
        "INSERT INTO campaign (title, description, scenario, created_by, status, scheduled_date, template_id) VALUES (?,?,?,?,?,?,?)",
        (
            data.get("title", ""),
            data.get("description", ""),
            data.get("scenario", ""),
            request.user_id,
            data.get("status", "active"),
            data.get("scheduled_date"),
            data.get("template_id"),
        )
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Campaign created"}), 201

@app.route("/api/admin/campaigns/<int:campaign_id>", methods=["PUT"])
@admin_required
def admin_update_campaign(campaign_id):
    data = request.get_json()
    conn = get_db()
    camp = conn.execute("SELECT * FROM campaign WHERE campaign_id=?", (campaign_id,)).fetchone()
    if not camp:
        return jsonify({"error": "Campaign not found"}), 404
    conn.execute(
        "UPDATE campaign SET title=?, description=?, scenario=?, status=?, scheduled_date=?, template_id=? WHERE campaign_id=?",
        (
            data.get("title", camp["title"]),
            data.get("description", camp["description"]),
            data.get("scenario", camp["scenario"]),
            data.get("status", camp["status"]),
            data.get("scheduled_date", camp["scheduled_date"]),
            data.get("template_id", camp["template_id"]),
            campaign_id,
        )
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Campaign updated"})

@app.route("/api/admin/campaigns/<int:campaign_id>", methods=["DELETE"])
@admin_required
def admin_delete_campaign(campaign_id):
    conn = get_db()
    conn.execute("DELETE FROM campaign WHERE campaign_id=?", (campaign_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Campaign deleted"})

# ------------------------------------------------------------------
# EMAIL TEMPLATES
# ------------------------------------------------------------------
@app.route("/api/admin/templates", methods=["GET"])
@admin_required
def admin_templates():
    conn = get_db()
    rows = conn.execute("SELECT * FROM email_template ORDER BY template_id").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/admin/templates", methods=["POST"])
@admin_required
def admin_create_template():
    data = request.get_json()
    conn = get_db()
    conn.execute(
        "INSERT INTO email_template (name, subject, sender, content, suspicious, awareness) VALUES (?,?,?,?,?,?)",
        (
            data.get("name", ""),
            data.get("subject", ""),
            data.get("sender", ""),
            data.get("content", ""),
            data.get("suspicious", ""),
            data.get("awareness", ""),
        )
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Template created"}), 201

@app.route("/api/admin/templates/<int:tid>", methods=["PUT"])
@admin_required
def admin_update_template(tid):
    data = request.get_json()
    conn = get_db()
    t = conn.execute("SELECT * FROM email_template WHERE template_id=?", (tid,)).fetchone()
    if not t:
        return jsonify({"error": "Template not found"}), 404
    conn.execute(
        "UPDATE email_template SET name=?, subject=?, sender=?, content=?, suspicious=?, awareness=? WHERE template_id=?",
        (
            data.get("name", t["name"]),
            data.get("subject", t["subject"]),
            data.get("sender", t["sender"]),
            data.get("content", t["content"]),
            data.get("suspicious", t["suspicious"]),
            data.get("awareness", t["awareness"]),
            tid,
        )
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Template updated"})

@app.route("/api/admin/templates/<int:tid>", methods=["DELETE"])
@admin_required
def admin_delete_template(tid):
    conn = get_db()
    conn.execute("DELETE FROM email_template WHERE template_id=?", (tid,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Template deleted"})

# ------------------------------------------------------------------
# QUIZ MANAGEMENT (ADMIN)
# ------------------------------------------------------------------
@app.route("/api/admin/quizzes", methods=["GET"])
@admin_required
def admin_quizzes():
    conn = get_db()
    rows = conn.execute("SELECT * FROM quiz_questions ORDER BY question_id").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/admin/quizzes/<int:qid>", methods=["GET"])
@admin_required
def admin_quiz_detail(qid):
    conn = get_db()
    row = conn.execute("SELECT * FROM quiz_questions WHERE question_id=?", (qid,)).fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "Question not found"}), 404
    return jsonify(dict(row))

@app.route("/api/admin/quizzes", methods=["POST"])
@admin_required
def admin_create_quiz():
    data = request.get_json()
    question = (data.get("question") or "").strip()
    options = data.get("options") or []
    correct_index = data.get("correct_index", 0)
    category = (data.get("category") or "").strip()
    difficulty = (data.get("difficulty") or "Medium").strip()
    explanation = (data.get("explanation") or "").strip()
    active = 1 if data.get("active", True) else 0

    # Validation
    if not question:
        return jsonify({"error": "Question text is required"}), 400
    if not options or len(options) != 4 or any(not (o or "").strip() for o in options):
        return jsonify({"error": "All four options are required"}), 400
    if correct_index not in (0, 1, 2, 3):
        return jsonify({"error": "Correct answer must be one of the options"}), 400

    conn = get_db()
    # Prevent duplicate questions
    dup = conn.execute("SELECT question_id FROM quiz_questions WHERE question=?", (question,)).fetchone()
    if dup:
        return jsonify({"error": "This question already exists"}), 400

    conn.execute(
        "INSERT INTO quiz_questions (question, options, correct_index, category, difficulty, active, explanation) VALUES (?,?,?,?,?,?,?)",
        (question, json.dumps(options), correct_index, category, difficulty, active, explanation)
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Question created"}), 201

@app.route("/api/admin/quizzes/<int:qid>", methods=["PUT"])
@admin_required
def admin_update_quiz(qid):
    data = request.get_json()
    conn = get_db()
    q = conn.execute("SELECT * FROM quiz_questions WHERE question_id=?", (qid,)).fetchone()
    if not q:
        return jsonify({"error": "Question not found"}), 404

    question = (data.get("question", q["question"]) or "").strip()
    options = data.get("options", json.loads(q["options"]))
    correct_index = data.get("correct_index", q["correct_index"])
    category = (data.get("category", q["category"]) or "").strip()
    difficulty = (data.get("difficulty", q["difficulty"]) or "Medium").strip()
    explanation = (data.get("explanation", q["explanation"]) or "").strip()
    active = data.get("active", bool(q["active"]))
    active = 1 if active else 0

    if not question:
        return jsonify({"error": "Question text is required"}), 400
    if not options or len(options) != 4 or any(not (o or "").strip() for o in options):
        return jsonify({"error": "All four options are required"}), 400
    if correct_index not in (0, 1, 2, 3):
        return jsonify({"error": "Correct answer must be one of the options"}), 400

    # Prevent duplicate (excluding self)
    dup = conn.execute("SELECT question_id FROM quiz_questions WHERE question=? AND question_id!=?", (question, qid)).fetchone()
    if dup:
        return jsonify({"error": "This question already exists"}), 400

    conn.execute(
        "UPDATE quiz_questions SET question=?, options=?, correct_index=?, category=?, difficulty=?, active=?, explanation=? WHERE question_id=?",
        (question, json.dumps(options), correct_index, category, difficulty, active, explanation, qid)
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Question updated"})

@app.route("/api/admin/quizzes/<int:qid>", methods=["DELETE"])
@admin_required
def admin_delete_quiz(qid):
    conn = get_db()
    q = conn.execute("SELECT question_id FROM quiz_questions WHERE question_id=?", (qid,)).fetchone()
    if not q:
        return jsonify({"error": "Question not found"}), 404
    conn.execute("DELETE FROM quiz_questions WHERE question_id=?", (qid,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Question deleted"})

# ------------------------------------------------------------------
# RESPONSE MONITORING
# ------------------------------------------------------------------
@app.route("/api/admin/responses", methods=["GET"])
@admin_required
def admin_responses():
    conn = get_db()
    rows = conn.execute("""
        SELECT sr.*, u.name, u.email, c.title AS campaign_title
        FROM simulation_response sr
        JOIN users u ON u.user_id = sr.user_id
        JOIN campaign c ON c.campaign_id = sr.campaign_id
        ORDER BY sr.timestamp DESC
    """).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

# ------------------------------------------------------------------
# ANALYTICS
# ------------------------------------------------------------------
@app.route("/api/admin/analytics", methods=["GET"])
@admin_required
def admin_analytics():
    conn = get_db()
    # department-wise
    dept = conn.execute("""
        SELECT department, AVG(awareness_score) avg_score, COUNT(*) cnt FROM users GROUP BY department
    """).fetchall()
    dept_data = [
        {"department": r["department"] or "Unassigned", "avg_score": round(r["avg_score"], 1), "count": r["cnt"]}
        for r in dept
    ]

    # risk distribution
    risk = {
        "low": conn.execute("SELECT COUNT(*) c FROM users WHERE risk_level='Low'").fetchone()["c"],
        "medium": conn.execute("SELECT COUNT(*) c FROM users WHERE risk_level='Medium'").fetchone()["c"],
        "high": conn.execute("SELECT COUNT(*) c FROM users WHERE risk_level='High'").fetchone()["c"],
    }

    # phishing detection % = reported / (opened + clicked) * 100
    opened = conn.execute("SELECT COUNT(*) c FROM simulation_response WHERE email_opened=1").fetchone()["c"]
    reported = conn.execute("SELECT COUNT(*) c FROM simulation_response WHERE reported=1").fetchone()["c"]
    detection_pct = round((reported / opened * 100), 1) if opened else 0

    # per-user scores
    users = conn.execute("SELECT name, awareness_score, risk_level FROM users ORDER BY awareness_score DESC").fetchall()
    conn.close()
    return jsonify({
        "department": dept_data,
        "risk_distribution": risk,
        "detection_pct": detection_pct,
        "users": [dict(u) for u in users],
    })

# ------------------------------------------------------------------
# REPORTS
# ------------------------------------------------------------------
@app.route("/api/admin/reports", methods=["GET"])
@admin_required
def admin_reports():
    conn = get_db()
    total_users = conn.execute("SELECT COUNT(*) c FROM users").fetchone()["c"]
    total_responses = conn.execute("SELECT COUNT(*) c FROM simulation_response").fetchone()["c"]
    opened = conn.execute("SELECT COUNT(*) c FROM simulation_response WHERE email_opened=1").fetchone()["c"]
    clicked = conn.execute("SELECT COUNT(*) c FROM simulation_response WHERE link_clicked=1").fetchone()["c"]
    reported = conn.execute("SELECT COUNT(*) c FROM simulation_response WHERE reported=1").fetchone()["c"]
    avg = conn.execute("SELECT AVG(awareness_score) a FROM users").fetchone()["a"] or 0
    high = conn.execute("SELECT COUNT(*) c FROM users WHERE risk_level='High'").fetchone()["c"]
    low = conn.execute("SELECT COUNT(*) c FROM users WHERE risk_level='Low'").fetchone()["c"]

    click_rate = round(clicked / opened * 100, 1) if opened else 0
    report_rate = round(reported / opened * 100, 1) if opened else 0
    risk_pct = round(high / total_users * 100, 1) if total_users else 0

    recommendations = []
    if avg < 70:
        recommendations.append("Increase frequency of phishing simulation campaigns.")
    if high > 0:
        recommendations.append(f"Provide targeted training for {high} high-risk users.")
    if report_rate < 40:
        recommendations.append("Encourage users to report phishing attempts more frequently.")
    if len(recommendations) == 0:
        recommendations.append("Maintain current awareness program and continue periodic testing.")

    conn.close()
    return jsonify({
        "report_type": "Security Awareness Report",
        "generated": now(),
        "total_participants": total_users,
        "total_responses": total_responses,
        "opened": opened,
        "clicked": clicked,
        "reported": reported,
        "click_rate": click_rate,
        "report_rate": report_rate,
        "avg_awareness": round(avg, 1),
        "high_risk_count": high,
        "low_risk_count": low,
        "risk_pct": risk_pct,
        "recommendations": recommendations,
    })

# ------------------------------------------------------------------
# WEIGHTED AWARENESS SCORE (25% Simulations + 25% Training + 50% Quiz)
# ------------------------------------------------------------------
def _compute_weighted_awareness(conn, user_id):
    """Compute the weighted awareness score and persist it to the users table.

    Formula:
        Awareness Score = (Simulation Completion % × 25)
                       + (Training Completion % × 25)
                       + (Quiz Score % × 50)
    Capped at 100%. Returns the full breakdown for display.
    """
    total_active_sim = conn.execute("SELECT COUNT(*) c FROM campaign WHERE status='active'").fetchone()["c"]
    sim_done = conn.execute("SELECT COUNT(DISTINCT campaign_id) c FROM simulation_response WHERE user_id=?", (user_id,)).fetchone()["c"]
    sim_pct = round((sim_done / total_active_sim * 100), 2) if total_active_sim else 0
    sim_contribution = round(sim_pct * 0.25, 2)

    total_training = conn.execute("SELECT COUNT(*) c FROM training").fetchone()["c"]
    training_completed = conn.execute("SELECT COUNT(DISTINCT training_id) c FROM training_progress WHERE user_id=?", (user_id,)).fetchone()["c"]
    training_pct = round((training_completed / total_training * 100), 2) if total_training else 0
    training_contribution = round(training_pct * 0.25, 2)

    quiz = conn.execute("SELECT MAX(quiz_score) s FROM quiz_result WHERE user_id=?", (user_id,)).fetchone()["s"] or 0
    quiz_pct = min(float(quiz), 100.0)
    quiz_contribution = round(quiz_pct * 0.50, 2)

    total = round(min(sim_contribution + training_contribution + quiz_contribution, 100.0))

    # Persist the computed score (recomputed on every login/dashboard load)
    conn.execute("UPDATE users SET awareness_score=? WHERE user_id=?", (total, user_id))

    return {
        "simulation_pct": round(sim_pct, 1),
        "simulation_contribution": sim_contribution,
        "training_pct": round(training_pct, 1),
        "training_contribution": training_contribution,
        "quiz_pct": round(quiz_pct, 1),
        "quiz_contribution": quiz_contribution,
        "total": total,
    }

# ------------------------------------------------------------------
# USER DASHBOARD
# ------------------------------------------------------------------
@app.route("/api/user/dashboard", methods=["GET"])
@token_required
def user_dashboard():
    if request.user_role != "user":
        return jsonify({"error": "Unauthorized"}), 403
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE user_id=?", (request.user_id,)).fetchone()

    total_sim = conn.execute("SELECT COUNT(*) c FROM simulation_response WHERE user_id=?", (request.user_id,)).fetchone()["c"]
    quiz = conn.execute("SELECT MAX(quiz_score) s FROM quiz_result WHERE user_id=?", (request.user_id,)).fetchone()["s"] or 0
    training_done = conn.execute("SELECT COUNT(*) c FROM training").fetchone()["c"]

    # pending simulations = active campaigns not yet responded
    responded = conn.execute("SELECT COUNT(DISTINCT campaign_id) c FROM simulation_response WHERE user_id=?", (request.user_id,)).fetchone()["c"]
    total_campaigns = conn.execute("SELECT COUNT(*) c FROM campaign WHERE status='active'").fetchone()["c"]
    pending = max(total_campaigns - responded, 0)

    # ---- Weighted awareness score (recomputed & persisted) ----
    aware = _compute_weighted_awareness(conn, request.user_id)
    # refresh user row so awareness_score reflects the freshly computed value
    user = conn.execute("SELECT * FROM users WHERE user_id=?", (request.user_id,)).fetchone()

    # ---- Certification tracking ----
    total_training = conn.execute("SELECT COUNT(*) c FROM training").fetchone()["c"]
    training_completed = conn.execute("SELECT COUNT(DISTINCT training_id) c FROM training_progress WHERE user_id=?", (request.user_id,)).fetchone()["c"]
    all_training_done = total_training > 0 and training_completed >= total_training

    total_active_sim = conn.execute("SELECT COUNT(*) c FROM campaign WHERE status='active'").fetchone()["c"]
    sim_done = conn.execute("SELECT COUNT(DISTINCT campaign_id) c FROM simulation_response WHERE user_id=?", (request.user_id,)).fetchone()["c"]
    all_sim_done = total_active_sim > 0 and sim_done >= total_active_sim

    quiz_passed = quiz >= 80
    awareness_ready = (user["awareness_score"] or 0) >= 80

    all_requirements_met = (all_sim_done and all_training_done and quiz_passed and awareness_ready) or aware["total"] >= 100

    # Progress percentage (weighted across 4 requirement categories)
    prog_parts = 0
    prog_parts += 100 if all_sim_done else (round(sim_done / total_active_sim * 100) if total_active_sim else 0)
    prog_parts += 100 if all_training_done else (round(training_completed / total_training * 100) if total_training else 0)
    prog_parts += 100 if quiz_passed else min(quiz, 100)
    prog_parts += 100 if awareness_ready else min(user["awareness_score"] or 0, 100)
    progress_percent = round(prog_parts / 4)

    # Completion date: use latest quiz/sim/training completion if unlocked
    completion_date = None
    if all_requirements_met:
        cert = conn.execute("SELECT issued_at FROM certificates WHERE user_id=?", (request.user_id,)).fetchone()
        latest = conn.execute("""
            SELECT MAX(completion_date) d FROM (
                SELECT completion_date FROM quiz_result WHERE user_id=?
                UNION ALL SELECT timestamp FROM simulation_response WHERE user_id=?
                UNION ALL SELECT completed_at FROM training_progress WHERE user_id=?
            )
        """, (request.user_id, request.user_id, request.user_id)).fetchone()
        completion_date = (cert["issued_at"] if cert else latest["d"]) or now()

    notifications = conn.execute("SELECT * FROM notifications WHERE user_id=? OR user_id IS NULL ORDER BY notification_id DESC LIMIT 5", (request.user_id,)).fetchall()

    conn.commit()
    conn.close()
    return jsonify({
        "user": dict(user),
        "total_simulations": total_sim,
        "quiz_score": quiz,
        "security_level": user["risk_level"],
        "training_modules": training_done,
        "pending_simulations": pending,
        "notifications": [dict(n) for n in notifications],
        "awareness_breakdown": {
            "simulation_pct": aware["simulation_pct"],
            "simulation_contribution": aware["simulation_contribution"],
            "training_pct": aware["training_pct"],
            "training_contribution": aware["training_contribution"],
            "quiz_pct": aware["quiz_pct"],
            "quiz_contribution": aware["quiz_contribution"],
            "total": aware["total"],
        },
        "certification": {
            "all_simulations_done": all_sim_done,
            "all_training_done": all_training_done,
            "quiz_passed": quiz_passed,
            "awareness_ready": awareness_ready,
            "all_requirements_met": all_requirements_met,
            "progress_percent": progress_percent,
            "completion_date": completion_date,
            "simulations_done": sim_done,
            "simulations_total": total_active_sim,
            "training_done": training_completed,
            "training_total": total_training,
            "quiz_score": quiz,
            "awareness_score": user["awareness_score"] or 0,
        },
    })

@app.route("/api/templates", methods=["GET"])
@token_required
def user_templates():
    conn = get_db()
    rows = conn.execute("SELECT template_id, name, subject, sender, content, suspicious, awareness FROM email_template").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/training", methods=["GET"])
@token_required
def training_list():
    conn = get_db()
    rows = conn.execute("SELECT * FROM training ORDER BY training_id").fetchall()
    # include completion status for the current user
    done = conn.execute("SELECT training_id FROM training_progress WHERE user_id=?", (request.user_id,)).fetchall()
    done_ids = {r["training_id"] for r in done}
    result = [dict(r) for r in rows]
    for t in result:
        t["completed"] = t["training_id"] in done_ids
    conn.close()
    return jsonify(result)

@app.route("/api/training/<int:training_id>/complete", methods=["POST"])
@token_required
def training_complete(training_id):
    conn = get_db()
    exists = conn.execute("SELECT training_id FROM training WHERE training_id=?", (training_id,)).fetchone()
    if not exists:
        conn.close()
        return jsonify({"error": "Training module not found"}), 404
    conn.execute(
        "INSERT OR IGNORE INTO training_progress (user_id, training_id) VALUES (?,?)",
        (request.user_id, training_id)
    )
    # Recompute the weighted awareness score automatically after training completion
    aware = _compute_weighted_awareness(conn, request.user_id)
    conn.commit()
    conn.close()
    return jsonify({"message": "Training module completed", "awareness_score": aware["total"]})

@app.route("/api/user/certificate", methods=["GET"])
@token_required
def user_certificate():
    if request.user_role != "user":
        return jsonify({"error": "Unauthorized"}), 403
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE user_id=?", (request.user_id,)).fetchone()

    total_training = conn.execute("SELECT COUNT(*) c FROM training").fetchone()["c"]
    training_completed = conn.execute("SELECT COUNT(DISTINCT training_id) c FROM training_progress WHERE user_id=?", (request.user_id,)).fetchone()["c"]
    total_active_sim = conn.execute("SELECT COUNT(*) c FROM campaign WHERE status='active'").fetchone()["c"]
    sim_done = conn.execute("SELECT COUNT(DISTINCT campaign_id) c FROM simulation_response WHERE user_id=?", (request.user_id,)).fetchone()["c"]
    quiz = conn.execute("SELECT MAX(quiz_score) s FROM quiz_result WHERE user_id=?", (request.user_id,)).fetchone()["s"] or 0

    all_training_done = total_training > 0 and training_completed >= total_training
    all_sim_done = total_active_sim > 0 and sim_done >= total_active_sim
    quiz_passed = quiz >= 80
    awareness_ready = (user["awareness_score"] or 0) >= 80
    all_requirements_met = all_training_done and all_sim_done and quiz_passed and awareness_ready

    if not all_requirements_met:
        conn.close()
        return jsonify({"error": "Certificate not yet unlocked"}), 403

    # Generate / retrieve a stable unique certificate ID
    cert = conn.execute("SELECT * FROM certificates WHERE user_id=?", (request.user_id,)).fetchone()
    if not cert:
        import hashlib
        raw = f"{request.user_id}-{user['name']}-{user['awareness_score']}"
        cert_id = "CERT-" + hashlib.sha256(raw.encode()).hexdigest()[:12].upper()
        issued_at = now()
        conn.execute("INSERT INTO certificates (certificate_id, user_id, issued_at) VALUES (?,?,?)", (cert_id, request.user_id, issued_at))
        conn.commit()
    else:
        cert_id = cert["certificate_id"]
        issued_at = cert["issued_at"]

    conn.close()
    return jsonify({
        "available": True,
        "user_name": user["name"],
        "certificate_id": cert_id,
        "issued_at": issued_at,
        "title": "Cyber Security Awareness Certificate",
        "quiz_score": quiz,
        "awareness_score": user["awareness_score"],
    })

@app.route("/api/quiz", methods=["GET"])
@token_required
def quiz_questions():
    conn = get_db()
    # Only return active questions for users
    rows = conn.execute("SELECT * FROM quiz_questions WHERE active=1 ORDER BY question_id").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/quiz/submit", methods=["POST"])
@token_required
def quiz_submit():
    data = request.get_json()
    answers = data.get("answers", [])
    conn = get_db()
    questions = conn.execute("SELECT question_id, correct_index FROM quiz_questions WHERE active=1").fetchall()
    qmap = {r["question_id"]: r["correct_index"] for r in questions}
    correct = 0
    for a in answers:
        qid = a.get("question_id")
        chosen = a.get("chosen")
        if qid in qmap and qmap[qid] == chosen:
            correct += 1
    total = len(questions)
    score = round(correct / total * 100) if total else 0
    conn.execute("INSERT INTO quiz_result (user_id, quiz_score) VALUES (?,?)", (request.user_id, score))
    # Recompute the weighted awareness score automatically after quiz completion
    aware = _compute_weighted_awareness(conn, request.user_id)
    conn.commit()
    conn.close()
    return jsonify({"score": score, "correct": correct, "total": total, "awareness_score": aware["total"]})

# ------------------------------------------------------------------
# USER SIMULATIONS
# ------------------------------------------------------------------
@app.route("/api/user/simulations", methods=["GET"])
@token_required
def user_simulations():
    if request.user_role != "user":
        return jsonify({"error": "Unauthorized"}), 403
    conn = get_db()
    campaigns = conn.execute("SELECT * FROM campaign WHERE status='active' ORDER BY campaign_id DESC").fetchall()
    responses = conn.execute("SELECT * FROM simulation_response WHERE user_id=?", (request.user_id,)).fetchall()
    resp_map = {r["campaign_id"]: r for r in responses}
    result = []
    for c in campaigns:
        r = resp_map.get(c["campaign_id"])
        result.append({
            "campaign": dict(c),
            "response": dict(r) if r else None,
        })
    conn.close()
    return jsonify(result)

@app.route("/api/user/simulations/<int:campaign_id>/action", methods=["POST"])
@token_required
def user_simulation_action(campaign_id):
    if request.user_role != "user":
        return jsonify({"error": "Unauthorized"}), 403
    data = request.get_json()
    action = data.get("action")  # email_opened | link_clicked | reported | page_visited | quiz_completed
    conn = get_db()
    resp = conn.execute("SELECT * FROM simulation_response WHERE user_id=? AND campaign_id=?", (request.user_id, campaign_id)).fetchone()

    if not resp:
        # create a fresh response
        conn.execute(
            "INSERT INTO simulation_response (user_id, campaign_id) VALUES (?,?)",
            (request.user_id, campaign_id)
        )
        resp = conn.execute("SELECT * FROM simulation_response WHERE user_id=? AND campaign_id=?", (request.user_id, campaign_id)).fetchone()

    valid_actions = {"email_opened", "link_clicked", "reported", "page_visited", "quiz_completed"}
    if action not in valid_actions:
        return jsonify({"error": "Invalid action"}), 400

    col = action
    conn.execute(f"UPDATE simulation_response SET {col}=1 WHERE response_id=?", (resp["response_id"],))
    conn.execute("INSERT INTO activity_log (user_id, action, campaign_id) VALUES (?,?,?)", (request.user_id, action, campaign_id))

    # compute score based on actions
    updated = conn.execute("SELECT * FROM simulation_response WHERE response_id=?", (resp["response_id"],)).fetchone()
    score = 0
    if updated["reported"]:
        score = 100
        conn.execute("UPDATE users SET risk_level='Low' WHERE user_id=?", (request.user_id,))
    elif updated["link_clicked"]:
        score = 30
        conn.execute("UPDATE users SET risk_level='High' WHERE user_id=?", (request.user_id,))
    elif updated["email_opened"]:
        score = 50
        conn.execute("UPDATE users SET risk_level='Medium' WHERE user_id=?", (request.user_id,))
    conn.execute("UPDATE simulation_response SET score=? WHERE response_id=?", (score, resp["response_id"]))
    # Recompute the weighted awareness score automatically after simulation action
    aware = _compute_weighted_awareness(conn, request.user_id)
    conn.commit()
    conn.close()
    return jsonify({"message": "Action recorded", "score": score, "awareness_score": aware["total"]})

# ------------------------------------------------------------------
# USER PROFILE
# ------------------------------------------------------------------
@app.route("/api/user/profile", methods=["PUT"])
@token_required
def user_profile():
    if request.user_role != "user":
        return jsonify({"error": "Unauthorized"}), 403
    data = request.get_json()
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE user_id=?", (request.user_id,)).fetchone()
    conn.execute(
        "UPDATE users SET name=?, department=? WHERE user_id=?",
        (data.get("name", user["name"]), data.get("department", user["department"]), request.user_id)
    )
    if data.get("password"):
        conn.execute("UPDATE users SET password_hash=? WHERE user_id=?", (hash_password(data["password"]), request.user_id))
    conn.commit()
    conn.close()
    return jsonify({"message": "Profile updated"})

@app.route("/api/user/results", methods=["GET"])
@token_required
def user_results():
    if request.user_role != "user":
        return jsonify({"error": "Unauthorized"}), 403
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE user_id=?", (request.user_id,)).fetchone()
    sims = conn.execute("SELECT * FROM simulation_response WHERE user_id=? ORDER BY timestamp DESC", (request.user_id,)).fetchall()
    quizzes = conn.execute("SELECT * FROM quiz_result WHERE user_id=? ORDER BY completion_date DESC", (request.user_id,)).fetchall()

    detected = sum(1 for s in sims if s["reported"])
    total = len(sims)
    correct_rate = round(detected / total * 100) if total else 0

    # mistake analysis
    mistakes = []
    for s in sims:
        if s["link_clicked"] and not s["reported"]:
            mistakes.append("Clicked a phishing link without reporting it")
    if correct_rate < 70:
        mistakes.append("Struggles with identifying suspicious indicators")

    recommendation = ""
    if user["risk_level"] == "Low":
        recommendation = "Continue practicing phishing identification techniques."
    elif user["risk_level"] == "Medium":
        recommendation = "Review the training modules and focus on URL detection."
    else:
        recommendation = "Complete all training modules and retake the phishing quiz."

    conn.close()
    return jsonify({
        "user": dict(user),
        "simulations": [dict(s) for s in sims],
        "quizzes": [dict(q) for q in quizzes],
        "correct_rate": correct_rate,
        "mistakes": mistakes,
        "recommendation": recommendation,
    })

if __name__ == "__main__":
    import os
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 5001))
    print(f" * Server running on http://localhost:{port}")
    print(f" * Server accessible on local network at http://0.0.0.0:{port}")
    app.run(debug=True, host=host, port=port)


