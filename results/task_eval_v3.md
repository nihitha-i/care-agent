Task eval 'v3': 20 tasks x 3 runs, judge gpt-4o

Summary (mean / min / max across runs; % except counts, seconds, steps)

|      |   task_success |   tool_selection |   approval_correct |   side_effects_ok |   key_facts_ok |   answer_correct |   unrequested_writes |   avg_latency_s |   avg_steps |
|:-----|---------------:|-----------------:|-------------------:|------------------:|---------------:|-----------------:|---------------------:|----------------:|------------:|
| mean |             90 |              100 |                100 |               100 |           96.7 |             93.3 |                    0 |             3.7 |         2.3 |
| min  |             85 |              100 |                100 |               100 |           95   |             90   |                    0 |             3.6 |         2.2 |
| max  |             95 |              100 |                100 |               100 |          100   |             95   |                    0 |             3.8 |         2.4 |

Weakest tasks

| task                |   success_% |
|:--------------------|------------:|
| cardiac_rehab       |           0 |
| snf_policy          |          67 |
| small_talk          |          67 |
| other_member_denied |          67 |
| addr_read_only      |         100 |
| update_addr_1       |         100 |
| send_support        |         100 |
| plan                |         100 |
