# Cogent-Adversary 实验系统

基于Web的双智能体教学实验系统，用于支持IEEE TLT期刊论文实验。

## 技术栈
- **后端**: Python 3.10+ + Flask + Flask-SocketIO
- **数据库**: SQLite3 (单文件，experiment.db)
- **LLM**: OpenAI GPT-4o-mini
- **知识图谱**: NetworkX (内存加载)
- **前端**: HTML5 + Vanilla JS + Socket.IO-client
- **分词**: jieba
- **向量化**: sentence-transformers

## 快速启动

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置API密钥
编辑 `config.json`，填入你的OpenAI API Key：
```json
{
    "openai_api_key": "sk-your-key-here",
    ...
}
```

### 3. 启动服务
```bash
python app.py
```

### 4. 访问系统
- **学生界面**: `http://localhost:5000/?group=CA&sid=S001`
  - 参数 `group`: SA/FA/RA/CA
  - 参数 `sid`: 学生ID (S001-S072)
- **教师监控面板**: `http://localhost:5000/teacher`

## 4组实验说明
| 组别 | 代号 | 对抗强度 | 说明 |
|------|------|----------|------|
| SA | 单Agent | α=0 | 仅Mentor，无Devil |
| FA | 固定对抗 | α=0.5 | 固定强度 |
| RA | 规则自适应 | α动态 | 根据答题正误±0.1调整 |
| CA | CODA控制 | α解析解 | 基于认知失调模型计算 |

## 核心模块
- **CSDI** (`modules/CSDI.py`): 认知状态动态推断，手写numpy前向算法
- **CODA** (`modules/CODA.py`): 认知失调感知控制，计算最优对抗强度
- **KGAR** (`modules/KGAR.py`): 知识图谱参数检索，路径选择
- **ACCL** (`modules/ACCL.py`): 对抗一致性校验，jieba实体提取

## 数据库Schema
- `logs`: 核心交互日志
- `students`: 被试信息
- `tlx`: NASA-TLX逐课记录
- `interviews`: 质性访谈
- `alpha_history`: RA组alpha历史

## 关键约束
- 前端纯HTML+JS，禁止React/Vue/Angular
- 知识图谱用NetworkX内存加载，禁止Neo4j
- CSDI前向算法手写numpy，禁止hmmlearn
- 所有中文文本UTF-8编码
- LLM调用带重试机制（最多3次）
- 学生ID匿名（S001-S072）
- TLX问卷未填写阻断下一课时

## 文件清单
```
app.py              # 主后端
modules/
  __init__.py
  CSDI.py           # 认知状态推断
  CODA.py           # 对抗强度控制
  KGAR.py           # 知识图谱检索
  ACCL.py           # 一致性校验
templates/
  index.html        # 学生界面
  teacher.html      # 教师面板
  survey.html       # 问卷页面
static/
  css/style.css
  js/main.js
config.json         # 配置文件
welding_kg.graphml # 知识图谱
csdi_params.json   # CSDI参数
requirements.txt   # Python依赖
README.md          # 本文档
```
