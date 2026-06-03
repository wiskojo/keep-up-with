## Step 1: Research

- **Research the source:** Do DFS into the event itself directly: original post, linked source, paper, repo, model card, release notes, benchmark page, dataset, demo, transcript, author thread, official page, or primary artifact.
- **Research the context:** Do BFS around the event: check adjacent links, prior art, related ideas, competing work, similar launches, comments, benchmarks, older claims, critiques, and close comparables; name concrete relationships and research any obvious closest comparison.
- **Track source support:** List sources as you research. For each source, write what it supports.
- **Map the evidence:** Capture depth and breadth: for depth, explain what happened, what was released or claimed, how it works, what numbers are claimed, what changed, what artifacts exist, and what is uncertain; for breadth, explain what came before, what it resembles, what differs, what supports or challenges it, and what gives it context.

## Step 2: Cross Reference

- **Check prior user-facing work:** Use `cli` and durable context to check prior user-facing surfaces that could be related: messages, threads, channels, prior events, dismissed inbox items, story/workspace folders, `USER.md`, `MEMORY.md`, prior notes, artifacts, recurring topics, and workflow lessons; this is not generic BFS research.
- **Calibrate to the user:** Cross-reference to contextualize the story around the user’s expected understanding: infer what they likely already know and should not be re-explained, what they likely do not know and needs more detail, what they would care about, and whether this is a new story, update, delta, continuation, correction, contradiction, repeated discourse, duplicate, or no real change.
- **Apply the cross-reference:** Use cross-reference to avoid duplicate threads, repeated background, mixed topics, and re-teaching context; if a thread already exists, plan an update that only explains the delta unless the user needs the full background again, and record the prior message/thread/source that shaped the decision.

## Step 3: Identify Highlight

- **Answer the user’s likely questions:** Extract highlights by first writing the specific questions this user would ask after a shallow summary, then make the highlights answer those questions instead of merely listing facts: What is this exactly? Can it be used? What does it require? What is the closest prior art? What changed? What breaks the claim? What does the key mechanism do? Is it real, useful, new, overclaimed, repeated, actionable, or worth following?
- **Explain the mechanism:** Explain what actually changed, what is new, what is corrected, what is confirmed, what is still unproven, and the actual mechanism the claim depends on, especially any evaluator, benchmark, dataset, verifier, ablation, or technical phrase carrying the substance.
- **Compare against familiar context:** Use comparisons the user is likely to understand to explain what is similar, what is different, and why it matters. Spend fewer words on familiar background and more on the new details that reduce the user’s time to understanding.
- **Choose the right visual:** Choose visuals based on what each highlight needs to convey. Source visuals are often best because the authors designed them to explain their own point, but use custom visuals when they better verify, compare, simplify, synthesize, or make the point readable.
- **Rank the highlights:** Frame highlights as source-supported answers in a ranked story, from most to least important, so the user gets the main understanding early and each later highlight adds less essential detail.

## Step 4: Write Draft

- **Plan the thread:** Draft the reasoning for the thread before writing final prose. For each post, explain its purpose, why it belongs in that position, what details it includes, what it omits, how it moves the story forward, what visual it uses, where the visual comes from, why that visual is right, and why weaker alternatives were rejected.
- **Write post 1 as an abstract:** Treat post 1 like an abstract for the thread. By default, include enough background to place the event, what happened or what it is in plain English, what changed or is new compared with relevant baselines, and the main visual; adjust or omit parts when the story calls for it. Use later posts for mechanism, comparison, results, caveats, user-relevant context, quotes, or examples.
- **End with sources:** Put sources last and split them into main sources and supplementary sources when both shaped the output.
- **Keep the thread readable:** Spend words on event substance instead of unnecessary names, and avoid wall-of-text posts with spacing, emphasis, visuals, quotes, and post breaks.

## Step 5: Output

- **Label supplementary material:** When using supplementary commentary, label it as supplementary and quote the exact relevant part if the wording matters.
- **Synthesize instead of opining:** Default to source-grounded synthesis over opinion. Report what sources say, reconcile competing perspectives, explain what is supported, disputed, missing, or uncertain, and do not lead with your own judgment. Avoid claims like “the most concrete,” “the strongest,” “the best,” or “the practical read” unless the sources clearly support that framing. When a judgment is useful, ground it in who said it, what data supports it, what comparison it depends on, and what would change the conclusion.
