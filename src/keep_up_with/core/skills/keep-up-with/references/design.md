# Design

## Purpose

Use this file as the baseline for custom thread visuals.

The baseline should make visuals clear, consistent, and fast to produce. It should not force every event into one fixed look. Palette, type feel, surface treatment, motif, and small styling details should come from the event and its source material.

Source visuals still come first as raw material. The camera-ready asset still goes through this visual system.

## Reference Backbone

Before building final visuals, read [`render.html`](render.html) and use it as the backbone for the asset set. Copy [`visual-kit.css`](visual-kit.css) and [`visual-kit.js`](visual-kit.js) beside the event renderer and keep them unchanged unless the event genuinely needs a different visual system.

Every visual post should have one story renderer in `outputs/assets/render.html`, even when the main material is a source screenshot, chart, product image, video frame, GIF, or clip. Select posts with `?visual=post-N`. Original material belongs inside the frame: cropped into the proof area, paired with labels, blended with a small chart, or used as the main evidence object.

The final visuals do not need to copy the examples, but they should look like they belong to the same family. Start from that shell and adapt it to the event's source material. Diverge only when the source asset, crop, diagram, or spatial problem genuinely needs another structure, and still keep the asset set visually tied to the same frame system.

## Design Read

Before building a custom visual, write a one-line design direction in `research/notes.md`:

```text
Design direction: <event/source type> for <audience>, using <source cues>, with <density/style>.
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

## Icons And Generated Graphics

Treat each rendered asset like a slide. Use Lucide icons for small symbols inside the frame: status dots with meaning, source-type labels, repo/file/product cues, arrows, warnings, checks, and tool actions. Keep them line-based, quiet, and aligned with the typography. Do not draw one-off icons when a Lucide icon already fits.

If a slide needs a raster graphic that source material cannot provide, use $imagegen for photos, illustrations, textures, mockups, cutouts, or other bitmap pieces. Treat the generated image as source material inside `render.html`: crop it, label it, pair it with data, or blend it with custom components in the shared frame.

Prefer source assets, Lucide, and code-native SVG/HTML for data, icons, diagrams, and simple shapes. Do not use generated images as evidence, and do not use them for text-heavy charts or anything that needs exact labels.

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

For each visual asset:

1. Record what source material or custom data the visual uses, and what it explains.
2. Record the design direction.
3. Use `references/render.html`, `references/visual-kit.css`, and `references/visual-kit.js` as the backbone for the renderer shape and visual range.
4. Record the source palette/motif/type cues you used.
5. Build one renderer in the event workspace at `outputs/assets/render.html`; put source crops, screenshots, GIFs, video frames/clips, and custom components inside that renderer.
6. Save the renderer, source data, raw media parents, and final assets.
7. Render still assets at the target size, usually `1280x720`; export motion assets from the same framed composition when the post needs GIF or video.
8. Inspect full-size and thumbnail-size outputs.

If a visual is only decorative, cut it.
