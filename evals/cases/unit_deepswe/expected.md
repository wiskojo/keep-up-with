# unit_deepswe expected behavior

This run injects one Reddit event about the DeepSWE announcement.

Expected outcome:

- The agent treats this as a real story, not a throwaway DM.
- It fetches the Reddit thread and source material behind DeepSWE.
- It explains what DeepSWE is in plain English.
- It uses source visuals if the benchmark page or post provides useful charts/screenshots.
- It compares DeepSWE to nearby coding-agent evals only where that helps explain the delta.
- It avoids dumping benchmark plumbing or internal tool details.
- It publishes into the most appropriate topic channel, likely `ai.evals`.
- The final output is readable as a user-facing update or thread.
