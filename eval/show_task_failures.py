"""Shows one example of each failing task: tools called, judge's reason, and the answer."""
import sys

import pandas as pd

label = sys.argv[1] if len(sys.argv) > 1 else "v1"
df = pd.read_csv(f"results/task_eval_{label}_details.csv")
failed = df[~df.success]

for task, group in failed.groupby("task"):
    r = group.iloc[0]
        checks = [c for c in ("tools_ok", "approval_ok", "side_ok", "facts_ok", "answer_ok") if not r[c]]
    print(f"=== {task}  (failed {len(group)}/{df[df.task == task].shape[0]} runs)")
    print(f"failed checks: {', '.join(checks)}")
    print(f"tools called:  {r.tools_called if isinstance(r.tools_called, str) else '(none)'}")
    print(f"judge reason:  {r.judge_reason}")
    print(f"answer:        {str(r.answer)[:350]}\n")