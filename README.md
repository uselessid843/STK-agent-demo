# STK Agent Demo
### Construction Daily Report Agent — Built by Sean Kenealy

A fully deployed AI agent that processes field submissions from construction supers and workers, structures them into daily PM reports, tracks submission compliance, sends reminders, and generates weekly summaries — with LangSmith observability and a structured eval system built in from day one.

**Live demo:** [stk-agent-demo.vercel.app](https://stk-agent-demo.vercel.app)

---

## What This Agent Does

Construction job sites generate unstructured field notes every day — voice memos, text messages, quick updates from supers. PMs spend hours turning that raw input into structured reports. This agent does it in seconds.

**Four capabilities:**

| Capability | What it does |
|---|---|
| Daily report | Processes raw field submissions and answers 7 structured PM questions |
| Submission compliance | Checks who has and hasn't reported in by end of day |
| Reminders | Sends targeted reminders to missing submitters with contact info |
| Weekly summary | Aggregates all daily reports into a PM-level week-in-review |

**Two user roles:**

- **Supers / Field Workers** — submit daily notes via a mobile-friendly form
- **Project Managers** — query the agent via chat, see submission status, rate responses

---

## Why I Built This

I built this project to close a gap I kept running into as an AI PM: I could spec and prioritize AI features, but I couldn't read a LangSmith trace, debug a prompt failure, or measure whether a change actually improved the agent. I wanted to understand the full stack — not at a surface level, but well enough to work alongside the engineers building it.

This project covers everything I needed to learn:

- Agent architecture (LLM + tools + orchestration)
- Prompt engineering with measurable iteration
- LangSmith observability and trace reading
- LLM-as-judge evaluations with blocking thresholds
- Deployment to a shareable URL with real user feedback collection

---

## Tech Stack

| Layer | Technology |
|---|---|
| Agent framework | LangGraph + LangChain |
| LLM | Claude (claude-opus-4-5) via Anthropic API |
| Observability | LangSmith |
| Backend | Python + Flask |
| Frontend | Vanilla HTML/CSS/JS |
| Deployment | Vercel |
| Feedback loop | Thumbs up/down → LangSmith feedback API |

---

## Project Structure

```
STK_agent_demo/
├── agent.py          # LLM initialization, system prompt, agent executor
├── tools.py          # Four tool functions the agent can call
├── database.py       # Fake data store with 15 submissions across 5 days
├── app.py            # Flask server with chat, submit, status, feedback endpoints
├── main.py           # Terminal chat loop for local testing
├── static/
│   └── index.html    # Role selector + Super form + PM dashboard
├── tests/
│   ├── eval_dataset.json   # 10 input/output eval cases
│   └── eval.py             # LLM-as-judge evaluator with blocking threshold
├── requirements.txt
└── vercel.json
```

---

## How the Agent Works

Every user message runs through this loop:

```
User input
    ↓
Claude reads input + system prompt + available tools
    ↓
Claude decides: answer directly, or call a tool?
    ↓
Tool runs against the fake database → result returned to Claude
    ↓
Claude decides: done, or call another tool?
    ↓
Final structured response returned to user
```

The LLM never touches data directly. It only decides which tool to call and what to do with what the tool returns. Tools are the only thing that touches real data.

---

## The Eval System

This is the part I'm most proud of. Instead of shipping prompt changes based on vibes, every change goes through a structured eval before it ships.

**5 evaluation dimensions:**

| Dimension | What it measures |
|---|---|
| Correctness | Did it answer all relevant PM questions? |
| Groundedness | Did it only use data from submissions — no hallucinations? |
| Completeness | Did it flag missing info explicitly rather than skipping it? |
| Safety | Did it surface safety incidents when present? |
| Submission compliance | Did it identify missing submitters when relevant? |

**Blocking threshold:** 4.0/5 average. Below this, the agent doesn't ship.

**Run evals:**
```bash
python3 tests/eval.py
```

**Eval progression across prompt iterations:**

| Version | Pass rate | What changed |
|---|---|---|
| v1 — initial | 30% (3/10) | Baseline — no attribution, no compliance header |
| v2 — prompt fix | 90% (9/10) | Added submitter attribution and submission status line |
| v3 — judge fix | 100% (10/10) | Calibrated judge criteria for compliance query types |

The jump from 30% to 100% happened across two prompt iterations. The third iteration fixed the judge, not the agent — an important distinction that only became clear from reading the failure reasons, not just the scores.

---

## Setup

**Prerequisites:** Python 3.9+, Node.js (for pptxgenjs if needed), Anthropic API key, LangSmith API key

**1. Clone and set up environment:**
```bash
git clone https://github.com/uselessid843/STK-agent-demo.git
cd STK-agent-demo
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**2. Create `.env` file:**
```
ANTHROPIC_API_KEY=your-key-here
LANGCHAIN_API_KEY=your-langsmith-key-here
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=schedule-health-agent
```

**3. Run locally:**
```bash
python3 app.py
```
Open `http://127.0.0.1:8080` in your browser.

**4. Run evals:**
```bash
python3 tests/eval.py
```

---

## The Fake Database

The agent runs against a fake database (`database.py`) covering one week of construction activity — 15 submissions across 5 days, 3 submitters.

Edge cases covered:
- Missing submission (Janet Wu, Monday and Friday) → triggers reminder
- Weather delay (Wednesday) → full crew sent home early
- Safety near-miss (Wednesday) → PPE violation caught in time
- Missing crew count (Thursday) → agent flags the gap explicitly
- Lumber shortage (Thursday) → supplier follow-up tracked
- Ahead of schedule (Friday) → Ray Delgado's framing crew running +1 day

---

## Feedback Loop

Every agent response in the UI has a thumbs up/down button. Ratings write directly to LangSmith via the feedback API, attached to the exact trace that generated the response.

Triage workflow for thumbs down:
1. Open LangSmith → Tracing
2. Find the matching trace by timestamp
3. Read the full reasoning chain in the Output tab
4. Decide: real failure or false negative?
5. Tag with failure category: `agent-confident-wrong`, `agent-unhelpful-vague`, or `agent-ignored-question`
6. Real failures → prompt fix → re-run evals → push

---

## What I Learned

**On agent architecture:** The docstring on each tool function is not documentation — it's the instruction Claude reads to decide whether to call that tool. Vague docstrings lead to wrong tool selection. Treat every docstring like a micro-prompt.

**On evals:** Eval failures are not always agent failures. Reading the failure reasons — not just the scores — is what tells you whether to fix the prompt or fix the judge.

**On debugging:** The moment you can read a LangSmith trace fluently — user input → LLM reasoning → tool call → tool output → final response — you can find any agent failure in under 2 minutes. That's the skill worth building.

**On prompt iteration:** `temperature=0` is essential for testable agents. You can't measure the impact of a prompt change if the model gives different answers every run.

---

## What I'd Build Next

- **Real database connection** — replace the fake data with a Postgres schema that persists field submissions across sessions
- **Photo/voice input** — use Claude's vision API to process actual site photos and Whisper for voice transcription
- **Slack integration** — route reminders to Slack DMs instead of printing to terminal
- **Automated eval runs in CI** — run evals on every push, block merge if pass rate drops below threshold
- **Multi-project support** — extend the data model to handle multiple job sites with per-project agent context

---

## About

Built by **Sean Kenealy**, Product Manager at [Outbuild](https://outbuild.com) — a construction scheduling platform for general contractors and specialty trades.

This project was built as a hands-on learning exercise in AI agent development, observability, and evaluation — the technical foundations every AI PM should understand, not just talk about.

[LinkedIn](https://linkedin.com/in/seankenealy) · [GitHub](https://github.com/uselessid843)
