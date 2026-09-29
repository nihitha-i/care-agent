Task eval 'v1': 20 tasks x 3 runs, judge gpt-4o

Summary (mean / min / max across runs; % except counts, seconds, steps)

|      |   task_success |   tool_selection |   approval_correct |   side_effects_ok |   answer_correct |   unrequested_writes |   avg_latency_s |   avg_steps |
|:-----|---------------:|-----------------:|-------------------:|------------------:|-----------------:|---------------------:|----------------:|------------:|
| mean |           63.3 |             93.3 |                100 |               100 |               70 |                    0 |             3.4 |         2.1 |
| min  |           55   |             90   |                100 |               100 |               60 |                    0 |             3.3 |         2   |
| max  |           70   |             95   |                100 |               100 |               80 |                    0 |             3.4 |         2.1 |

Weakest tasks

| task           |   success_% |
|:---------------|------------:|
| update_addr_1  |           0 |
| appeal         |           0 |
| denial_why     |           0 |
| email_summary  |           0 |
| small_talk     |           0 |
| send_support   |          33 |
| cardiac_rehab  |          67 |
| denied_explain |          67 |
