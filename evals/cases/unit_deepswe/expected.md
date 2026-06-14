# unit_deepswe expected behavior

This run injects one Reddit event about the DeepSWE announcement.

Expected outcome:

- The agent treats this as a real story, not a throwaway DM.
- It fetches the Reddit thread and source material behind DeepSWE.
- The story is owned end to end by a real subagent; the orchestrator should dispatch, wait, and dismiss with the subagent/thread disposition instead of doing parallel research itself.
- `research/notes.md` is filled during the work before the thread is published, not written afterward as a recap.
- It explains what DeepSWE is in plain English.
- It inventories the source visuals and uses enough high-value charts/tables to cover the benchmark, not just one overview image. For this case, expect at least five well-cropped DeepSWE visuals from the blog/leaderboard, with no clipped text, adjacent prose, browser chrome, or loose horizontal framing.
- It compares DeepSWE to nearby coding-agent evals only where that helps explain the delta.
- It avoids dumping benchmark plumbing or internal tool details.
- It publishes into the most appropriate topic channel, likely `ai.evals`.
- The final output is readable as a user-facing update or thread.
