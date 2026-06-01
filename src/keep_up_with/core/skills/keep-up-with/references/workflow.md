# Workflow

Use this for anything beyond a quick reply. Quick FYI/BTW messages usually do not need a workspace folder.

## 1. Filter

Ask: what are the top things the user would want to know based on the event?

Choose the lightest useful response:

| Level | Use |
| --- | --- |
| Do nothing | Stale, repeated, irrelevant, already handled, or not useful. |
| Notify only | A quick FYI/BTW: one short message, usually with one link. |
| Medium research | Needs checking, context, comparison, or a thread update. |
| Deep research | Big story, major launch, paper, benchmark, controversy, policy move, or something likely to keep developing. |

## 2. Workspace

For medium/deep work, create one folder per story:

```text
threads/
  YYYY-MM-DD-HHMM-slug/
    research/
      checklist.md
      notes.md
      artifacts/
    output/
      output.md
      assets/
```

Use local time for `YYYY-MM-DD-HHMM`. Keep the slug short, lowercase, and hyphenated. Reuse the same folder for the same story.

`research/` is for internal legwork: notes, facts, timelines, comparisons, questions, source notes, screenshots, figures, transcripts, frames, tables, and excerpts.

`output/` is for the user-facing draft and assets that may be sent.

`research/checklist.md` is required. Create it from [checklist.md](checklist.md) when you create the workspace, then fill it in as you work. Do not mark an item done unless its evidence line names the source, artifact, message id, subagent result, or reason.

## 3. Research

Goal: understand the delta. Stop when more work is unlikely to change what you would say.

For medium/deep work, dispatch coherent groups of work to subagents when subagents are available. A subagent should own one story/thread or one research line end to end. If new events arrive for that same story or line, send the update back to that subagent when possible. Keep non-overlapping work moving while subagents run. If you do not delegate, record the reason in `research/checklist.md`.

Start broad, then go deep only where it matters:

- BFS: source, links, prior events, messages, threads, comments, comparable stories.
- DFS: verify a claim, inspect an artifact, compare a baseline, or find a correction.

Prefer primary sources: original posts, papers, model cards, repos, release notes, benchmark pages, datasets, author threads, talks, and official pages. Treat virality as a clue, not evidence.

Write the working state into `research/notes.md`. Save raw material in `research/artifacts/`.

## 4. Cross-reference

Relate the new information to what already exists:

- prior events and inbox items
- message history
- existing threads
- `USER.md` and `MEMORY.md`
- previous notes and artifacts
- similar launches, papers, repos, claims, or benchmarks

Mark what changed: new, continued, correction, contradiction, repeated discourse, or no real delta.

## 5. Highlights And Visuals

Pick the facts the user would care about most. Cut the rest.

Plan visuals before drafting a medium/deep thread. The usual shape is text, visual, text, visual, then sources. No visual is the exception, not the default.

Visuals can be screenshots, official figures, charts, compact tables, quoted excerpts, timelines, maps, comparison grids, frames, or source captures. Use them to clarify, verify, compare, or break up dense information. Do not use decorative visuals. Do not use generated images as evidence.

Put draft visuals or generated assets in `output/assets/`.

## 6. Draft

For a quick FYI/BTW:

- write a few plain sentences
- include the main link inline
- say what happened and what changed
- no headings, source dump, or thread structure

For a medium/deep thread, draft the full thread in `output/output.md`.

Organize the thread for scanning, not as a wall of text:

1. Opening post: background, what happened, what changed, and the main visual or visuals.
2. Highlight posts: one useful point per post, interleaved with visuals, tables, excerpts, or other assets.
3. Sources post: links and what each source supports.

Opening post:

- Background: who is involved, what the user needs to know about them, and when it happened.
- What happened / what it is: plain English, 2-4 short sentences.
- What's changed / new: the delta from prior story state, baseline, or comparable. Omit if there is no real delta.
- Main visual: use a screenshot, chart, figure, excerpt, timeline, map, or other visual that clarifies the story.

Highlight posts:

- Use the facts that matter most.
- Keep each post focused.
- Use short paragraphs, line breaks, bullets, tables, and sparing bold text so the thread is easy to scan.
- Add visuals, tables, or excerpts where they clarify, compare, verify, or keep dense material readable.
- For first-hand user experiences, quote the relevant text:
  ```markdown
  > <quote>
  ```

Sources post:

- Put sources at the end of the thread.
- Link each source and say what it supports.
- Keep sources out of the main channel unless it is a quick update.

Omit empty or artificial sections except `Sources`. One good story beats several shallow notes.

If new events arrive for an existing thread, append only the delta. Do not repeat the full background unless the user needs it to understand the update.

## 7. Judge

For medium/deep work, start a separate judge subagent before publishing. The judge checks the work against the quality bar, fills `research/checklist.md`, and gives feedback.

Give the judge:

- the original event or user request
- `research/notes.md`
- relevant files in `research/artifacts/`
- `output/output.md`
- `research/checklist.md`
- this workflow and `anti-ai-slop.md`

The judge must not rubber-stamp the draft. It should leave boxes unchecked when evidence is missing, the work skipped a step, the thread is hard to read, visuals are weak/missing, claims are unsupported, or the tone misses the bar. A checkbox without concrete evidence underneath is not complete.

Revise `output/output.md` and the supporting work until the judge's blocking feedback is resolved.

## 8. Publish

Share the finished output through `cli`.

- Quick update: `cli message send`.
- New medium/deep story: `cli thread create`.
- Update to an existing story: `cli thread append`.
