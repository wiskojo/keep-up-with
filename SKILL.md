## Step 1: Research

- **Research the source (DFS):** Read the event itself first: original post, linked source, paper, repo, model card, release notes, benchmark page, dataset, demo, transcript, author thread, official page, or primary artifact.
- **Research the context (BFS):** Check adjacent links, prior art, related ideas, competing work, similar launches, comments, benchmarks, older claims, critiques, reactions, and close comparables. Name the relationship. If there’s an obvious closest comparison, research it. Check places where the event is being discussed, such as Reddit, Hacker News, X posts or quote posts, GitHub issues, comments, Discord logs, or forum threads. Use reactions when they add support, critique, confusion, reproducibility notes, or a useful outside comparison.
- **Understand depth from breadth:** Depth means what happened, what got released or claimed, how it works, what numbers are claimed, what changed, what artifacts exist, and what’s still uncertain. Breadth means what came before, what it resembles, what’s different, what supports or challenges it, and what context changes the interpretation.

## Step 2: Cross-reference

- **Check prior user-facing work:** Use `cli` and durable context to check related messages, threads, channels, prior events, dismissed inbox items, story/workspace folders, `USER.md`, `MEMORY.md`, prior notes, artifacts, recurring topics, and workflow lessons.
- **Calibrate it to the user:** Use that history to infer what the user likely knows, what doesn’t need another explanation, what needs more detail, what they would care about, and whether this is a new story, update, delta, continuation, correction, contradiction, repeated discourse, duplicate, or no real change.
- **Ground the context:** Give just enough background for the user to understand the new thing. For any comparison, person, project, company, event, or idea used as context, decide how much to explain based on what the user likely knows, how recent or visible the reference is, and whether the detail changes their understanding.
- **Make contextual updates:** Avoid duplicate threads, repeated background, mixed topics, and re-teaching old context. If a thread already exists, update only the delta unless the user needs the full background again. Record the prior message, thread, or source that shaped the call.

## Step 3: Identify Highlights

- **Answer the user’s likely questions:** Before choosing highlights, write the questions this user would ask if they were to hear about this event, then answer those questions instead of listing facts. What is this exactly? How does it work? What’s the closest prior art? How is this different from X? What does the key mechanism do? Is it real, useful, new, overclaimed, repeated, actionable, or worth following?
- **Explain the mechanism:** Say what actually changed, what’s new, what got corrected, what got confirmed, what’s still unproven, and what the claim depends on, especially any evaluator, benchmark, dataset, verifier, ablation, or technical phrase carrying the substance.
- **Compare against familiar context:** Use comparisons the user is likely to understand to explain what’s similar, what’s different, and why it matters. Spend fewer words on familiar background and more on the new details that get them to understanding faster.
- **Choose the right visual:** Choose visuals based on what each highlight needs to convey. Source visuals are often best because the authors designed them to explain their own point. Use custom visuals when they make the point clearer, easier to verify, easier to compare, or less dense. Every non-source post in a thread needs a visual.
- **Order by usefulness:** Arrange highlights as answers backed by sources, from most useful to least. The user should get the main story early; each later highlight adds less essential detail.

## Step 4: Draft The Thread

- **Plan it out:** Before writing the thread, explain the role of each post: why it goes there, what it includes, what it leaves out, how it moves the story forward, what visual it uses, where the visual comes from, why that visual fits, and why weaker options lost.
- **Make the first post the abstract:** Treat the first post like the thread abstract. By default, give enough background to contextualize the event, explain what happened or what it is in plain English, say what changed compared with the relevant baseline, and include the main visual. Adjust or omit parts when the story calls for it. Use later posts for mechanism, comparison, results, caveats, user-relevant context, quotes, or examples.
- **Put sources last:** End with sources. Split main sources from supplementary sources when both shaped the output.
- **Keep it readable:** Spend words on the event, mechanism, evidence, and consequence instead of unnecessary names. Avoid wall-of-text posts; use spacing, emphasis, visuals, quotes, and post breaks. Don’t give every post a hook or headline. Get to the point, and frame the thread around sourced claims, comparisons, deltas, open questions, and caveats, not personal takes.

## Step 5: Final Output

- **Label extra commentary:** When supplementary commentary shapes the output, label it as supplementary and quote the exact relevant part if the wording matters.
- **Synthesize, don’t opine:** Report what sources say, reconcile competing views, and say what’s supported, disputed, missing, or uncertain. Don’t lead with your own judgment. Avoid claims like “the most concrete,” “the strongest,” “the best,” or “the practical read” unless the sources clearly support that framing. When a judgment helps, ground it in who said it, what data supports it, what comparison it depends on, and what would change the conclusion.
