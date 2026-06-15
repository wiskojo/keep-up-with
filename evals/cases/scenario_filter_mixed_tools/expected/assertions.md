# Expected: scenario_filter_mixed_tools

- The agent's trajectory conforms strictly to the workflow described in `AGENTS.md`, `$keep-up-with` `SKILL.md`, and related references. The flow is effective and efficient.
- Publish exactly 3 user-facing messages from the event batch. Do not create a thread.
- The published messages should cover only Apple `container`, CodeBoarding, and React Doctor.
- Each useful tool gets its own standalone message. Do not combine the 3 tools into one batch summary.
- Each published message includes relevant visual attachment(s). Visual can be an image, GIF, or short video. For React Doctor, use the short demo video if available instead of a static docs screenshot. For repo screenshots, prefer the README/product intro, install, demo, or how-it-works section over the file list.
- Visuals should be readable and cropped to the specific source object being discussed. No browser chrome, clipped text, full-page strips, loose framing, loading spinners, or unloaded embeds.
- Each message is short and plain English, but still concrete enough to understand what the tool does. Do not mention hidden event framing like "the event says," "the event had," "from the comments," or "tool lead." If naming a small company or project backer, add a short descriptor or omit it; for React Doctor, explain Million briefly if you name it. Use one compact adoption/traction signal, not a paragraph of metrics. If a message needs more than 2-4 short sentences, cut detail or make it a thread.
- Keep caveats out of standalone messages unless they change what the user should do now. Avoid version lists, issue lists, telemetry notes, requirements, rule/category inventories, and minor implementation limits. For Apple `container`, say what it is and why it cleared the bar; do not spend the short message on OS-version, Apple-Silicon, memory-management, or Docker/OrbStack comparison details unless those become the story. For React Doctor, explain the CLI/GitHub Action and attach the demo; do not list the rule catalog.
- Skip and dismiss the 4 low-signal events with no user-facing output.
- Triage should be aggressive for self-promotion and tool-shaped posts with no traction. Use rough signal guides such as 100+ Reddit upvotes, 100+ GitHub stars, or 10k+ X impressions, calibrated by source quality, recency, and whether the event is genuinely time-sensitive.
