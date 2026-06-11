---
name: keep-up-with
description: Investigate an event, decide how much attention it deserves, and publish at the right depth — a quick update, a single update post, or a deep-dive thread.
---

# keep-up-with

## Goal

Turn something the user would have bookmarked and maybe never read into the research they would have done if they had the time: read the main source, inspect the actual artifact, check the surrounding discussion, relate it to what they already know, and compress the useful parts into the right-sized update.

The response tier is an output of this work, not an input. Research until you know what the story is, then publish at the depth the evidence earned. Most stories end as a quick update or a single update post; a thread is for stories with real depth. Coming back down to a smaller update is success, not wasted work.

The user should be able to see how the original source, repo or docs, outside reactions, comments, prior work, and prior user-facing context each change the read. Attribute outside perspectives clearly, especially when they come from people the user knows, people with weight in the field, or reactions getting attention.

Prior messages, threads, durable context, browser or source history when available, and recurring user interests are part of the research surface. Use them to infer what the user already understands, what they would have checked themselves, what they don’t need re-explained, and what needs more detail now.

## Setup

- **One folder per story, reused:** Search `stories/` for an existing folder before creating one; follow-up events belong with the original story. For a new story, create `stories/<YYYY-MM-DD>-<slug>/` and work from inside it, so `research/` and `outputs/` paths below resolve there:

```text
stories/2026-06-10-example-launch/
    research/
        notes.md
        artifacts/
    outputs/
        output.md
        assets/
```

- **Use the notes template:** Initialize `research/notes.md` from [template.md](references/template.md). Keep the headings and fill them in as you work. `notes.md` is the running record of what you checked, learned, decided, and why.
- **Keep raw work separate from final work:** Put raw files gathered during research in `research/artifacts/`. If you find potentially useful figures, diagrams, screenshots, charts, videos, frames, tables, or source images, save them there as you go. Put the camera-ready draft in `outputs/output.md` and final visual assets in `outputs/assets/`.
- **Check available tools:** You have access to the `cli` command for this work. Run `cli tools --help` during setup.

## Step 1: Research

- **Research the source (DFS):** Read the event itself first: original post, linked source, paper, repo, model card, release notes, benchmark page, dataset, demo, transcript, author thread, official page, or primary artifact. Save source media as you go — event payloads often carry media URLs; download the relevant images or video stills into `research/artifacts/`. For talks and videos, get the transcript; if no transcript is available, extract key frames instead — video metadata alone is not research.
- **Research the context (BFS):** Check adjacent links, prior art, related ideas, competing work, similar launches, comments, benchmarks, older claims, critiques, reactions, and close comparables. Name the relationship. If there’s an obvious closest comparison, research it. Check places where the event is being shared and discussed, such as Reddit, X, Youtube, Huggingface, etc. Use reactions when they add support, critique, confusion, reproducibility notes, or a useful outside comparison.
- **Understand depth from breadth:** Depth means what happened, what got released or claimed, how it works, what numbers are claimed, what changed, what artifacts exist, and what’s still uncertain. Breadth means what came before, what it resembles, what’s different, what supports or challenges it, and what context changes the interpretation.
- **Gauge the attention:** Check how much activity the event is getting relative to when it appeared and where that activity is happening. Look for discussion volume, tone, and content across the obvious relevant surfaces, not only the source platform: Reddit, X, GitHub, YouTube, forums, Discord, blogs/newsletters, package/download activity, stars, forks, comments, reposts, or other domain-specific signals. Exact numbers are fine point-in-time. These updates are meant to be timely and represent the current state. We can always append to the thread later if there are important updates.
- **Weigh reactions:** Judge reactions by both who is saying it and what they show. A major lab, known expert, maintainer, or person the user follows can make a reaction worth reporting, but brand is not proof. Unknown or anonymous sources can still matter when they bring concrete experiments, logs, code, screenshots, careful firsthand analysis, or strong aggregate signal. Treat low-quality individual comments as low value; report them only as aggregate sentiment when the pattern matters.
- **Identify people who matter:** When a named person affects the story, check who they are before drafting: X profile, linked personal site, LinkedIn, GitHub, papers, talks, affiliation, relevant work, and public signals. Capture why their role or background matters here. Do not assume a name explains itself.

## Step 2: Cross-reference

- **Find prior user-facing work:** Triage already did a cheap duplicate search; now do the real pass. Search messages, threads, and events for the story’s links and key terms (`cli message list -q`, `cli thread list -q`, `cli events list -q`), and check prior story folders under `stories/`, dismissed inbox items, `USER.md`, `MEMORY.md`, prior notes, and artifacts.
- **Calibrate it to the user:** Use that history to infer what the user likely knows, what doesn’t need another explanation, what needs more detail, what they would care about, and whether this is a new story, update, delta, continuation, correction, contradiction, repeated discourse, duplicate, or no real change.
- **Ground the context:** Give just enough background for the user to understand the new thing. For any comparison, speaker, author, person, project, company, event, or idea used as context, decide how much to explain based on what the user likely knows, how recent or visible the reference is, and whether the detail changes their understanding. Name people and entities when the identity matters. Include only the descriptor the user needs. If the identity is not useful, describe the source, role, or evidence instead.
- **Place the event among evolving stories:** Stories evolve. The same event can start a new thread, land as a standalone post that may grow into a thread as more news rolls in, or be a delta appended to a thread that already exists. Decide the event’s primary home. If a thread already exists, update only the delta; do not start a duplicate thread or re-teach background the user already has.
- **Link related stories instead of retelling them:** One event can touch several stories — new model results on a benchmark belong in the model’s thread even when a separate thread covers that benchmark. Put the update in its primary home, then link the related thread or post inline: mention a thread with `<#thread_id>` or paste a message `url` from `cli thread list` / `cli message list`. Pulling related context together and making the relationships visible is part of the job; it helps the user understand what’s going on faster.
- **Make contextual updates:** Avoid repeated background and mixed topics. Record the prior message, thread, or source that shaped the placement call.

## Step 3: Identify Highlights

- **Answer the user’s likely questions:** Before choosing highlights, write the questions this user would ask if they were to hear about this event, then answer those questions instead of listing facts. What is this exactly? How does it work? What’s the closest prior art? How is this different from X? What does the key mechanism do? What can actually be used now? What is missing? Is it useful, new, overclaimed, repeated, actionable, or worth following?
- **Explain the mechanism:** Say what actually changed, what’s new, what got corrected, what got confirmed, what’s still unproven, and what the claim depends on, especially any evaluator, benchmark, dataset, verifier, ablation, or technical phrase carrying the substance.
- **Compare against familiar context:** Use comparisons the user is likely to understand to explain what’s similar, what’s different, and why it matters. Spend fewer words on familiar background and more on the new details that get them to understanding faster.
- **Surface public discussion:** If there is real public discourse around the event, say where people are talking and what they are saying: the launch post on X, practitioner debate on Reddit/forums, YouTube or newsletter explainers, confusion, or pushback. If there is not much discourse around the event, do not mention it. If the discussion has several useful threads, split them into separate highlights instead of compressing them into one reactions post. Use short representative quotes when they carry the tone, claim, critique, or evidence better than a paraphrase; format them as blockquotes with `>`. Use metrics to show scale, but spend the words on the claims, disagreements, evidence, and open questions.
- **Choose source visuals:** Inventory visuals from the source, linked artifacts, docs, demos, videos, social posts, repos, and discussion threads. Use source visuals when they carry the point directly: screenshots, figures, charts, tables, diagrams, video frames, thumbnails, product surfaces, repo views, comments, or issue excerpts. Do not build custom visuals, generated images, synthetic charts, SVG summaries, new timelines, new diagrams, or visual reinterpretations. If no source visual supports the post, publish without one instead of inventing one. Follow [visuals.md](references/visuals.md).
- **Order by usefulness:** Arrange highlights as answers backed by sources, from most useful to least. The user should get the main story early; each later highlight adds less essential detail.

## Step 4: Decide The Tier

- **Let the evidence pick:** The tier is how much the user cares times how much survives distillation. If the story compresses into a quick update without losing anything the user would want, send the quick update no matter how long the source is. One coherent point that needs explanation, a visual, or a quote → update post. Highlights that keep stacking — multiple useful perspectives, artifacts, results, or deltas the user may return to → deep-dive thread.
- **Figure density is a deep-dive signal:** Model releases, benchmarks, papers, and technical posts packed with charts, tables, diagrams, and figures usually earn a thread — each worthwhile figure can carry a post with its visual. Do not downgrade a rich source because the transcript, frames, or figures take work to extract.
- **An existing thread wins:** If the story already has a thread, append the delta there instead of choosing a new tier.
- **Distill, don't pad:** A tight update the user reads beats a padded thread they skim — but losing interesting highlights to brevity is a miss, not a win. Record the tier and the reason in `notes.md`.

## Step 5: Draft

- **Write the abstract post first:** Draft one post of around ~1,000 characters that could stand alone: enough background to contextualize the event, what happened or what it is in plain English, what changed compared with the relevant baseline, and the main visual when one exists. This is the whole output at the update-post tier, and the opening post of a thread. For a quick update, compress it to a few plain sentences and the main link.
- **Ground it in the source:** An update post or thread post should carry a source quote, an attached source visual, or both. Attach files from `outputs/assets/` with `-a`; an attached image beats a bare link. If the sources offer neither a usable quote nor a visual, note why in `notes.md`.
- **For a thread, plan the rest:** Decide how much of the research is worth sending. Use a longer thread when there are multiple useful perspectives, artifacts, or deltas; use a short thread when one point carries the story. For each post, know why it goes there, what it includes, what it leaves out, how it moves the story forward, and which visual it uses and why weaker options lost. Use later posts for mechanism, comparison, results, caveats, user-relevant context, quotes, or examples, around ~500 characters each.
- **Keep it readable:** Spend words on the event, mechanism, evidence, and consequence instead of unnecessary names. Avoid wall-of-text posts; use spacing, emphasis, visuals, quotes, and post breaks. Use only the supported formatting in [formatting.md](references/formatting.md) — there are no tables.
- **No hooks or signposting:** Don’t give every post a hook or headline. Do not open posts with sentences that explain the role of the post instead of advancing the story; if a signpost is useful, fold it into a factual sentence and get to the point.
- **Show where perspectives come from when it matters:** original source, outside reaction, repo, issue, comment, benchmark, or prior work.
- **Keep internals out:** Do not expose internal tool details like CLI names, tool responses, sandbox status, traces, or file paths unless the user asked or that detail changes the public story.
- **Synthesize without opining:** Act like a reporter, not a pundit. Don’t share your own opinions by default; collect facts, attributed perspectives, source claims, contradictions, and open questions, then report how they fit together. Reconcile competing views and say what is supported, disputed, missing, or uncertain. Avoid ranking claims unless the sources support the ranking. If a judgment belongs in the output, ground it in who said it, what data supports it, what comparison it depends on, and what would change the conclusion. Keep caveats proportional. Do not help me "frame" or tell me what the "read" is; just investigate and faithfully report different perspectives around the event.
- **Run the anti-slop pass:** Before publishing at any tier — quick update, update post, or thread — run `$anti-slop` over everything you are about to send. Remove banned phrases, generic framing, internal narration, over-structured prose, and unsupported judgments.
- **Put sources last:** End threads with sources. Split main sources from supplementary sources when both shaped the output. For quick updates and update posts, the main link inline is enough.

## Step 6: Publish

- **Ship through `cli`:** Quick update or update post: `cli message send --channel <topic channel>`, with the DM reserved for direct replies. New deep dive: publish the whole thread in one command — `cli thread create --channel <channel> --title <title> -p "<post 1>" -p "<post 2>" …`, attaching visuals from `outputs/assets/` with `-a N:path` to bind a file to post N. The user is mentioned automatically in a final post once everything is up, so create the thread only when it is complete. Update to an existing story: `cli thread append --thread-id <id>`.
- **Stay under the limits:** Keep each message or post comfortably under Discord’s 2,000-character cap; split before sending.
- **Record what you published:** Write the message or thread ids and links into `notes.md` so future triage finds this story.
