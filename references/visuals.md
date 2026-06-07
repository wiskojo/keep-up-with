# Visuals

## Principle

Pick the visual that best explains the highlight.

Source visuals are useful when they show the artifact, claim, result, product, or evidence directly. Custom visuals are useful when they compress, compare, sequence, or translate the research better than a raw screenshot.

Do not use visuals as decoration. Custom or generated visuals can explain or synthesize; they are not evidence unless the underlying source or data is cited.

## Inventory

Before drafting the thread, check for visuals in:

- the original post and attached media
- linked blog posts, papers, docs, demos, notebooks, model cards, datasets, leaderboards, and release notes
- repos, READMEs, issues, PRs, examples, benchmark pages, and dashboards
- social posts, quote posts, Reddit comments, forum threads, YouTube videos, and newsletters
- videos, GIFs, demo recordings, slide decks, screenshots, tables, and chart images embedded in the page

Save useful raw parents in `research/artifacts/` as soon as you find them. Put only camera-ready assets in `outputs/assets/`.

Record the visual inventory in `research/notes.md`: what existed, what you used or built, and what each visual is meant to convey.

## Extraction Order

Prefer the least lossy source path available:

1. Download or save the original image, chart, video frame, table, or document asset when the page exposes it directly.
2. For webpages, use browser automation to screenshot the chart or figure element itself instead of hand-cropping a viewport.
3. For videos or demos, capture the exact frame or short clip that carries the point, with the timestamp in notes.
4. For flat screenshots, crop from the screenshot with normalized coordinates or an auto-detected crop box.
5. Use manual pixel offsets only as a fallback, and write the crop box down so it can be reproduced.
6. Build a custom visual when it is the clearest way to explain, compare, or summarize the highlight.

## Webpage Crops

For live pages, avoid raw pixel trial and error when possible. Use element screenshots.

Good targets:

- `figure`
- `img`
- `svg`
- a chart container found by heading text
- a bordered card or table around the chart
- a video element or canvas element

Playwright-style pattern:

```js
const chart = page.locator('text=DeepSWE tasks are larger').locator('..');
await chart.screenshot({ path: 'outputs/assets/post-2-task-shape.png' });
```

If the DOM is awkward, list candidate elements and their bounding boxes, then crop from those boxes:

```js
const boxes = await page.locator('figure, svg, img, canvas').evaluateAll(nodes =>
  nodes.map((node, i) => {
    const r = node.getBoundingClientRect();
    return { i, tag: node.tagName, x: r.x, y: r.y, w: r.width, h: r.height };
  })
);
```

Use full-page screenshots only to locate material or when element screenshots are blocked.

## Screenshot Crops

For screenshot-only inputs, use a crop helper when the same page may be captured at different resolutions:

```sh
node scripts/crop-image.mjs \
  --in research/artifacts/source-screenshot.png \
  --out outputs/assets/post-2.png \
  --box 0.189,0.339,0.671,0.444
```

## Video Frames And Clips

When dealing with videos, you can extract useful frames, videos, or gifs with:

```sh
cli tools youtube frames "VIDEO_URL" 00:01:23 00:02:10 --output-dir research/artifacts/video
cli tools youtube download "VIDEO_URL" --output-dir research/artifacts/video
cli tools youtube clip "VIDEO_URL" 00:01:23 6 outputs/assets/post-2-clip.mp4
cli tools youtube clip "VIDEO_URL" 00:01:23 6 outputs/assets/post-2-crop.mp4 --crop 960:540:160:90
cli tools youtube gif "VIDEO_URL" 00:01:23 4 outputs/assets/post-2.gif
```

## Custom Visuals

Use a custom visual when it helps the user understand the point, for example:

- the thread needs a comparison that no source made
- multiple source facts need to be combined into one compact table, chart, timeline, or map
- a mechanism, process, or tradeoff needs to be simplified
- the useful part is spread across several source materials
- the source visual is stale, misleading, cropped badly, unreadable, or unavailable
- a source crop would include too much irrelevant page furniture

Use the skills in $build-web-data-visualization and follow the baseline plus source-style pass in [design.md](design.md). For examples of the expected artifact shape and visual range, study [render.html](render.html).

Implementation defaults:

- Put the structured data in the renderer or a nearby JSON file.
- Use SVG marks, direct labels, and explicit scales.
- Add `title`, `desc`, or surrounding text so the visual is accessible and inspectable.
- Render each visual to PNG at the target size, usually `1280x720`.
- Inspect each PNG at full size and thumbnail size before using it.
- Save the renderer, source data, and final PNGs.

Render with:

```sh
node scripts/render-visuals.mjs \
  --html outputs/assets/render.html \
  --out-dir outputs/assets \
  --visuals post-1,post-2,post-3
```

Vanilla SVG is fine for simple static bar charts. Install D3 only when the D3-specific skill lens above applies, using `npm install d3` or `pnpm add d3` in the event workspace.
