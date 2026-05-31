# Technical Dossier
## Construction Daily Report Agent
**Author:** Sean Kenealy, Product Manager — Outbuild
**Last updated:** May 2026

---

## Purpose

This document explains the design decisions behind the Construction Daily Report Agent — not what it does, but why it was built the way it was. It covers architecture choices, prompt design rationale, evaluation framework design, failure taxonomy, and honest retrospective.

Intended audience: hiring managers, technical leads, and AI PMs evaluating the depth of thinking behind the project.

---

## 1. Problem Framing

Construction job sites generate daily field notes from multiple supers and foremen. These notes are unstructured — voice memos, text messages, quick updates typed on a phone between tasks. Project managers need that information structured into a consistent format every day, covering 7 specific questions, before they can make scheduling decisions.

The manual process takes 30-60 minutes per PM per day. The failure mode is inconsistency — different supers provide different levels of detail, safety incidents get buried, and submission gaps go unnoticed until the PM follows up manually.

**The agent's job:** ingest raw field input → structure it → answer the 7 PM questions → flag gaps → track who submitted and who didn't → remind missing submitters → roll up weekly.

---

## 2. Architecture Decisions

### Why LangGraph over vanilla LangChain

LangGraph was chosen over a simple LangChain agent executor for one reason: the `should_continue` decision node. LangGraph makes the agent's looping logic explicit and observable — every decision to call another tool or stop is a named node in the graph, visible in LangSmith traces. This matters for debugging. When something goes wrong, you can see exactly where in the reasoning loop the failure occurred.

Vanilla LangChain agents hide this logic inside the executor. LangGraph exposes it.

### Why `temperature=0`

Evaluations require reproducibility. If the model gives different answers on the same input across runs, you can't measure whether a prompt change improved anything — the variance from temperature overwhelms the signal from the edit.

`temperature=0` makes the agent deterministic. Every prompt change produces a measurable delta. This is the foundation of a credible eval system.

### Why 4 tools and not more

Each tool maps to one user intent:

| Tool | Intent |
|---|---|
| `process_daily_submissions` | "Tell me what happened today" |
| `check_missing_submitters` | "Who hasn't reported in?" |
| `send_reminder` | "Follow up with missing people" |
| `generate_weekly_summary` | "Give me the week in review" |

More tools would have introduced routing ambiguity — the LLM would have needed to choose between tools that partially overlap. Fewer tools meant cleaner decisions and more predictable behavior. The docstring on each tool is the critical artifact: it's the instruction Claude reads to decide whether to call it. Vague docstrings cause wrong tool selection. Every docstring was written as a micro-prompt.

### Why a fake database instead of real data

The fake database (`database.py`) was designed to be realistic enough to produce meaningful traces but simple enough to reason about completely. Every record is known. Every edge case is intentional. This matters for eval design — you can't write a ground-truth eval dataset if you don't know what the correct answer is.

The fake data covers 5 specific edge cases:
- Missing submission (triggers reminder flow)
- Weather delay (tests delay extraction)
- Safety near-miss (tests safety surfacing)
- Missing crew count (tests gap flagging)
- Ahead of schedule (tests positive signal extraction)

Each edge case maps to a specific eval dimension.

---

## 3. Prompt Design Rationale

The system prompt went through 3 iterations. Each iteration was driven by eval scores, not intuition.

### What the final system prompt enforces

**Submission status header** — every daily report opens with "Submissions received: X of 3 — [name] not yet submitted." This was added after v1 evals showed submission_compliance scoring 2.4/5. The agent was answering correctly but not proactively surfacing the compliance picture. One line in the prompt fixed it.

**Submitter attribution** — every factual claim must be attributed by name: "Per Mike Torres: poured east foundation wall." This was added after groundedness scored 3/5 in v1. The agent was correct but unverifiable — the judge couldn't confirm whether facts came from submissions or were hallucinated. Attribution makes every claim traceable.

**Default date range** — "this week" defaults to 2026-05-19 to 2026-05-23. Without this, the agent asked users for date ranges on every vague time reference. Field supers don't want to type date strings. One line eliminated the clarification loop.

**Out-of-scope fallback** — if the user asks about something outside the agent's tools (weather, budget, personnel records), respond immediately with a clean "I don't have access to that." Without this, the agent attempted tool calls that never resolved, producing spinning traces in LangSmith.

---

## 4. Evaluation Framework

### Why LLM-as-judge

Human evaluation doesn't scale across prompt iterations. Running 10 eval cases manually after every prompt change takes 20+ minutes and introduces rater inconsistency. LLM-as-judge runs in 2-3 minutes, scores consistently, and explains every score in one sentence — which is more useful than a number alone.

The tradeoff: the judge can be wrong. This happened in v1, where the judge penalized correct agent behavior because its own criteria were miscalibrated. The fix was reading failure reasons, not just scores — and updating the judge prompt to handle compliance query types correctly.

### Why these 5 dimensions

| Dimension | Why it matters for this use case |
|---|---|
| Correctness | A PM report missing any of the 7 questions is incomplete — doesn't matter how well-written it is |
| Groundedness | Construction decisions based on hallucinated facts have real consequences |
| Completeness | Missing info flagged explicitly is better than missing info silently omitted |
| Safety | A near-miss buried in section 6 is a liability issue, not just a UX issue |
| Submission compliance | A report that looks complete but is missing a super's input is worse than no report |

### Why 4.0/5 as the blocking threshold

4.0/5 allows for minor gaps (a score of 4 on one dimension) while blocking anything with a major failure (a score of 2 or 3). It was calibrated against the baseline eval — at 4.0, the initial 30% pass rate correctly identified the two broken dimensions without being so strict that minor phrasing variations triggered failures.

### The distinction between agent failures and judge failures

This is the most important operational insight from building the eval system.

When an eval case fails, there are two possible causes:
1. The agent did something wrong
2. The judge criteria are wrong for that query type

In v1, eval_004 failed with groundedness: 3/5. The judge said it "couldn't verify the source data." But the agent had correctly called `check_missing_submitters` and returned Janet Wu's name, role, and phone number — data that can only come from the database. The agent was right. The judge was applying criteria designed for narrative reports to a compliance query.

The fix was updating the judge prompt, not the agent prompt. Getting this distinction wrong would have introduced a regression — "fixing" a prompt that wasn't broken.

**Rule:** always read the failure reason before deciding what to fix.

---

## 5. Observability Design

### Why LangSmith tracing matters

The agent produces different outputs depending on what the LLM decides to do at each step. Without traces, a wrong answer is opaque — you know something failed but not where or why. With traces, every failure has a location: was it the tool selection? The tool output? The final synthesis?

Every deployed response in the UI now writes feedback scores directly to LangSmith via the feedback API, attached to the exact trace that generated it. This closes the loop between user experience and system behavior.

### Triage workflow

For every thumbs down:
1. Find the matching trace by timestamp
2. Read the full output — don't just look at the score
3. Classify: real failure or false negative?
4. Tag with failure category
5. Real failures only → add to eval dataset → fix prompt → re-run evals

False negatives (correct responses that received thumbs down) are as important to identify as real failures. Acting on false negatives introduces regressions.

---

## 6. Failure Taxonomy

Three failure categories observed in production traces:

**`agent-confident-wrong`**
The agent answers with apparent confidence but gets facts wrong — wrong submitter, wrong date, wrong crew count. Root cause is usually insufficient grounding instructions in the system prompt. Fix: tighten attribution requirements.

**`agent-unhelpful-vague`**
The agent gives a technically correct but useless response — "there were some delays this week" instead of naming the delay, the cause, and the impact. Root cause is usually system prompt instructions that are too general. Fix: add specificity requirements to the relevant section.

**`agent-ignored-question`**
The agent answers a different question than the one asked, or asks a clarifying question instead of using available defaults. Root cause is usually missing default context in the system prompt or ambiguous tool docstrings. Fix: add explicit defaults or sharpen the docstring.

---

## 7. Honest Retrospective

### What worked well
- Building evals before sharing with users meant the first external feedback was on a 100%-passing agent, not a broken one
- LangGraph's explicit graph structure made debugging significantly faster than a black-box executor
- The fake database edge cases mapped almost perfectly to real failure modes discovered in production traces

### What I'd do differently
- **Start with the eval dataset before writing the system prompt.** Writing evals first forces you to define what "correct" means before you build the thing that's supposed to be correct. I wrote the prompt first and retrofitted evals — which meant the first eval run was as much a test of my eval criteria as my agent.
- **Add the out-of-scope fallback on day one.** The spinning trace from "what's the weather" was predictable. Any question outside the tool set should have been handled from the first prompt version.
- **Use a smaller model for tool selection.** Claude Opus is used for every step including simple tool routing decisions. A cheaper model (Haiku) for the initial tool selection step with Opus only for final synthesis would reduce latency and cost significantly.

### What I'd build next
1. Real database with persistent submissions across sessions
2. Photo input via Claude vision API — supers photograph site conditions instead of typing
3. Voice transcription via Whisper — supers leave voice notes, agent transcribes and structures
4. Slack integration for reminders — route to DMs instead of terminal output
5. Automated eval runs in CI — block merge if pass rate drops below threshold
6. Multi-project support — extend data model to handle multiple job sites

---

## 8. Key Metrics

| Metric | Value |
|---|---|
| Eval pass rate (final) | 100% (10/10) |
| Avg eval score (final) | 4.9/5 |
| Prompt iterations to 100% | 2 |
| Judge calibration fixes | 1 |
| Deployment target | Vercel (serverless Python) |
| LangSmith traces per session | 3-5 |
| Avg agent latency | ~11s (Claude Opus, 2 tool calls) |
| Cost per query | ~$0.03 |

---

*This dossier is a living document. It is updated after every prompt iteration, eval run, and production failure. See CHANGELOG.md for the full iteration history.*
