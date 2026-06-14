# Expected: unit_claude_lazy_senior_dev_mode

- The agent's trajectory conforms strictly to the workflow described in `AGENTS.md`, `$keep-up-with` `SKILL.md`, and related references. The flow is effective and efficient.
- A short thread is published to the most appropriate channel, expected to be `ai.tools`. A one-message update is too thin for this case; a long deep-dive thread is not expected.
- Explain Ponytail as a Claude Code plugin plus portable ruleset/adapters for making coding agents write less code, rather than only as a prompt.
- Explain the “lazy senior dev” rule plainly: before coding, the agent checks whether the code needs to exist, whether the standard library, platform, installed dependencies, or one line already solve it, and only then writes custom code.
- For GitHub repo events, the first image should be a sensible screenshot crop of the repo itself. For this case, expect a repo README image, a how-it-works image, a benchmark chart, and a star-history chart made with `cli tools repo star-history`.
- Keep benchmark claims tied to the repo's benchmark README. Do not present Ponytail as independently proving a 3-6x improvement.
- Visuals should be cropped tightly to exactly where they need to be and readable, with no clipped labels, adjacent prose, browser chrome, or loose horizontal framing. See `expected/assets/` for examples of good crop quality.
- Use `expected/reference.md` as the quality bar. The final output should be on par with or better than that reference in coverage, visual use, plain-English explanation, source attribution, and readability.
