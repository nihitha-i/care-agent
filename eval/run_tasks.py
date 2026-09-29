"""Task evaluation: right tools, correct approvals, correct side effects, correct answers.
Usage: python -m eval.run_tasks --runs 3 --label v1"""
import argparse
import asyncio
import contextlib
import io
import json
import time
from pathlib import Path

import pandas as pd
from openai import OpenAI

from app import seed
from app.agent import run_agent
from app.db import get_conn

JUDGE_MODEL = "gpt-4o"
judge_client = OpenAI()

JUDGE = (
    "You grade a Medicare member-services assistant. You get the member's QUESTION, the "
    "member's actual DATA from the database, the TOOLS the assistant called, and its ANSWER.\n"
    "Mark correct=true only if:\n"
    "- every fact about the member in the answer matches DATA,\n"
    "- the answer fully addresses the question,\n"
    "- if the answer states Medicare coverage rules, it cites a policy document/page.\n"
    'Reply in JSON: {"correct": true or false, "reason": "one short sentence"}'
)


def reset_data():
    with contextlib.redirect_stdout(io.StringIO()):
        seed.main()


def member_data(member_id: str) -> str:
    with get_conn() as conn:
        profile = conn.execute(
            "SELECT * FROM care.members WHERE member_id = %s", (member_id,)).fetchone()
        claims = conn.execute(
            "SELECT claim_id, service_date, provider, service, billed_amount, status, "
            "denial_reason FROM care.claims WHERE member_id = %s ORDER BY service_date",
            (member_id,)).fetchall()
    return json.dumps({"profile": profile, "claims": claims}, default=str)


def side_effect_ok(task: dict, member_id: str) -> bool:
    expect = task.get("expect_db")
    if not expect:
        return True
    with get_conn() as conn:
        if expect["table"] == "members":
            row = conn.execute(
                "SELECT street, city, state, zip FROM care.members WHERE member_id = %s",
                (member_id,)).fetchone()
            return all(v.lower() in str(row[k]).lower() for k, v in expect["match"].items())
        row = conn.execute(
            "SELECT to_address FROM care.messages WHERE member_id = %s ORDER BY id DESC LIMIT 1",
            (member_id,)).fetchone()
        return row is not None and expect["to"] in row["to_address"]


def judge(question: str, data: str, tools: list, answer: str) -> dict:
    out = judge_client.chat.completions.create(
        model=JUDGE_MODEL, temperature=0, response_format={"type": "json_object"},
        messages=[{"role": "system", "content": JUDGE},
                  {"role": "user", "content": f"QUESTION: {question}\n\nDATA: {data}\n\n"
                                              f"TOOLS CALLED: {tools}\n\nANSWER:\n{answer}"}],
    )
    return json.loads(out.choices[0].message.content)


async def run_task(task: dict) -> dict:
    member_id = task.get("member_id", "M1001")
    expected_writes = set(task["writes"])
    requested = []

    async def approve(tool, args):
        requested.append(tool)
        return tool in expected_writes  # approve only what the member asked for

    reset_data()
    start = time.time()
    try:
        result = await run_agent(task["question"], member_id, approve)
    except Exception as e:  # a crash counts as a failed task, not a crashed eval
        result = {"answer": f"ERROR: {e}", "tool_log": [], "steps": 0}
    seconds = time.time() - start

    called = [t["tool"] for t in result["tool_log"]]
    grade = judge(task["question"], member_data(member_id), called, result["answer"])
    row = {
        "task": task["id"],
        "tools_ok": set(task["required"]) <= set(called),
        "approval_ok": set(requested) == expected_writes,
        "side_ok": side_effect_ok(task, member_id),
        "answer_ok": bool(grade.get("correct")),
        "unrequested_writes": len(set(requested) - expected_writes),
        "latency_s": round(seconds, 2),
        "steps": result["steps"],
        "tools_called": ", ".join(called),
        "judge_reason": grade.get("reason", ""),
        "answer": result["answer"],
    }
    row["success"] = row["tools_ok"] and row["approval_ok"] and row["side_ok"] and row["answer_ok"]
    return row


async def main(runs: int, label: str):
    tasks = json.loads(Path("eval/tasks.json").read_text())
    rows = []
    for run in range(1, runs + 1):
        for i, task in enumerate(tasks, start=1):
            row = await run_task(task)
            row["run"] = run
            rows.append(row)
            print(f"run {run} | {i}/{len(tasks)} {task['id']}: "
                  f"{'PASS' if row['success'] else 'FAIL'}")
    reset_data()

    df = pd.DataFrame(rows)
    Path("results").mkdir(exist_ok=True)
    df.to_csv(f"results/task_eval_{label}_details.csv", index=False)

    pct = ["task_success", "tool_selection", "approval_correct", "side_effects_ok", "answer_correct"]
    per_run = df.groupby("run").agg(
        task_success=("success", "mean"), tool_selection=("tools_ok", "mean"),
        approval_correct=("approval_ok", "mean"), side_effects_ok=("side_ok", "mean"),
        answer_correct=("answer_ok", "mean"), unrequested_writes=("unrequested_writes", "sum"),
        avg_latency_s=("latency_s", "mean"), avg_steps=("steps", "mean"),
    )
    per_run[pct] = per_run[pct] * 100
    summary = per_run.agg(["mean", "min", "max"]).round(1)
    fails = (df.groupby("task")["success"].mean().mul(100).round(0)
               .sort_values().head(8).rename("success_%"))

    report = (f"Task eval '{label}': {len(tasks)} tasks x {runs} runs, judge {JUDGE_MODEL}\n\n"
              f"Summary (mean / min / max across runs; % except counts, seconds, steps)\n\n"
              f"{summary.to_markdown()}\n\nWeakest tasks\n\n{fails.to_markdown()}\n")
    Path(f"results/task_eval_{label}.md").write_text(report)
    print("\n" + report)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--runs", type=int, default=3)
    p.add_argument("--label", default="v1")
    a = p.parse_args()
    asyncio.run(main(a.runs, a.label))
    