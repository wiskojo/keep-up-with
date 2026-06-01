# Skill Quality Checklist

Use this when editing the Keep Up With skill.

## Discovery And Frontmatter

- [ ] Folder name and `name` are lowercase kebab-case.
- [ ] `SKILL.md` exists at the skill root.
- [ ] YAML frontmatter is delimited with `---`.
- [ ] `description` states what the skill does and when to use it.
- [ ] `description` is third person, specific, under 1024 characters, and includes trigger contexts.
- [ ] The skill is not overbroad; it should not trigger for unrelated general research or writing tasks.

## Progressive Disclosure

- [ ] Root `SKILL.md` is a concise index plus critical operating contract.
- [ ] Detailed guidance lives in one-level `references/` files linked directly from `SKILL.md`.
- [ ] No reference depends on an unlinked nested reference.
- [ ] Each reference has a clear "read this when..." purpose.
- [ ] Information is not duplicated across root and references.
- [ ] Long references include enough headings for fast scanning.

## Actionability

- [ ] Critical workflows are numbered or checklist-based.
- [ ] Commands are concrete and match the current CLI.
- [ ] Fragile operations have specific guardrails.
- [ ] Judgment-heavy work leaves appropriate freedom for context.
- [ ] Output requirements are concrete enough to verify.

## Keep Up With Fit

- [ ] Wording is generic to an agent, not tied to one model or host app.
- [ ] The runtime contract uses the Keep Up With CLI and messaging system.
- [ ] Startup gives the user fast feedback, then performs orientation.
- [ ] Messaging concepts are explained: message, channel, section, thread.
- [ ] Memory rules distinguish `USER.md` from `MEMORY.md`.
- [ ] Medium/deep work uses the required `threads/story-slug/` workspace structure.

## Output Quality

- [ ] Quick FYI/BTW format is 1-4 sentences with a primary link.
- [ ] Medium/deep thread format includes Background, What happened / what is it, What's changed / new when useful, Highlights, and Sources.
- [ ] Sources are cited but do not clutter the main channel.
- [ ] Claims are source-grounded and uncertainty is explicit.
- [ ] Filtering, routing, and skipped items stay backstage.
- [ ] Visuals are useful, not decorative.

## Validation

- [ ] Search for host-specific model or app names and justify any matches.
- [ ] Check there are no XML-style tags in the skill files.
- [ ] Run `find SKILL_DIR -type f -maxdepth 3` and confirm only useful skill files exist.
- [ ] Check every link from `SKILL.md` resolves to an existing reference.
- [ ] Compare CLI command examples with `cli --help`.
- [ ] Test obvious trigger, paraphrased trigger, and unrelated non-trigger prompts conceptually.
- [ ] Run repository checks after edits.
