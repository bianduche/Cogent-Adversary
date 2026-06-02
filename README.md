# Cogent-Adversary

A Cognitive Dissonance-Adaptive Control Framework for Adversarial Dual-Agent Tutoring in Engineering Education.

This repository contains the complete experimental system accompanying the IEEE Transactions on Learning Technologies (TLT) submission.

## Overview

**Cogent-Adversary** is an adversarial dual-agent tutoring system that introduces two core innovations:

1. **CODA (Cognitive Dissonance-Adaptive Control)**: A closed-form real-time adaptive control law that dynamically regulates adversarial intensity $\alpha^*(t) \in [0, 1]$ based on the student's inferred cognitive state, grounded in cognitive-dissonance theory.
2. **KGAR + ACCL (Knowledge-Graph-Grounded Adversarial Reasoning with Consistency Check)**: A multi-path causal retrieval mechanism that constrains agent debates within structured causal paths of a domain knowledge graph, reducing graph-inconsistent or off-path claims in professional education.

A lightweight dynamic Bayesian network (**CSDI**) provides online cognitive-state inference to feed the controller.

## Architecture

```
┌─────────────────────────────────────────────────┐
│                 Teacher Dashboard                 │
├─────────┬─────────┬──────────────┬───────────────┤
│ Observer│Controller│   Executor   │    Safety     │
│  CSDI   │  CODA   │    KGAR      │    ACCL       │
│  (DBN)  │(Control)│ (Dual-Agent) │(Consistency)  │
├─────────┴─────────┴──────────────┴───────────────┤
│              Student Interface                     │
└─────────────────────────────────────────────────┘
```

- **CSDI (Observer)**: Infers cognitive state (Deep Confusion, Surface Understanding, Overconfidence, True Mastery) from interaction features via a 4-state DBN with hand-written NumPy forward algorithm.
- **CODA (Controller)**: Computes $\alpha^*(t)$ using a one-step receding-horizon formulation that tracks an inverted-U pedagogical reference trajectory $D_{ref}(t)$.
- **KGAR (Executor)**: Retrieves dual causal paths from a 200-node welding-defect knowledge graph, assigning one path to the Socratic Mentor agent and the other to the Devil's Advocate agent.
- **ACCL (Safety)**: Verifies that both agents' claims share a lowest common ancestor (LCA) in the knowledge graph, rejecting off-path claims with a fixed deviation threshold $\theta = 0.2$.

## Experimental Design

A stratified randomized pre-test–post-test–delayed-test study with four conditions ($N = 72$ completers) over a two-week, 10-session welding-defect curriculum:

| Group | Condition | Adversarial Intensity | Description |
|-------|-----------|----------------------|-------------|
| **SA** | Single-Agent | $\alpha = 0$ | Mentor only, no Devil's Advocate |
| **FA** | Fixed Dual-Agent | $\alpha = 0.5$ | Static intensity, no adaptation |
| **RA** | Rule-Based Adaptive | $\alpha$ heuristic | ±0.1 adjustment per answer correctness |
| **CA** | CODA-Adaptive | $\alpha^*(t)$ closed-form | Cognitive-dissonance-driven control |

## Key Results

| Metric | SA | FA | RA | CA |
|--------|----|----|----|----|
| Knowledge T1 (0–100) | 62.1 | 68.9 | 71.8 | **76.5** |
| Reasoning T1 (0–50) | 26.8 | 31.0 | 34.2 | **37.9** |
| NASA-TLX Mean | 44.5 | 68.3 | 61.5 | **57.8** |
| Factual Error Rate (%) | 5.2 | 8.1 | 5.7 | **4.1** |

- CA outperformed SA ($d = 1.12$), FA ($d = 0.89$), and RA ($d = 0.64$) on knowledge acquisition ($p < .001$).
- KGAR+ACCL reduced factual error rate by 49.4% compared to unconstrained debate (CA–no-KG ablation: 7.1%).
- CA maintained stable NASA-TLX within the Optimal Challenge Zone (50–65), while FA showed volatile spikes exceeding the overload threshold (75).

## Tech Stack

- **Backend**: Python 3.10+ / Flask / Flask-SocketIO
- **Database**: SQLite3 (single-file: `experiment.db`)
- **LLM**: OpenAI GPT-4o-mini (API)
- **Knowledge Graph**: NetworkX (in-memory, ~200 nodes, ~600 edges)
- **Frontend**: HTML5 + Vanilla JS + Socket.IO-client
- **NLP**: jieba (tokenization), sentence-transformers (semantic embeddings)

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Key

Edit `config.json`:

```json
{
    "openai_api_key": "sk-your-key-here",
    "model": "gpt-4o-mini",
    "max_retries": 3,
    "csdi_params": "csdi_params.json"
}
```

### 3. Launch Server

```bash
python app.py
```

### 4. Access the System

- **Student Interface**: `http://localhost:5000/?group=CA&sid=S001`
  - `group`: SA / FA / RA / CA
  - `sid`: Student ID (S001–S072)
- **Teacher Dashboard**: `http://localhost:5000/teacher`

## Database Schema

| Table | Description |
|-------|-------------|
| `logs` | Core interaction logs (turns, utterances, agent roles) |
| `students` | Participant demographics and group assignment |
| `tlx` | NASA-TLX per-session cognitive load records |
| `interviews` | Qualitative post-experiment interview transcripts |
| `alpha_history` | RA group $\alpha(t)$ trajectory for analysis |

## Core Modules

| Module | File | Function |
|--------|------|----------|
| CSDI | `modules/CSDI.py` | Cognitive-state dynamic inference (hand-written NumPy forward algorithm, no hmmlearn) |
| CODA | `modules/CODA.py` | Closed-form adaptive control law for adversarial intensity |
| KGAR | `modules/KGAR.py` | Multi-path causal retrieval from knowledge graph |
| ACCL | `modules/ACCL.py` | Adversarial consistency check (jieba entity extraction, LCA verification) |

## Design Constraints

- Frontend: pure HTML + vanilla JavaScript (no React/Vue/Angular)
- Knowledge graph: NetworkX in-memory (no Neo4j)
- CSDI: hand-written forward algorithm (no hmmlearn)
- All Chinese text: UTF-8 encoding
- LLM calls: retry mechanism (max 3 attempts)
- Student IDs: anonymized (S001–S072)
- NASA-TLX: mandatory per-session (blocks next session if incomplete)

## File Structure

```
app.py                  # Main Flask backend
modules/
  __init__.py
  CSDI.py               # Cognitive-state dynamic inference
  CODA.py               # Cognitive dissonance-adaptive control
  KGAR.py               # Knowledge-graph-grounded adversarial reasoning
  ACCL.py               # Adversarial consistency check
templates/
  index.html            # Student interface (split-panel debate view)
  teacher.html          # Teacher monitoring dashboard
  survey.html           # NASA-TLX questionnaire
static/
  css/style.css
  js/main.js
config.json             # API configuration
csdi_params.json        # CSDI transition/emission parameters
welding_kg.graphml      # Welding-defect knowledge graph (GraphML)
requirements.txt        # Python dependencies
README.md               # This file
```

## Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| $\eta$ | 0.35 | Conflict-gain coefficient (fitted via teacher gold-standard) |
| $\delta$ | 0.28 | Knowledge-relief coefficient |
| $D_{low}$ | 0.3 | Baseline dissonance reference |
| $D_{peak}$ | 0.7 | Peak dissonance reference |
| $\theta$ | 0.2 | ACCL deviation threshold |
| $\lambda$ | $\to 0$ | Control regularization weight |

## Citation

If you use this system in your research, please cite:

```bibtex
@article{cogent-adversary,
  title   = {Cogent-Adversary: A Cognitive Dissonance-Adaptive Control
             Framework for Adversarial Dual-Agent Tutoring in
             Engineering Education},
  author  = {Anonymous Authors},
  journal = {IEEE Transactions on Learning Technologies},
  year    = {2026},
  note    = {Under review}
}
```

## Data Availability

The datasets generated and analyzed during this study, along with the source code, prompt templates, and knowledge-graph triples, are publicly available in this repository to facilitate replication.

## License

This project is released for academic and research purposes. See repository for license details.
