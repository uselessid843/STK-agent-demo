import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from anthropic import Anthropic
from agent import create_agent
from dotenv import load_dotenv

load_dotenv()

client = Anthropic()

BLOCKING_THRESHOLD = 4.0  # out of 5 — below this, agent fails eval

JUDGE_PROMPT = """You are evaluating a construction daily report AI agent.

The agent received this input:
{input}

The agent produced this output:
{output}

Evaluate the output on these 5 dimensions. Score each 1-5.
Return ONLY a JSON object, no other text:

{{
  "correctness": {{
    "score": <1-5>,
    "reason": "<one sentence>"
  }},
  "groundedness": {{
    "score": <1-5>,
    "reason": "<one sentence>"
  }},
  "completeness": {{
    "score": <1-5>,
    "reason": "<one sentence>"
  }},
  "safety": {{
    "score": <1-5>,
    "reason": "<one sentence>"
  }},
  "submission_compliance": {{
    "score": <1-5>,
    "reason": "<one sentence>"
  }}
}}

Scoring guide:
5 = Perfect. Fully addressed with no issues.
4 = Good. Minor gaps but nothing critical.
3 = Partial. Key information present but incomplete.
2 = Poor. Major gaps or errors.
1 = Fail. Missing entirely or factually wrong.

Correctness: Did it answer all relevant PM questions for this type of request?
Groundedness: Did it only use information from the submissions, no invented facts? For compliance and reminder queries, if the agent returned specific names, roles, and phone numbers that match expected submitter records (e.g. Janet Wu, Site Foreman, 603-555-0163), score 5 — this data can only come from the database, not be hallucinated. Only score below 5 if the agent invented facts not present in any submission.
Completeness: Did it flag missing or incomplete information explicitly?
Safety: Did it surface safety incidents when present AND relevant to the query type. If the query is purely a compliance or reminder check, safety is not applicable — score 5.
Submission compliance: Did it identify missing submitters when relevant?"""


def run_agent(input_text):
    """Run the agent and return its response."""
    agent = create_agent()
    result = agent.invoke({
        "messages": [{"role": "user", "content": input_text}]
    })
    return result["messages"][-1].content


def judge_output(input_text, output_text):
    """Use Claude as a judge to score the agent output."""
    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": JUDGE_PROMPT.format(
                input=input_text,
                output=output_text
            )
        }]
    )
    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


def run_evals():
    """Run all eval cases and report results."""
    with open("tests/eval_dataset.json") as f:
        dataset = json.load(f)

    results = []
    passed = 0
    failed = 0

    print("\n=== Running Evaluations ===\n")

    for case in dataset:
        print(f"Running {case['id']}: {case['notes']}")

        # Get agent output
        output = run_agent(case["input"])

        # Judge it
        scores = judge_output(case["input"], output)

        # Calculate average score
        avg = sum(s["score"] for s in scores.values()) / len(scores)

        # Check threshold
        status = "PASS" if avg >= BLOCKING_THRESHOLD else "FAIL"
        if status == "PASS":
            passed += 1
        else:
            failed += 1

        results.append({
            "id": case["id"],
            "status": status,
            "avg_score": round(avg, 2),
            "scores": scores,
            "input": case["input"],
            "output": output,
        })

        print(f"  Status: {status} | Avg score: {avg:.2f}/5")
        for dim, data in scores.items():
            print(f"  {dim}: {data['score']}/5 — {data['reason']}")
        print()

    # Summary
    print("=== Eval Summary ===")
    print(f"Total: {len(dataset)} | Passed: {passed} | Failed: {failed}")
    print(f"Pass rate: {round(passed/len(dataset)*100)}%")

    # Save results
    with open("tests/eval_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nResults saved to tests/eval_results.json")

    # Blocking assertion
    if failed > 0:
        print(f"\n❌ EVAL FAILED — {failed} case(s) below threshold of {BLOCKING_THRESHOLD}/5")
        print("Do not ship this version.")
        sys.exit(1)
    else:
        print(f"\n✅ ALL EVALS PASSED — safe to ship")


if __name__ == "__main__":
    run_evals()