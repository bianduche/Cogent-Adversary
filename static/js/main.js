// Cogent-Adversary 学生前端主逻辑

// ─── 全局状态 ───
const urlParams = new URLSearchParams(window.location.search);
const GROUP = urlParams.get("group") || "SA";
const SID = urlParams.get("sid") || "S001";
let CURRENT_SESSION = parseInt(urlParams.get("session")) || 1;
let CURRENT_TURN = 0;
let VIDEO_ENDED = false;
let IS_SENDING = false;

// SocketIO连接
const socket = io();
socket.emit("join", {student_id: SID});

socket.on("connect", () => {
    console.log("[SocketIO] 已连接");
});

socket.on("ai_response", (data) => {
    renderResponse(data);
    IS_SENDING = false;
    document.getElementById("sendBtn").disabled = false;
    document.getElementById("sendBtn").textContent = "发送";
});

// ─── 初始化 ───
document.addEventListener("DOMContentLoaded", () => {
    // 设置头部信息
    document.getElementById("headerInfo").textContent = ` | 组别: ${GROUP} | 学生: ${SID}`;
    document.getElementById("currentSession").textContent = CURRENT_SESSION;

    // 根据组别切换UI
    if (GROUP === "SA") {
        document.getElementById("saChat").style.display = "block";
        document.getElementById("dualChat").style.display = "none";
        document.getElementById("headerTitle").textContent = "🤖 AI 导师";
        document.getElementById("kgToggle").style.display = "none";
    } else {
        document.getElementById("saChat").style.display = "none";
        document.getElementById("dualChat").style.display = "flex";
        document.getElementById("headerTitle").textContent = "⚔️ 双Agent辩论";
        document.getElementById("kgToggle").style.display = "block";
        document.getElementById("alphaTag").style.display = "inline-block";
    }

    // 注册学生
    registerStudent();

    // 启动课时
    startSession();

    // 添加系统欢迎消息
    addSystemMessage("欢迎来到第 " + CURRENT_SESSION + " 课时！请观看左侧视频，结束后可与AI进行互动。");
});

async function registerStudent() {
    try {
        await fetch("/api/register", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                student_id: SID,
                group_id: GROUP,
                gender: "",
                grade: "",
                major: "",
                prior_welding_exp: 0
            })
        });
    } catch (e) {
        console.error("注册失败:", e);
    }
}

async function startSession() {
    try {
        await fetch("/api/session/start", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({student_id: SID, session: CURRENT_SESSION})
        });
    } catch (e) {
        console.error("启动课时失败:", e);
    }
}

// ─── 视频控制 ───
function endVideo() {
    VIDEO_ENDED = true;
    document.getElementById("videoPlaceholder").innerHTML = `
        <div style="color:#fff;font-size:18px;">✅ 视频播放完毕</div>
        <div style="color:#fff;margin-top:10px;opacity:0.8;">现在可以开始提问了</div>
    `;
    document.getElementById("videoProgress").style.display = "block";

    fetch("/api/video/end", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({student_id: SID})
    });

    addSystemMessage("视频播放结束，你现在可以向AI助手提问了！");
}

// ─── 消息发送 ───
function sendMessage() {
    const input = document.getElementById("userInput");
    const text = input.value.trim();
    if (!text || IS_SENDING) return;

    if (!VIDEO_ENDED) {
        addSystemMessage("请等待视频播放完毕后提问。");
        return;
    }

    IS_SENDING = true;
    const btn = document.getElementById("sendBtn");
    btn.disabled = true;
    btn.innerHTML = '发送中<span class="loading"></span>';

    // 显示用户消息
    addUserMessage(text);
    input.value = "";

    // 构造观测变量（简化版，实际应由前端行为采集）
    const answerCorrect = Math.random() > 0.3;  // 模拟
    const responseTime = 10 + Math.random() * 40;  // 模拟10-50秒
    const semanticSim = 0.4 + Math.random() * 0.6;  // 模拟0.4-1.0
    const editsRatio = Math.random() * 0.5;  // 模拟0-0.5

    const payload = {
        student_id: SID,
        group: GROUP,
        question: text,
        student_answer: text,
        answer_correct: answerCorrect,
        response_time: responseTime,
        semantic_sim: semanticSim,
        edits_ratio: editsRatio
    };

    // 优先使用HTTP（更稳定），SocketIO作为备选
    fetch("/api/ask", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(payload)
    })
    .then(r => r.json())
    .then(data => {
        renderResponse(data);
        IS_SENDING = false;
        btn.disabled = false;
        btn.textContent = "发送";
    })
    .catch(err => {
        console.error("请求失败:", err);
        addSystemMessage("网络错误，请重试。");
        IS_SENDING = false;
        btn.disabled = false;
        btn.textContent = "发送";
    });
}

// ─── 渲染回复 ───
function renderResponse(data) {
    CURRENT_TURN = data.turn || CURRENT_TURN + 1;
    document.getElementById("turnInfo").textContent = `第 ${CURRENT_TURN} 轮`;

    if (GROUP === "SA") {
        addMentorMessageSA(data.mentor_resp);
    } else {
        addMentorMessageDual(data.mentor_resp);
        addDevilMessage(data.devil_resp, data.alpha);
    }

    // 更新alpha显示
    if (GROUP !== "SA") {
        document.getElementById("alphaTag").textContent = `强度: ${data.alpha.toFixed(2)}`;
    }

    // 存储路径用于可视化
    window.currentPathA = data.path_a;
    window.currentPathB = data.path_b;

    // 检查是否达到课时结束条件（简化：15轮后自动弹出问卷）
    if (CURRENT_TURN >= 15) {
        setTimeout(() => {
            if (confirm("本课时对话轮数已达上限，是否进入课后问卷？")) {
                window.location.href = `/survey?sid=${SID}&session=${CURRENT_SESSION}`;
            }
        }, 500);
    }
}

// ─── 消息添加函数 ───
function addUserMessage(text) {
    const div = document.createElement("div");
    div.className = "message user";
    div.textContent = text;

    if (GROUP === "SA") {
        document.getElementById("saChat").appendChild(div);
        scrollToBottom("saChat");
    } else {
        // 双模式下同时添加到两个窗口（或只添加到导师窗口）
        const clone = div.cloneNode(true);
        document.getElementById("mentorMessages").appendChild(div);
        document.getElementById("devilMessages").appendChild(clone);
        scrollToBottom("mentorMessages");
        scrollToBottom("devilMessages");
    }
}

function addMentorMessageSA(text) {
    const div = document.createElement("div");
    div.className = "message mentor";
    div.innerHTML = `<strong>🤖 导师:</strong> ${text}`;
    document.getElementById("saChat").appendChild(div);
    scrollToBottom("saChat");
}

function addMentorMessageDual(text) {
    const div = document.createElement("div");
    div.className = "message mentor";
    div.innerHTML = `<strong>🤖:</strong> ${text}`;
    document.getElementById("mentorMessages").appendChild(div);
    scrollToBottom("mentorMessages");
}

function addDevilMessage(text, alpha) {
    if (!text) return;
    const div = document.createElement("div");
    div.className = "message devil";
    div.innerHTML = `<strong>😈:</strong> ${text}`;
    document.getElementById("devilMessages").appendChild(div);
    scrollToBottom("devilMessages");
}

function addSystemMessage(text) {
    const div = document.createElement("div");
    div.className = "message system";
    div.textContent = text;

    if (GROUP === "SA") {
        document.getElementById("saChat").appendChild(div);
        scrollToBottom("saChat");
    } else {
        const clone = div.cloneNode(true);
        document.getElementById("mentorMessages").appendChild(div);
        document.getElementById("devilMessages").appendChild(clone);
        scrollToBottom("mentorMessages");
        scrollToBottom("devilMessages");
    }
}

function scrollToBottom(elementId) {
    const el = document.getElementById(elementId);
    if (el) el.scrollTop = el.scrollHeight;
}

// ─── 知识路径可视化 ───
function toggleKG() {
    const modal = document.getElementById("kgModal");
    modal.classList.toggle("active");

    if (modal.classList.contains("active") && window.currentPathA) {
        renderPath("pathAContent", window.currentPathA, "a");
        renderPath("pathBContent", window.currentPathB, "b");
    }
}

function renderPath(containerId, path, type) {
    const container = document.getElementById(containerId);
    if (!path || path.length === 0) {
        container.innerHTML = "<span style=\"color:#999\">暂无路径数据</span>";
        return;
    }

    let html = "";
    path.forEach((node, idx) => {
        let cls = "kg-node";
        if (idx === 0) cls += " lca";  // 首节点为LCA
        else if (idx === path.length - 1) cls += " diverge";  // 末节点为分歧点

        html += `<span class="${cls}">${node}</span>`;
        if (idx < path.length - 1) {
            html += `<span class="kg-arrow">→</span>`;
        }
    });
    container.innerHTML = html;
}

// ─── 键盘快捷键 ───
document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
        const modal = document.getElementById("kgModal");
        if (modal.classList.contains("active")) {
            toggleKG();
        }
    }
});
