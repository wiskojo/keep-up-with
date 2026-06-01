# Memory And Workspace

Read this before updating durable memory or creating medium/deep research files.

## Memory Files

`USER.md` is for stable user context:

- interests, goals, recurring topics, and watch areas
- communication preferences
- explicit likes, dislikes, and correction history
- long-lived constraints that should shape future decisions

`MEMORY.md` is for operational memory:

- source-quality lessons
- durable comparison baselines
- recurring entities, projects, and stories
- things to track more or less often
- workflow improvements learned from feedback

Do not store secrets, tokens, credentials, private keys, or raw sensitive payloads in either file.

## Update Rules

- Update memory only when the fact should affect future work.
- Keep entries short and dated when timing matters.
- Prefer specific lessons over vague preferences.
- Do not copy event feeds into memory. Events already live in durable history.

## Thread Workspace Structure

For medium and deep dives, keep working files under `threads/`:

```text
threads/
  story-slug/
    notes.md
    sources.md
    output.md
    artifacts/
```

Use lowercase hyphen-case for `story-slug`. Reuse an existing story folder when the update is part of the same story.

`notes.md` should track:

- current question
- timeline
- confirmed facts
- comparisons
- open questions

`sources.md` should track:

| Source | What it supports | Limits / uncertainty |
| --- | --- | --- |

`output.md` is the drafted thread or message.

`artifacts/` stores screenshots, figures, frames, charts, transcripts, source excerpts, or other files used in the output.

Do not create a thread workspace for a simple quick FYI unless the item is likely to become a continuing story.
