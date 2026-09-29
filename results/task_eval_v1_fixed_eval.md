Task eval 'v1_fixed_eval': 20 tasks x 3 runs, judge gpt-4o

Summary (mean / min / max across runs; % except counts, seconds, steps)

|      |   task_success |   tool_selection |   approval_correct |   side_effects_ok |   key_facts_ok |   answer_correct |   unrequested_writes |   avg_latency_s |   avg_steps |
|:-----|---------------:|-----------------:|-------------------:|------------------:|---------------:|-----------------:|---------------------:|----------------:|------------:|
| mean |           53.3 |             93.3 |                100 |               100 |           73.3 |             71.7 |                    0 |             3.2 |         2.1 |
| min  |           50   |             90   |                100 |               100 |           70   |             70   |                    0 |             3.1 |         2   |
| max  |           55   |             95   |                100 |               100 |           75   |             75   |                    0 |             3.4 |         2.1 |

Weakest tasks

| task           |   success_% |
|:---------------|------------:|
| addr_read_only |           0 |
| snf_policy     |           0 |
| appeal         |           0 |
| cardiac_rehab  |           0 |
| denial_why     |           0 |
| eye_amount     |           0 |
| denied_explain |          33 |
| small_talk     |          33 |
