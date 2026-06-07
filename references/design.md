# Design

## Purpose

Use this file as the baseline for custom thread visuals.

The baseline should make visuals clear, consistent, and fast to produce. It should not force every event into one fixed look. Palette, type feel, surface treatment, motif, and small styling details should come from the event and its source material.

Source visuals still come first. Use this guide when a custom visual is justified.

## Reference Backbone

Before building custom visuals, read [`render.html`](render.html) and use it as the backbone for the asset set. The examples define the expected shape: a `1280x720` editorial frame, source label, short kicker, large title, brief subhead, one main proof area, direct labels, restrained cards, and a bottom source note.

The final visuals do not need to copy the examples, but they should look like they belong to the same family. Start from that shell and adapt it to the event's source material. Diverge only when the source asset, crop, diagram, or spatial problem genuinely needs another structure.

## Design Read

Before building a custom visual, write a one-line design read in `research/notes.md`:

```text
Reading this as: <event/source type> for <audience>, using <source cues>, with <density/style>.
```

Check:

- source material: screenshots, charts, site UI, docs, repos, logos, product surfaces, social posts
- audience: technical readers, operators, researchers, customers, open-source maintainers, investors
- tone: sober, launch-like, academic, developer-tool, consumer, public-sector, playful, contentious
- constraints: accessibility, evidence quality, chart density, source trust, brand safety

If the source already has a strong design language, adapt it. If the source is plain or messy, use the neutral baseline and one restrained accent.

## Baseline

The baseline aesthetic is modern, quiet, and lightly editorial. It should feel designed, but not branded.

Default canvas:

- `1280x720`
- 48-64px outer margin
- warm off-white, cool off-white, or near-black background
- one clear title
- one dominant proof object
- small source note
- no decorative filler

Default composition:

- title top-left or left rail unless the source strongly suggests another structure
- chart/table/crop carries most of the frame
- labels sit directly on marks where possible
- legends only when direct labels would make the visual worse
- use whitespace, dividers, and alignment before adding cards
- prefer one strong data object over several equal boxes
- use asymmetry when it improves scan order

Default tokens:

```css
--surface: #fbfaf7;
--card: #fffdf8;
--ink: #181713;
--muted: #706a5e;
--line: #ded6c8;
--neutral-strong: #8b8274;
--neutral-soft: #d8d1c5;
--accent: #3157a4;
--accent-soft: #e8eef9;
--success: #2f7d5c;
--warning: #c87913;
--danger: #b83b5b;
```

Treat these as fallback tokens. Replace `--accent` with the source accent. Adjust neutrals only when the source clearly leans warm, cold, dark, editorial, terminal-like, academic, or consumer.

Use this visual grammar by default:

- background: plain or a very subtle paper/screen tint
- rules: 1px lines, usually low contrast
- cards: only for contained evidence objects, 6-10px radius, no heavy shadow
- type: strong title, small precise labels, tabular numbers
- color: tinted neutrals, one source accent, and semantic warning/success/error colors only when those meanings are present
- motion/texture: none for static thread assets unless the source itself depends on it

## Source Styling

Borrow simple cues from the event source:

- palette: one source accent, plus neutrals
- typography: plain UI sans, technical mono, editorial serif, dense academic labels, or product-marketing display type when the source supports it
- surface: flat docs, dark terminal, paper/report, product UI, repo chrome, chart card, presentation slide, notebook, dashboard
- shape: square, soft, pill, table-like, code-block, terminal, dense grid
- motif: verified logo/icon, source crop detail, repeated chart mark, repo/file symbol, tiny abstract event marker

Do not invent official marks, mascots, product UI, badges, or logos. If the source asset is not verified, omit it.

The visual should feel related to the source without pretending to be official collateral.

## Taste Checks

Run these before shipping:

- If this sits beside the examples in `render.html`, does it feel like the same visual system?
- Does this look like the event, or just a generic chart?
- Did you pick the palette from the source, not from habit?
- Is there only one main accent unless the data needs more?
- Are shadows, cards, borders, and patterns doing real hierarchy work?
- Would the visual still read at thumbnail size?
- Is the typography intentional, or did you accept the browser/default font stack without thinking?
- Did you avoid common model defaults: AI-purple gradients, glassy blobs, centered hero language, three equal cards, noisy decoration, random dark mesh?

Use cards only when framing helps comprehension. Otherwise use open layout, section rules, or aligned groups.

## Typography

Typography should match the source and use case:

- developer/tool/source-code event: system sans plus a restrained mono
- research/paper/benchmark event: sober sans, compact labels, table discipline
- consumer/product event: source-like display face only when the source already uses one
- editorial/report event: serif only when the source genuinely has that tone

Modern-minimal default:

- title: 44-56px, 700-800 weight, tight but readable line height
- body: 15-18px, muted, short
- labels: 11-13px
- chart values: 14-18px or 44-76px for one headline number
- use tabular numbers when the renderer supports it

Keep display text short. Do not scale type with viewport width. Use `letter-spacing: 0` unless matching an existing source treatment.

Use font weight, size, and position before using color for emphasis.

## Data Style

For charts and data-heavy visuals:

- use explicit scales
- show uncertainty when the source provides it
- do not invent precision
- use direct labels
- keep axes quiet but readable
- avoid unlabeled color meanings
- reserve warning/danger colors for real caveats or failures

If a benchmark or measurement has caveats, show them in the visual structure or source note. Do not hide measurement limits behind pretty styling.

## Custom Visual Workflow

For each custom visual:

1. Record why the custom visual beats the best source visual, what it explains, and what sources or data it uses.
2. Record the design read.
3. Use `references/render.html` as the backbone for the renderer shape and visual range.
4. Record the source palette/motif/type cues you used.
5. Build one small renderer in the event workspace, usually `outputs/assets/render.html`.
6. Save the renderer, source data, and final PNGs.
7. Render at the target size, usually `1280x720`.
8. Inspect full-size and thumbnail-size PNGs.

If a custom visual is only decorative, cut it.
