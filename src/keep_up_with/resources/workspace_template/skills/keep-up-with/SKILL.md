---
name: keep-up-with
description: Investigate an event, decide how much attention it deserves, and publish at the right depth — a quick update, a single update post, or a deep-dive thread.
---

# keep-up-with

## Goal

Turn something the user would have bookmarked and maybe never read into the research they would have done if they had the time: read the main source, inspect the actual artifact, check the surrounding discussion, relate it to what they already know, and compress the useful parts into the right-sized update.

The response tier is an output of this work, not an input. Research until you know what coverage the story needs, then publish at that depth. Simple events end as a quick update. Use a thread when the source itself is long or dense — a report, paper, deep technical post, or 20-50+ minute video or talk — when the event is clearly important, or when public discussion adds several distinct claims that need coverage. A thread opens with a short version that is useful by itself, then expands only the details worth reading.

The user should be able to see how the original source, repo or docs, outside reactions, comments, prior work, and prior user-facing context each change the read. Attribute outside perspectives clearly, especially when they come from people the user knows, people with weight in the field, or reactions getting attention.

Prior messages, threads, durable context, and recurring user interests are part of the research surface. Use them to infer what the user already understands, what they would have checked themselves, what they don’t need re-explained, and what needs more detail now. Use browser or bookmark history only when it directly helps calibrate the current story.

## Output Contract

**IMPORTANT: THE ONLY MESSAGE OR FIRST THREAD POST IS FOR HIGH-LEVEL UNDERSTANDING ONLY.**

Write it for a technical reader who has not read the source and does not want implementation details yet. It should answer:

- what happened
- what the thing is
- why it is showing up now
- why it matters enough to send

It should usually include three brief context anchors:

- **Time:** when the thing actually happened or started gaining attention, not just when this notification arrived. Use relative time first: `2 hours ago`, `3 days ago`, `1 week ago`; add a date only when the relative time is more than 2 weeks ago, such as `3 weeks ago (May 27)`.
- **Entity:** who or what the unfamiliar person, company, project, or tool is. If it is not in `MEMORY.md`, not in subscriptions, and not obviously well known, add the shortest useful descriptor: role, affiliation, maturity, adoption, category, or why their view matters. Do not write `the company behind X` or `the author of X` by itself; that restates the link. Say what kind of entity it is, how established it is, what it builds, or omit the name if that context is not useful.
- **Traction:** a rounded sense of current attention or adoption, not an exact telemetry dump: `nearly 200k X impressions`, `500+ Reddit upvotes`, `around 9k GitHub stars`, `quiet discussion so far`.

Do not put implementation details, config names, API fields, IOCs, release-note lists, version numbers, package inventories, benchmark plumbing, or long caveats in the only message or first post.

If those details matter, make a thread and put them in later posts. If they do not matter, cut them.

Single message: max two short paragraphs, source link, attachments. No detail section.

Thread: opener follows the same high-level rule; later posts can explain mechanism, evidence, comparisons, examples, caveats, and technical details.

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

- **Use the notes template:** Initialize `research/notes.md` from [template.md](references/template.md). Keep a running record for each workflow step as you work through it, not a recap written after publishing. Rough notes are fine; capture what you checked, what changed your understanding, what decisions you made, and why.
- **Keep raw work separate from final work:** Put raw files gathered during research in `research/artifacts/`. If you find potentially useful figures, diagrams, screenshots, charts, videos, frames, tables, or source images, save them there as you go. Put the camera-ready draft in `outputs/output.md` — one `## ` heading per post, with `Attachment: <path>` lines inside the post they belong to — and final visual assets in `outputs/assets/`.
- **Check available tools:** You have access to the `cli` command for this work. Run `cli tools --help` during setup.

## Step 1: Research

- **Research the source (DFS):** Read the event itself first: original post, linked source, paper, repo, model card, release notes, benchmark page, dataset, demo, transcript, author thread, official page, or primary artifact. Save source media as you go — event payloads often carry media URLs; download the relevant images or video stills into `research/artifacts/`. For any source artifact, inspect it directly enough to understand what it contains; do not stop at metadata or the headline.
- **Research the context (BFS):** Check adjacent links, prior art, related ideas, competing work, similar launches, comments, benchmarks, older claims, critiques, reactions, and close comparables. Name the relationship. If there’s an obvious closest comparison, research it. Choose the surrounding surfaces most likely to change the story; do not query every platform by default. Use reactions when they add support, critique, confusion, reproducibility notes, or a useful outside comparison.
- **Understand depth from breadth:** Depth means what happened, what got released or claimed, how it works, what numbers are claimed, what changed, what artifacts exist, and what’s still uncertain. Breadth means what came before, what it resembles, what’s different, what supports or challenges it, and what context changes the interpretation.
- **Gauge the attention:** Check how much activity the event is getting relative to when it appeared and where that activity is happening. Separate the notification time from the artifact time: for tools, repos, products, papers, videos, or posts, find when the thing was released or started gaining attention, not only when this notification arrived. Look for discussion volume, tone, and content across the obvious relevant surfaces: Reddit, X, GitHub, YouTube, forums, Discord, blogs/newsletters, package/download activity, stars, forks, comments, reposts, or other domain-specific signals. For self-promotion and tool/repo shares, use rough starting gates like 50+ Reddit upvotes, 100+ GitHub stars, or 10k+ X impressions before surfacing it; a weak post can still clear if the linked artifact has real adoption or immediate usefulness. Exact numbers are fine point-in-time.
- **Weigh reactions:** Judge reactions by both who is saying it and what they show. A major lab, known expert, maintainer, or person the user follows can make a reaction worth reporting, but brand is not proof. Unknown or anonymous sources can still matter when they bring concrete experiments, logs, code, screenshots, careful firsthand analysis, or strong aggregate signal. Treat low-quality individual comments as low value; report them only as aggregate sentiment when the pattern matters.
- **Identify people who matter:** When a named person affects the story, check who they are before drafting: X profile, linked personal site, LinkedIn, GitHub, papers, talks, affiliation, relevant work, and public signals. If the person is not a technical household name, add the shortest useful descriptor when naming them: role, company, project, or why their view matters. For talks, interviews, and author-led work, search the person plus company or project before drafting; use the most specific verified role or seniority in the opening, or stick to the source-stated title if you cannot verify more.

## Step 2: Cross-reference

- **Find prior user-facing work:** Search like a human would before posting. Check the main link, distinctive keywords, creator, topic, and likely alternate forms of the same story — a clip from a longer video, a crosspost, a re-upload, or a different source covering the same event. Search messages, threads, and events (`cli message list -q`, `cli thread list -q`, `cli events list -q`), then check prior story folders under `stories/`, dismissed inbox items, `USER.md`, `MEMORY.md`, prior notes, and artifacts.
- **Calibrate it to the user:** Use that history to infer what the user likely knows, what doesn’t need another explanation, what needs more detail, what they would care about, and whether this is a new story, update, delta, continuation, correction, contradiction, repeated discourse, duplicate, or no real change.
- **Ground the context:** Give just enough background for the user to understand the new thing. For any comparison, speaker, author, person, project, company, event, or idea used as context, decide how much to explain based on what the user likely knows, how recent or visible the reference is, and whether the detail changes their understanding. If `MEMORY.md` has no entry and the entity is not in the subscriptions and not obviously well known, assume the user may not know it. If the identity does not matter, omit the name or describe the source, role, or evidence instead.
- **Pick the closest channel:** Use channel descriptions, not section names, to place work. A developer tool belongs in the tools channel when that is the closest reusable topic, even if the surrounding section is AI-focused. Use `general` only when no topic channel fits.
- **Place evolving stories:** A story can start as a message or thread. Same story means the same concrete release, project, repo, paper, product, company event, source, or claim got new facts; same theme or trend is not enough. If a same-story event is a substantial source on its own, such as a long video, report, repo, paper, or detailed investigation, publish its own output first, then append or link a delta in the existing story thread. If it is only an update, read the existing thread and append the delta there. If prior coverage is a standalone post and a later same-story event adds discussion, tests, source material, or a useful update, convert it into a thread (`cli thread create --from-message`) and put the delta there; dismiss only true repeats with no new user-facing value.
- **Use trend threads:** A trend thread is a separate meta-thread across multiple distinct story outputs. Do not create one from the first story alone, and do not promote the first story thread into the trend thread later. When a second distinct story reveals the pattern, first publish that story's own output, then create or update a separate trend thread whose title names the pattern, not one product, repo, paper, company, or project. The trend thread links story outputs and explains the cross-story delta.
- **Split independent leads:** One event or batch can contain several unrelated tools, claims, or stories. Split them into separate messages or threads when they answer different user questions, belong in different channels, or need different evidence. Judge each lead by its own artifact, adoption, and usefulness, not only by the score of the comment or post where you found it. Group only when they are parts of the same specific story; do not write a roundup just because the items arrived together. Link related coverage inline when useful.

## Step 3: Identify Highlights

- **Answer the user’s likely questions:** Before choosing highlights, write the questions this user would ask if they were to hear about this event, then answer those questions instead of listing facts. What is this exactly? What can someone do with it? How does it work? What’s the closest prior art? How is this different from X? What can actually be used now? What is missing? Is it useful, new, overclaimed, repeated, actionable, or worth following?
- **Understand the mechanism:** In notes, identify what actually changed, what’s new, what got corrected, what got confirmed, what’s still unproven, and what the claim depends on. In output, include only the amount the chosen tier needs; the opener never carries mechanism details.
- **Compare against familiar context:** Use comparisons the user is likely to understand to explain what’s similar, what’s different, and why it matters. Spend fewer words on familiar background and more on the new details that get them to understanding faster.
- **Use public discussion when it changes the story:** If discourse matters, capture where people are talking and what they are saying. Keep weak or quiet discussion in notes. Use representative quotes for concrete claims, evidence, confusion, or pushback; do not add a reactions section just because you looked.
- **Choose source visuals:** Open [visuals.md](references/visuals.md), then inventory source visuals in `notes.md`: screenshots, figures, charts, tables, diagrams, video frames, product surfaces, repo views, comments, and social posts. For repo/tool stories, include both an overview of the artifact itself, such as the repo README or product page, and the specific update/release surface when both exist; this applies to single-message updates too. For visual-rich sources, reports, studies, dashboards, talks, and long posts, do not stop at one overview image; extract each high-value figure or table separately before adding outside-context visuals. For talks, use a title/stage/speaker frame as the opener when available; do not replace it with a technical slide unless the talk frame is unreadable. Then use technical frames for the claims. Split multi-panel screenshots when separate panels need separate explanation. Source material only, no custom or generated visuals.
- **Choose source quotes:** Inventory quotes the way you inventory visuals: author claims, paper sentences, release notes, changelog lines, X posts, Reddit comments, and talk moments. If a good source visual carries the point, use the visual before a quote. Prefer quotes with concrete evidence, results, numbers, failure reports, or sharp questions over generic reactions. Use enough of the quote to carry the context; do not clip a five-word fragment if the surrounding sentence is what makes it meaningful. Quotes sit inside your own synthesis, grounding it rather than replacing it. Quote verbatim from saved source material as `>` blockquotes. For public reactions, put the quote first and the attribution directly under it, still inside the blockquote: `> quote text` then `> _r/example comment, 60 upvotes_`. Do not put attribution before the quote or outside the blockquote. Never reconstruct a quote from memory.
- **Order by usefulness:** Arrange highlights as answers backed by sources, from most useful to least. The user should get the main story early; each later highlight adds less essential detail.

## Step 4: Decide The Tier

- **Let the evidence pick:** Decide tier after the visual and quote inventory is resolved. A quick update is one timely fact and a link. An update post is one compact point following the Output Contract. Repo/tool releases default to one short message when the user can understand the point without multiple posts, even if the repo has many details. Use a thread only when the source is long/dense, the artifact needs several separate claims explained, or a short post would mislead. Do not make a thread because you found prior art, reactions, caveats, or a busy comment thread. Gathered research is raw material, not the payload.
- **Use the right story surface:** If the same concrete story already has a thread and the new event is just a delta, append there. If the new source also deserves its own message or thread, publish that independent output first, then append a shorter delta that links it from the story thread. A cross-story trend is different: keep the story output and create or update the separate trend thread.
- **Distill, don't pad:** Add posts only when they change understanding. For talks and videos, do not recap every segment; pick the moments that matter. Record the tier and the reason in `notes.md`.

## Step 5: Draft

- **Follow the Output Contract:** The only message or first thread post must be a high-level short version. Start from the user's mental model, not source jargon.
- **Ground it in the source:** Every post should carry source visual media by default: image, chart, table, diagram, screenshot, video frame, GIF, or short clip. Use the best source visual for the claim; if no prebuilt visual exists, capture a readable screenshot of the article, docs, repo, release, post, comment, transcript, or source surface. Quotes are supplementary context, not a substitute for visual media. Multiple attachments are fine when they explain the same compact point, but do not attach the same image or crop more than once. Attach files from `outputs/assets/` with `-a`; attached media beats a bare link.
- **Make outputs stand alone:** Do not refer to hidden discovery context like "from the comments," "from this batch," "the event said," "people pointed at," "same discussion," or "tool lead" unless that context is the story itself and visible in the same post. A message split out from a larger source should read as if it were discovered directly. Once an independent tool, project, or claim is split into its own output, write it as its own update and omit how you discovered it.
- **For a thread, plan the rest:** Later posts expand only the details worth reading — mechanism, comparison, results, reactions, caveats, user-relevant context, examples — around ~500 characters each. Use a longer thread when the evidence keeps stacking; use a short thread when one point carries the story. In short threads, group related visuals under one point instead of giving every image its own post. For each post, know which aspect it expands, what it includes, what it leaves out, and which visuals or quotes ground it. Spread the evidence across the thread so each post stands on its own — not front-loaded into the opening posts, not dumped at the end.
- **Keep it readable:** Spend words on understanding, not inventory. When a percentage, benchmark, or breakdown appears, say what it measures. When a framework-specific term matters, explain it plainly. Avoid wall-of-text posts; use spacing, emphasis, visuals, quotes, and post breaks. Use only the supported formatting in [formatting.md](references/formatting.md) — there are no tables.
- **No hooks or signposting:** Don’t give every post a hook or headline. Do not open posts with sentences that explain the role of the post instead of advancing the story; if a signpost is useful, fold it into a factual sentence and get to the point.
- **Show where perspectives come from when it matters:** original source, outside reaction, repo, comment, benchmark, or prior work. Treat issues and PRs as research details by default. In output, use at most a short summary unless the issue or PR is the event itself; do not give issue/PR material its own post, quote, or screenshot.
- **Keep internals out:** Do not expose internal tool details like CLI names, tool responses, sandbox status, traces, or file paths unless the user asked or that detail changes the public story.
- **Synthesize without opining:** Act like a reporter, not a pundit. Don’t share your own opinions by default; collect facts, attributed perspectives, source claims, contradictions, and open questions, then report how they fit together. Reconcile competing views and say what is supported, disputed, missing, or uncertain. Avoid ranking claims unless the sources support the ranking. If a judgment belongs in the output, ground it in who said it, what data supports it, what comparison it depends on, and what would change the conclusion. Keep caveats proportional and lower in the thread unless they change the main takeaway. Do not help me "frame" or tell me what the "read" is; just investigate and faithfully report different perspectives around the event.
- **Run the grounding check:** Before publishing at any tier, scan `outputs/output.md` post by post: each post carries visual attachment(s); every final visual in `outputs/assets/` is attached; quotes support visuals instead of replacing them; evidence is spread rather than clustered; the visual inventory covers the claims you mention; each crop shows one visual object tied to that post, with no clipped labels, browser chrome, adjacent prose, or loose framing; the opener gives a useful short version without trying to cover every detail. Fix gaps before sending.
- **Run the anti-slop pass:** Before publishing at any tier — quick update, update post, or thread — run `$anti-slop` over everything you are about to send. Remove banned phrases, generic framing, internal narration, over-structured prose, and unsupported judgments.
- **Put sources last:** End threads with a separate sources post. Split main sources from supplementary sources when both shaped the output. List actual sources, not failed searches, low-traction checks, or notes that public discussion was quiet. Do not bundle sources into a caveats or discussion post. For quick updates and update posts, the main link inline is enough.

## Step 6: Publish

- **Ship through `cli`:** Quick update or update post: `cli message send --channel <topic channel>`, with the DM reserved for direct replies. New deep dive or new trend thread: publish the draft directly — `cli thread create --channel <channel> --title <title> --file outputs/output.md`; each `## ` heading becomes a post and its `Attachment:` lines become attached files. Do not write ad-hoc scripts to convert the draft into arguments. Create the thread only when the draft is complete; thread creation handles notification/membership on its own. Story outgrowing a standalone post: same command with `--from-message <message_id>` — the existing post becomes the thread opener and every `## ` post lands inside the thread. Update to an existing story or existing trend: `cli thread append <thread_id>` — use the matching story thread for story deltas and the separate trend thread for trend deltas.
- **Stay under the limits:** Keep each message or post comfortably under Discord’s 2,000-character cap; split before sending.
- **Record what you published, then stop:** Write the ids and links returned by the publish command into `notes.md`, then return. Do not run a post-publish audit loop unless the publish command failed or the user asked for verification.
