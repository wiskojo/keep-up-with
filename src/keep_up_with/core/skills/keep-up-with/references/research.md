# Research

Use research to understand the delta, not to produce a generic summary.

## Search Shape

Use BFS to map surrounding context:

- primary source
- linked artifact
- author or organization
- prior messages and threads
- related events
- comments and reactions
- comparable releases, claims, benchmarks, repos, papers, or prior stories

Use DFS only where it changes understanding:

- verify a claim
- check whether a demo is real
- read comments for important corrections
- compare a benchmark or model to relevant baselines
- inspect a repo, paper, release note, dataset, or product page

## Working Files

For medium and deep research, write working notes before final output:

```text
research/
  notes.md
  artifacts/

outputs/
  output.md
  assets/
```

`research/notes.md` is for facts, links, timestamps, open questions, comparisons, and what each source directly supports.

`research/artifacts/` is for screenshots, extracted figures, tables, generated charts, transcripts, frames, source snapshots, or other evidence.

`outputs/output.md` is the camera-ready message or thread post.

`outputs/assets/` is for visuals that belong with the final output.

## Cross-Reference

Relate new information to what the user already knows.

Check:

- previous events
- inbox items
- message history
- existing threads
- `MEMORY.md`
- relevant source tools
- prior research notes or artifacts

Do not re-explain old context unless the user needs it to understand the delta. If the user likely saw the prior update, focus on what changed.

## Visuals

Every real story should have useful visuals unless a visual would add nothing.

Prefer visuals from source material:

- screenshots
- figures
- tables
- benchmark charts
- product screenshots
- repo diffs or activity
- paper diagrams
- video frames
- source excerpts

If source visuals are unavailable, create a useful visual yourself:

- comparison table
- timeline
- source map
- entity map
- benchmark chart
- before/after view
- small generated diagram

Do not use decorative visuals. A visual should help the user understand, verify, or compare something.
