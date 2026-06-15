# Expected: unit_reddit_multi_tool_split

- The agent's trajectory conforms strictly to the workflow described in `AGENTS.md`, `$keep-up-with` `SKILL.md`, and related references. The flow is effective and efficient.
- Do not assume one event equals one output. Inspect the Reddit post and comments, then identify any independent tools or leads that clear their own quality/signal bar.
- Expected shape is roughly two independent tool outputs plus one token-saving workflow/tip output, if research confirms they clear the bar.
- Surface only the useful subset. Weak mentions, jokes, generic workflow advice, or tools with no independent signal should be skipped or used only as context. A low-score comment can still surface a tool worth covering if the tool itself has clear adoption, activity, or usefulness.
- Independent tools should become separate messages or threads. Do not combine unrelated tools into one roundup just because they came from the same Reddit event.
- Each surfaced tool must have its own source link and relevant visual attachment, usually a README/product intro, docs screenshot, demo, or star-history chart when repo growth or popularity is part of the reason to care. Do not use quote-only output for a repo/tool when a readable source surface exists. Do not use a GitHub file-list screenshot unless repository structure is the point.
- Visuals should be readable and cropped to the specific source object being discussed. No browser chrome, clipped text, full-page strips, loose framing, loading spinners, or unloaded embeds.
- The output must make sense to a user reading the channel cold. For independent tool outputs, do not say "from the comments," "from the discussion," "people pointed at," "same discussion," "tool lead," "the Reddit comment made it sound," or similar discovery framing. Start with what the tool is and what it does.
- The original token-saving workflow may get a short message or thread if it clears the bar, but it should not bury separate tool leads in a paragraph list.
- If RTK is surfaced, explain it as a command-output compressor before listing details: it rewrites noisy terminal output before the agent sees it. Use one concise adoption or savings signal, and include a representative real-user quote only if it helps calibrate the README claim. Do not list every supported command family.
