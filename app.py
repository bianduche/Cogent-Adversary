"""
Cogent-Adversary 实验系统主后端
Flask + SocketIO + SQLite + OpenAI GPT-4o-mini
"""
import os
import json
import sqlite3
import time
import random
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, jsonify, g
from flask_socketio import SocketIO, emit, join_room
from openai import OpenAI
import numpy as np

from modules.CSDI import CSDI
from modules.CODA import CODA
from modules.KGAR import KGAR
from modules.ACCL import ACCL

# ───────────────────────────────
# 初始化应用
# ───────────────────────────────
app = Flask(__name__)
app.config["SECRET_KEY"] = "cogent-adversary-secret-key-2026"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# 加载配置
with open("config.json", "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

client = OpenAI(
    api_key=CONFIG["openai_api_key"],
    base_url=CONFIG.get("base_url", "https://api.openai.com/v1")
)
MODEL = CONFIG["model"]
DB_PATH = CONFIG["db_path"]
MAX_RETRY = CONFIG["max_retry"]
ACCL_THRESHOLD = CONFIG["accl_threshold"]

# 初始化核心模块
csdi = CSDI(CONFIG["csdi_params"])
coda = CODA(eta=0.35, delta=0.28, T=10)
kgar = KGAR(CONFIG["kg_path"])
accl = ACCL()

# 内存状态：课时状态机、学生当前session/turn
# student_states[student_id] = {"session": 1, "turn": 0, "status": "IDLE", ...}
student_states = {}

# ───────────────────────────────
# 数据库工具
# ───────────────────────────────
def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()

def init_db():
    """初始化数据库表"""
    with app.app_context():
        db = get_db()
        cursor = db.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                group_id TEXT NOT NULL,
                session INTEGER NOT NULL,
                turn INTEGER NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                O1 INTEGER,
                O2 INTEGER,
                O3 INTEGER,
                O4 INTEGER,
                P_S1 REAL, P_S2 REAL, P_S3 REAL, P_S4 REAL,
                D_t REAL,
                K_t REAL,
                alpha REAL,
                path_a TEXT,
                path_b TEXT,
                mentor_resp TEXT,
                devil_resp TEXT,
                accl_delta_mentor REAL,
                accl_delta_devil REAL,
                accl_passed INTEGER,
                student_question TEXT,
                student_answer TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                student_id TEXT PRIMARY KEY,
                group_id TEXT NOT NULL,
                gender TEXT,
                grade TEXT,
                major TEXT,
                prior_welding_exp INTEGER,
                pretest_score REAL,
                posttest_score REAL,
                delayed_score REAL,
                reasoning_pretest REAL,
                reasoning_posttest REAL,
                ues_score REAL,
                sus_score REAL,
                manipulation_check TEXT,
                completed INTEGER DEFAULT 0
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tlx (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                session INTEGER NOT NULL,
                mental_demand INTEGER,
                temporal_demand INTEGER,
                effort INTEGER,
                frustration INTEGER,
                performance INTEGER,
                weighted_score REAL,
                timestamp DATETIME
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                transcript TEXT,
                coded_themes TEXT,
                interviewer TEXT,
                duration_min INTEGER,
                timestamp DATETIME
            )
        """)

        # 用于RA组的alpha历史记录
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alpha_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                alpha REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        db.commit()
        print("[DB] 数据库初始化完成")

# ───────────────────────────────
# LLM调用（带重试机制）
# ───────────────────────────────
def call_llm(messages, temperature=0.7, max_tokens=512):
    """调用OpenAI API，带重试机制"""
    for attempt in range(MAX_RETRY + 1):
        try:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            print(f"[LLM Error] attempt {attempt+1}/{MAX_RETRY+1}: {e}")
            if attempt < MAX_RETRY:
                time.sleep(1)
            else:
                return "[系统错误：AI服务暂时不可用，请稍后重试]"
    return "[系统错误：AI服务暂时不可用]"

def build_mentor_prompt(path_a, question):
    return [
        {"role": "system", "content": f"""你是焊接缺陷分析领域的苏格拉底式导师。你的任务是基于以下知识路径，以引导式提问帮助学生理解因果关系。

知识路径：{' -> '.join(path_a)}

要求：
1. 必须基于上述路径中的实体和关系展开解释
2. 不要引入路径外的新概念
3. 使用中文回答
4. 语气鼓励、引导性强"""},
        {"role": "user", "content": f"学生问题：{question}"}
    ]

def build_devil_prompt(path_b, mentor_response, question, alpha):
    if alpha > 0.7:
        persona = "严格学术质疑者"
        style = "直接指出逻辑漏洞，要求证据"
    elif alpha > 0.4:
        persona = "建设性反对者"
        style = "提出具体反例，推动深入思考"
    else:
        persona = "好奇追问者"
        style = "温和询问细节，引导补充论证"

    return [
        {"role": "system", "content": f"""你是焊接缺陷分析领域的{persona}。你的任务是基于以下知识路径，对导师的观点提出质疑或补充。

知识路径：{' -> '.join(path_b)}

要求：
1. 必须基于上述路径中的实体和关系展开反驳
2. 不要引入路径外的新概念
3. 使用中文回答
4. {style}"""},
        {"role": "user", "content": f"导师观点：{mentor_response}\n\n学生问题：{question}"}
    ]

# ───────────────────────────────
# Alpha计算逻辑
# ───────────────────────────────
def get_alpha(group, student_id, D_t, K_t, t, last_correct):
    if group == "SA":
        return 0.0
    elif group == "FA":
        return 0.5
    elif group == "RA":
        db = get_db()
        row = db.execute(
            "SELECT alpha FROM alpha_history WHERE student_id = ? ORDER BY id DESC LIMIT 1",
            (student_id,)
        ).fetchone()
        last_alpha = row["alpha"] if row else 0.5
        new_alpha = np.clip(last_alpha + 0.1 * (1 if last_correct else -1), 0, 1)
        db.execute(
            "INSERT INTO alpha_history (student_id, alpha) VALUES (?, ?)",
            (student_id, float(new_alpha))
        )
        db.commit()
        return float(new_alpha)
    elif group == "CA":
        return coda.solve(D_t, K_t, t)
    return 0.0

# ───────────────────────────────
# 路由
# ───────────────────────────────
@app.route("/")
def student_page():
    group = request.args.get("group", "SA")
    sid = request.args.get("sid", "S001")
    return render_template("index.html", group=group, sid=sid)

@app.route("/teacher")
def teacher_page():
    return render_template("teacher.html")

@app.route("/survey")
def survey_page():
    sid = request.args.get("sid", "S001")
    session = request.args.get("session", "1")
    return render_template("survey.html", sid=sid, session=session)

# ───────────────────────────────
# API端点
# ───────────────────────────────
@app.route("/api/register", methods=["POST"])
def register_student():
    data = request.json
    sid = data.get("student_id")
    group = data.get("group_id", "SA")
    db = get_db()
    db.execute("""
        INSERT OR REPLACE INTO students 
        (student_id, group_id, gender, grade, major, prior_welding_exp)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (sid, group, data.get("gender"), data.get("grade"), data.get("major"), data.get("prior_welding_exp", 0)))
    db.commit()

    # 初始化学生状态
    student_states[sid] = {
        "session": 1,
        "turn": 0,
        "status": "IDLE",
        "group": group,
        "video_ended": False
    }
    csdi.reset_student(sid)
    return jsonify({"status": "ok", "student_id": sid, "group": group})

@app.route("/api/session/start", methods=["POST"])
def session_start():
    data = request.json
    sid = data.get("student_id")
    session_num = data.get("session", 1)
    if sid in student_states:
        student_states[sid]["session"] = session_num
        student_states[sid]["turn"] = 0
        student_states[sid]["status"] = "VIDEO_PLAYING"
        student_states[sid]["video_ended"] = False
        csdi.reset_student(sid)
    return jsonify({"status": "ok", "session": session_num})

@app.route("/api/video/end", methods=["POST"])
def video_end():
    data = request.json
    sid = data.get("student_id")
    if sid in student_states:
        student_states[sid]["video_ended"] = True
        student_states[sid]["status"] = "AGENT_INTERACTION"
    return jsonify({"status": "ok", "status_text": "AGENT_INTERACTION"})

@app.route("/api/ask", methods=["POST"])
def student_ask():
    """处理学生提问（HTTP轮询版，也支持SocketIO）"""
    start_time = time.time()
    data = request.json
    sid = data.get("student_id")
    group = data.get("group", "SA")
    question = data.get("question", "")
    answer = data.get("student_answer", "")

    # 观测变量
    answer_correct = data.get("answer_correct", True)
    response_time = data.get("response_time", 10.0)
    semantic_sim = data.get("semantic_sim", 0.8)
    edits_ratio = data.get("edits_ratio", 0.1)

    # CSDI前向推断
    obs = csdi.extract_obs(answer_correct, response_time, semantic_sim, edits_ratio)
    posterior = csdi.forward(sid, obs)
    D_t = csdi.get_dissonance(posterior)
    K_t = csdi.get_mastery(posterior)

    # 当前课时序号 (0-9)
    t = student_states.get(sid, {}).get("session", 1) - 1

    # 计算alpha
    alpha = get_alpha(group, sid, D_t, K_t, t, answer_correct)

    # KGAR检索路径
    # 从问题中提取核心实体（简单版：取问题中最长的词或第一个名词短语）
    entity = _extract_entity(question)
    path_a, path_b = kgar.find_paths(entity, k=3)

    # 生成Mentor回复
    mentor_prompt = build_mentor_prompt(path_a, question)
    mentor_resp = call_llm(mentor_prompt, temperature=0.7)

    # ACCL校验Mentor
    mentor_passed, mentor_delta = accl.check(mentor_resp, path_a)
    if not mentor_passed:
        # 重试一次，降低temperature
        mentor_resp = call_llm(mentor_prompt, temperature=0.3)
        mentor_passed, mentor_delta = accl.check(mentor_resp, path_a)

    devil_resp = ""
    devil_passed = True
    devil_delta = 0.0

    # 非SA组生成Devil回复
    if group != "SA":
        devil_prompt = build_devil_prompt(path_b, mentor_resp, question, alpha)
        devil_resp = call_llm(devil_prompt, temperature=0.7)
        devil_passed, devil_delta = accl.check(devil_resp, path_b)
        if not devil_passed:
            devil_resp = call_llm(devil_prompt, temperature=0.3)
            devil_passed, devil_delta = accl.check(devil_resp, path_b)

    accl_passed = 1 if (mentor_passed and devil_passed) else 0

    # 更新turn
    if sid in student_states:
        student_states[sid]["turn"] += 1
    turn = student_states.get(sid, {}).get("turn", 0)
    session = student_states.get(sid, {}).get("session", 1)

    # 写入数据库
    db = get_db()
    db.execute("""
        INSERT INTO logs 
        (student_id, group_id, session, turn, O1, O2, O3, O4,
         P_S1, P_S2, P_S3, P_S4, D_t, K_t, alpha,
         path_a, path_b, mentor_resp, devil_resp,
         accl_delta_mentor, accl_delta_devil, accl_passed,
         student_question, student_answer)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        sid, group, session, turn,
        obs[0], obs[1], obs[2], obs[3],
        float(posterior[0]), float(posterior[1]), float(posterior[2]), float(posterior[3]),
        D_t, K_t, alpha,
        json.dumps(path_a, ensure_ascii=False),
        json.dumps(path_b, ensure_ascii=False),
        mentor_resp, devil_resp,
        mentor_delta, devil_delta, accl_passed,
        question, answer
    ))
    db.commit()

    elapsed = time.time() - start_time
    print(f"[Ask] sid={sid}, group={group}, alpha={alpha:.2f}, time={elapsed:.2f}s")

    return jsonify({
        "mentor_resp": mentor_resp,
        "devil_resp": devil_resp,
        "alpha": alpha,
        "path_a": path_a,
        "path_b": path_b,
        "D_t": D_t,
        "K_t": K_t,
        "posterior": posterior.tolist(),
        "elapsed": elapsed,
        "turn": turn
    })

def _extract_entity(text: str) -> str:
    """从问题中提取核心实体（简化版）"""
    # 常见焊接缺陷关键词
    keywords = ["裂纹", "气孔", "夹渣", "未焊透", "未熔合", "咬边", "焊瘤", "塌陷", "烧穿", "飞溅"]
    for kw in keywords:
        if kw in text:
            return kw
    # 默认返回问题前10个字
    return text[:10] if text else "焊接缺陷"

@app.route("/api/tlx/submit", methods=["POST"])
def submit_tlx():
    data = request.json
    sid = data.get("student_id")
    session = data.get("session", 1)
    mental = data.get("mental_demand", 50)
    temporal = data.get("temporal_demand", 50)
    effort = data.get("effort", 50)
    frustration = data.get("frustration", 50)
    performance = data.get("performance", 50)
    weighted = (mental + temporal + effort + frustration + (100 - performance)) / 5.0

    db = get_db()
    db.execute("""
        INSERT INTO tlx (student_id, session, mental_demand, temporal_demand, effort, frustration, performance, weighted_score, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (sid, session, mental, temporal, effort, frustration, performance, weighted, datetime.now()))
    db.commit()

    # 更新状态为可进入下一课时
    if sid in student_states:
        student_states[sid]["status"] = "END"

    return jsonify({"status": "ok", "weighted_score": weighted})

@app.route("/api/teacher/dashboard", methods=["GET"])
def teacher_dashboard():
    """获取Dashboard数据"""
    db = get_db()

    # 班级热力图数据
    rows = db.execute("""
        SELECT student_id, group_id, session, P_S1, P_S2, P_S3, P_S4 
        FROM logs 
        WHERE id IN (SELECT MAX(id) FROM logs GROUP BY student_id, session)
        ORDER BY student_id, session
    """).fetchall()

    heatmap = {}
    for r in rows:
        sid = r["student_id"]
        if sid not in heatmap:
            heatmap[sid] = {"group": r["group_id"], "sessions": {}}
        # 确定当前状态（概率最大的）
        probs = [r["P_S1"], r["P_S2"], r["P_S3"], r["P_S4"]]
        state = probs.index(max(probs)) + 1  # 1-4
        heatmap[sid]["sessions"][r["session"]] = state

    # NASA-TLX预警列表 (>75)
    tlx_rows = db.execute("""
        SELECT student_id, session, weighted_score FROM tlx WHERE weighted_score > 75
        ORDER BY weighted_score DESC
    """).fetchall()
    alerts = [{"student_id": r["student_id"], "session": r["session"], "score": r["weighted_score"]} for r in tlx_rows]

    # 最近对话抽样
    chat_rows = db.execute("""
        SELECT student_id, student_question, mentor_resp, devil_resp, timestamp 
        FROM logs ORDER BY id DESC LIMIT 50
    """).fetchall()
    chats = []
    for r in chat_rows:
        chats.append({
            "student_id": r["student_id"],
            "question": r["student_question"],
            "mentor": r["mentor_resp"][:100] + "..." if r["mentor_resp"] else "",
            "devil": r["devil_resp"][:100] + "..." if r["devil_resp"] else "",
            "time": r["timestamp"]
        })

    return jsonify({"heatmap": heatmap, "alerts": alerts, "chats": chats})

@app.route("/api/teacher/export", methods=["GET"])
def export_csv():
    """导出CSV数据"""
    import csv
    from io import StringIO
    db = get_db()

    output = StringIO()
    writer = csv.writer(output)

    # 导出logs表
    rows = db.execute("SELECT * FROM logs").fetchall()
    if rows:
        headers = rows[0].keys()
        writer.writerow(headers)
        for r in rows:
            writer.writerow([r[h] for h in headers])

    output.seek(0)
    return output.getvalue(), 200, {"Content-Type": "text/csv; charset=utf-8-sig", "Content-Disposition": "attachment; filename=experiment_logs.csv"}

@app.route("/api/student/status", methods=["GET"])
def student_status():
    sid = request.args.get("sid")
    return jsonify(student_states.get(sid, {"status": "UNKNOWN"}))

# ───────────────────────────────
# SocketIO事件（实时通信）
# ───────────────────────────────
@socketio.on("connect")
def handle_connect():
    print("[SocketIO] Client connected")

@socketio.on("join")
def handle_join(data):
    sid = data.get("student_id")
    join_room(sid)
    emit("joined", {"room": sid})

@socketio.on("student_message")
def handle_student_message(data):
    """SocketIO版学生提问处理"""
    # 复用HTTP版的逻辑
    with app.test_client() as client:
        resp = client.post("/api/ask", json=data)
        result = resp.get_json()
        emit("ai_response", result, room=data.get("student_id"))

# ───────────────────────────────
# 启动
# ───────────────────────────────
if __name__ == "__main__":
    init_db()
    socketio.run(app, host=CONFIG["host"], port=CONFIG["port"], debug=True, allow_unsafe_werkzeug=True)
