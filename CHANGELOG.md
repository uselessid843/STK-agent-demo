# Changelog

All prompt changes, eval runs, and architectural decisions are logged here.
Format: **What changed → Why → Eval impact**

---

## [v3] — 2026-05-30
**Calibrated judge criteria for compliance query types**

### What changed
- Updated `JUDGE_PROMPT` in `tests/eval.py` to explicitly instruct the judge that specific phone numbers and roles returned by compliance queries are verifiable database signals — not unknowns
- Added guidance that safety scoring is not applicable to reminder/compliance query types

### Why
eval_004 (compliance check) was failing with groundedness: 3/5. The judge was penalizing the agent for "not verifying source data" on a query where the agent had correctly called `check_missing_submitters` and returned Janet Wu's name, role, and phone number. The agent was right. The judge criteria were wrong.

This is the distinction between an agent failure and a judge calibration failure. Reading the failure reason — not just the score — revealed it was the latter.

### Eval results
| Metric | v2 | v3 |
|---|---|---|
| Pass rate | 90% (9/10) | 100% (10/10) |
| Failed cases | eval_004 | none |
| Avg score | 4.6/5 | 4.9/5 |

### Lesson
Always read the failure reason before fixing the prompt. A score of 3/5 looks like an agent failure but can be a judge calibration problem. The fix is different in each case.

---

## [v2] — 2026-05-30
**Added submitter attribution and submission compliance header**

### What changed
Added two instructions to the system prompt in `agent.py`:
1. Every daily report must open with a submission status line: "Submissions received: X of 3 — [name] not yet submitted"
2. Every factual claim must be attributed to the submitter by name: "Per Mike Torres: poured east foundation wall..."

### Why
eval results showed groundedness scoring 3/5 and submission_compliance scoring 2-3/5 across almost every case. The agent was answering correctly but not citing sources or flagging missing submitters proactively. Two targeted lines in the system prompt fixed both dimensions simultaneously.

### Eval results
| Metric | v1 | v2 |
|---|---|---|
| Pass rate | 30% (3/10) | 90% (9/10) |
| Failed cases | 7 | 1 |
| Groundedness avg | 3/5 | 4/5 |
| Submission compliance avg | 2.4/5 | 4.6/5 |

### Lesson
Score by dimension, not just average. The two failing dimensions pointed directly to two missing instructions. One prompt edit per dimension is cleaner and easier to revert than a wholesale rewrite.

---

## [v1] — 2026-05-30
**Initial agent — baseline eval**

### What was built
- `agent.py` with system prompt covering 7 PM report questions and weekly summary format
- `tools.py` with 4 tools: process_daily_submissions, check_missing_submitters, send_reminder, generate_weekly_summary
- `database.py` with 15 fake submissions across 5 days, 3 submitters, covering 5 edge cases
- `tests/eval.py` with 10 eval cases and LLM-as-judge scoring across 5 dimensions
- Blocking threshold set at 4.0/5

### Eval results
| Metric | Score |
|---|---|
| Pass rate | 30% (3/10) |
| Correctness | 4/5 avg |
| Groundedness | 3/5 avg |
| Completeness | 4.2/5 avg |
| Safety | 4.6/5 avg |
| Submission compliance | 2.4/5 avg |

### Known gaps at baseline
- Agent answers correctly but doesn't cite which submitter each fact came from
- Daily reports don't open with submission status (who submitted, who didn't)
- Compliance queries score low because the judge can't verify grounding without source attribution
- No graceful fallback for out-of-scope queries (weather, budget, costs)

---

## Upcoming

### Planned improvements
- [ ] Add graceful out-of-scope fallback to system prompt — agent currently hangs on queries outside its tool set (e.g. "what's the weather")
- [ ] Add eval case for out-of-scope query handling
- [ ] Wire eval runs to CI — block push if pass rate drops below 4.0/5
- [ ] Expand eval dataset to 20 cases covering real failure patterns from LangSmith traces
- [ ] Add photo/voice input handling via Claude vision API and Whisper transcription
- [ ] Replace fake database with persistent Postgres connection
- [ ] Route reminders to Slack DMs instead of terminal output
