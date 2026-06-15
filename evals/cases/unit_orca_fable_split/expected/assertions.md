# Expected: unit_orca_fable_split

- The agent's trajectory conforms strictly to the workflow described in `AGENTS.md`, `$keep-up-with` `SKILL.md`, and related references. The flow is effective and efficient.
- Recognize that the Reddit event contains two separable stories: Fable access/policy discussion and the Orca tool. Do not collapse them into one confusing message.
- If both parts are worth surfacing, publish them separately in the most appropriate places: Fable as an update to the relevant Fable/policy story, Orca as a tools story. If one part is already covered or too weak, dismiss it with that disposition.
- Orca coverage should inspect the repo and compare it only where useful to adjacent multi-agent or coding-workspace tools such as Herd, Conductor, or cmux.
- Orca output should include relevant source image attachment(s), usually the repo/README surface and a star-history chart if popularity or growth is mentioned.
- Keep each output short unless research finds enough distinct material for a thread. Avoid generic Fable recap, benchmark plumbing, or internal tool details.
