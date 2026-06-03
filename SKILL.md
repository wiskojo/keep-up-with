## Research

- Do DFS into the event itself directly: original post, linked source, paper, repo, model card, release notes, benchmark page, dataset, demo, transcript, author thread, official page, or primary artifact.
- Do BFS around the event: adjacent links, prior art, related ideas, competing work, similar launches, comments, benchmarks, older claims, critiques, and useful comparables.
- List sources as you research. For each source, write what it supports.
- Capture depth: what happened, what was released or claimed, how it works, what numbers are being claimed, what changed, what artifacts exist, and what is still missing or uncertain.
- Capture breadth: what came before, what this resembles, what it differs from, what supports it, what challenges it, and what gives it context.
- **DFS and BFS must do actual research. Do not write vague category labels like “prompt optimization” or “agent workflows” without naming concrete comparables and explaining the relationship.**
- **If there is an obvious close comparable, research it. Missing the closest comparison is a research failure.**

## Cross Reference

- Use `cli` to check what we have already sent to the user that could be related.
- Look at prior messages, threads, channels, prior events, dismissed inbox items, and existing story/workspace folders.
- Look at durable context when it helps: `USER.md`, `MEMORY.md`, prior notes, artifacts, recurring topics, and workflow lessons.
- Identify what the user has already been told, what they likely remember, what has already been handled, and what should not be repeated.
- Mark the relationship: new story, update, delta, continuation, correction, contradiction, repeated discourse, duplicate, or no real change.
- **Cross-reference is specifically about prior user-facing surfaces, not generic BFS research.**
- **Use it to avoid duplicate threads, repeated background, mixed topics, and re-teaching context the user already has.**
- **If a thread already exists, plan an update that only explains the delta unless the user needs the full background again.**
- **When prior communication affects the framing, record the message/thread/source so the decision is traceable.**

## Highlight

- Extract the top points from the research and cross-reference work.
- Before picking highlights, ask what this specific user would ask after reading a shallow summary.
- Write those likely questions down, then make the highlights answer them.
- Ask what the user would need to know to decide whether this is real, useful, overclaimed, repeated, actionable, or worth following.
- Focus on what changed, what is new, what is corrected, what is confirmed, what is still unproven, and why it matters now.
- Use comparisons and contrasts to things the user likely understands: similar to X, different because Y; same category as X, except with a new mechanism.
- Cut details that are true but do not help the user understand the story.
- Decide what visuals are needed to make the thread readable and concrete.
- **Highlights are answers to anticipated user questions, not just extracted facts.**
- **Ask the obvious skeptical questions before drafting: What is this exactly? Can it be used? What does it require? What is the closest prior art? What breaks the claim? What does the key mechanism actually do?**
- **For technical claims, identify the load-bearing mechanism. If that part fails, what happens? If a validation gate, evaluator, benchmark, dataset, verifier, or ablation carries the argument, explain it.**
- **Do not spend the opening or highlights on background the user already has. Use that space for the specific detail that makes the event different.**
- **If a phrase like “scored rollouts,” “validation gate,” or “optimizer edits” carries the substance, explain the substance instead of hiding behind the phrase.**
- **Visuals are part of the highlight selection, not decoration. Use them to verify, compare, simplify, or break up dense material.**
- **Prefer source visuals for evidence. Use custom visuals for synthesis, comparison, timelines, or simplified result summaries.**
- **Do not turn highlights into personal takes. Phrase them as answers supported by research and cross-reference.**
- Highlights tell a story, it's ranked from most to least important and progressively as people read they understand more of the story. If they stop reading at any point they still have a good understanding as there is diminisng returns in reading the highlgihts.

## Draft

- Sketch the thread structure before writing the final thread.
- For each post, say what it will do (what is its purpose), what details it will include, what it will omit, and why it belongs in that position.
- For each post, plan the visual: what it is, where it comes from, why it is the right visual, and why alternatives are weaker.
- Opening post should give the skimmer version: what happened, what changed, why it is different from the closest baseline or comparable, and the main visual.
- Later posts should expand the parts that need detail: mechanism, comparison, results, caveats, user-relevant context, quotes, or examples.
- Sources should be last.
- Split sources into main sources and supplementary sources when both are used.
- **A draft is the reasoning for the structure, not the final prose. It should explain why this order, why these posts, why these visuals, and why these omissions.**
- **Post 1 should not be short by default. It should carry the essence for skimmers, then later posts can expand the pieces that need more detail.**
- **Do not waste words naming people, companies, repos, or papers unless that identity changes the user’s read of the story. Use the words to explain the event, mechanism, evidence, or consequence.**
- **Do not write a wall of text. Plan for spacing, emphasis, visuals, quotes, and post breaks before drafting.**
- **Do not frame posts around your own opinion. Frame them around source-backed claims, comparisons, deltas, open questions, and caveats.**

## Output

- **Infer what the user likely already knows from the request, durable context, prior messages, prior threads, and related source/browser history when available. Do not spend words teaching basics they already know.**
- **Spend the most words on the new mechanism, delta, evidence, contradiction, or comparison.**
- **When using supplementary commentary, label it as supplementary and quote the exact relevant part if the wording matters.**
- **If a technical label compresses the useful part, unpack it. Explain what the thing actually does.**
- **Do not lead with your own judgment or opinion. Most updates should report what the sources say, reconcile competing perspectives, and explain what is supported, disputed, missing, or uncertain.**
- **Avoid claims like “the most concrete,” “the strongest,” “the best,” or “the practical read” unless the sources clearly support that framing and you can cite why.**
- **When a judgment is useful, ground it in evidence: who said it, what data supports it, what comparison it depends on, and what would change the conclusion.**
- **Default to synthesis, not opinion. The job is to help the user understand the event from source evidence and cross-reference, not to sound decisive.**