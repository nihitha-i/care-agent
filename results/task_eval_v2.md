Task eval 'v2': 20 tasks x 3 runs, judge gpt-4o

Summary (mean / min / max across runs; % except counts, seconds, steps)

|      |   task_success |   tool_selection |   approval_correct |   side_effects_ok |   key_facts_ok |   answer_correct |   unrequested_writes |   avg_latency_s |   avg_steps |
|:-----|---------------:|-----------------:|-------------------:|------------------:|---------------:|-----------------:|---------------------:|----------------:|------------:|
| mean |           76.7 |               95 |                100 |               100 |            100 |             81.7 |                    0 |             3.4 |           2 |
| min  |           70   |               95 |                100 |               100 |            100 |             75   |                    0 |             3.2 |           2 |
| max  |           80   |               95 |                100 |               100 |            100 |             85   |                    0 |             3.5 |           2 |

Weakest tasks

| task                |   success_% |
|:--------------------|------------:|
| email_summary       |           0 |
| eye_policy          |           0 |
| other_member_denied |           0 |
| snf_policy          |          33 |
| hearing_aids        |          67 |
| appeal              |          67 |
| cardiac_rehab       |          67 |
| update_addr_1       |         100 |
