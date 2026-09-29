Task eval 'v1_stable': 20 tasks x 3 runs, judge gpt-4o

Summary (mean / min / max across runs; % except counts, seconds, steps)

|      |   task_success |   tool_selection |   approval_correct |   side_effects_ok |   key_facts_ok |   answer_correct |   unrequested_writes |   avg_latency_s |   avg_steps |
|:-----|---------------:|-----------------:|-------------------:|------------------:|---------------:|-----------------:|---------------------:|----------------:|------------:|
| mean |             75 |               95 |                100 |               100 |             90 |               85 |                    0 |             3.1 |         2.1 |
| min  |             75 |               95 |                100 |               100 |             90 |               85 |                    0 |             3.1 |         2.1 |
| max  |             75 |               95 |                100 |               100 |             90 |               85 |                    0 |             3.1 |         2.1 |

Weakest tasks

| task           |   success_% |
|:---------------|------------:|
| appeal         |           0 |
| cardiac_rehab  |           0 |
| denial_why     |           0 |
| snf_policy     |           0 |
| eye_policy     |           0 |
| addr_read_only |         100 |
| update_addr_1  |         100 |
| small_talk     |         100 |
