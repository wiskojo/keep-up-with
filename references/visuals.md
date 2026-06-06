# Visuals

## Principle

Use source visuals first. Authors, maintainers, and early reactions often already made the best chart, demo frame, screenshot, clip, table, or diagram for the point they are making.

Make your own visual only when the source material does not fit the highlight, is stale, is too noisy to read, or when a custom comparison, timeline, crop, table, or summary genuinely makes the point clearer.

Do not use visuals as decoration. Do not use generated images as evidence.

## Inventory

Before drafting the thread, check for visuals in:

- the original post and attached media
- linked blog posts, papers, docs, demos, notebooks, model cards, datasets, leaderboards, and release notes
- repos, READMEs, issues, PRs, examples, benchmark pages, and dashboards
- social posts, quote posts, Reddit comments, forum threads, YouTube videos, and newsletters
- videos, GIFs, demo recordings, slide decks, screenshots, tables, and chart images embedded in the page

Save useful raw parents in `research/artifacts/` as soon as you find them. Put only camera-ready assets in `outputs/assets/`.

Record the visual inventory in `research/notes.md`: what existed, what you used, what you rejected, and why.

## Extraction Order

Prefer the least lossy source path available:

1. Download or save the original image, chart, video frame, table, or document asset when the page exposes it directly.
2. For webpages, use browser automation to screenshot the chart or figure element itself instead of hand-cropping a viewport.
3. For videos or demos, capture the exact frame or short clip that carries the point, with the timestamp in notes.
4. For flat screenshots, crop from the screenshot with normalized coordinates or an auto-detected crop box.
5. Use manual pixel offsets only as a fallback, and write the crop box down so it can be reproduced.
6. Create a custom visual only after the source-visual options fail or a synthesis visual is clearly better.

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

For screenshot-only inputs, prefer normalized crop boxes over raw pixels:

```json
{ "x": 0.189, "y": 0.339, "w": 0.671, "h": 0.444 }
```

Convert to pixels at runtime:

```text
x_px = round(image_width * x)
y_px = round(image_height * y)
w_px = round(image_width * w)
h_px = round(image_height * h)
```

This makes the crop reusable when the same page is captured at a different resolution. It still breaks if the layout changes, so use DOM element screenshots for live webpages when available.

## Cropping Tools

Prefer tools that use the natural rectangle order: left, top, width, height.

ImageMagick:

```sh
magick identify -format "%w %h\n" input.png
magick input.png -crop 1470x1080+415+825 +repage output.png
magick input.png -fuzz 3% -trim +repage output.png
```

libvips:

```sh
vips crop input.png output.png 415 825 1470 1080
```

macOS `sips` fallback:

```sh
sips -c 1080 1470 --cropOffset 825 415 input.png --out output.png
```

`sips` works, but it is easier to make mistakes because it takes height/width and y/x ordering. Use it only when better crop tools are unavailable.

## Custom Visuals

Use a custom visual when:

- the best source visual is stale, misleading, cropped badly, unreadable, or unavailable
- the thread needs a comparison that no source made
- multiple source facts need to be combined into one compact table, chart, timeline, or map
- a source crop would include too much irrelevant page furniture

When making a custom visual:

- base it on saved source data or clearly attributed facts
- keep the design simple enough to read in a thread
- do not invent precision or imply evidence that the source does not support
- save the source data and the rendered output
