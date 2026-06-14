# Visuals

## Principle

Use visuals extracted from source material only.

A visual should help verify, explain, or make a specific highlight easier to scan. It should come from the event itself or from material discovered during research: source pages, papers, repos, docs, dashboards, posts, comments, videos, demos, slides, screenshots, charts, tables, diagrams, thumbnails, GIFs, or frames.

Default to inclusion. Every useful visual in the source material belongs in the output — if a source offers ten useful figures, use all ten. The bar is per-visual quality: readable, relevant, tied to a specific claim. Never ration by count, and never compress a visual-rich source into a short text summary when separate charts or tables carry separate claims. Outside-context visuals can add perspective, but they do not replace source coverage.

Do not create custom graphics for now. Do not make generated images, synthetic charts, SVG summaries, new diagrams, timelines, maps, tables, or visual reinterpretations. If the sources do not contain a useful visual, ground the post in source quotes instead — one or many, interleaved with the commentary the way visuals would be.

## Inventory

Before drafting the thread, check for visuals in:

- the original post and attached media
- linked blog posts, papers, docs, demos, notebooks, model cards, datasets, leaderboards, and release notes
- repos, READMEs, issues, PRs, examples, benchmark pages, and dashboards
- social posts, quote posts, Reddit comments, forum threads, YouTube videos, and newsletters
- videos, GIFs, demo recordings, slide decks, screenshots, tables, and chart images embedded in pages

Save useful raw source material in `research/artifacts/` as soon as you find it. Put only final cropped or extracted assets in `outputs/assets/`.

Record the visual inventory in `research/notes.md`: what existed, what you used, where it came from, what claim it supports, and why it fits the post.

## Extraction Order

Prefer the least lossy source path available:

1. Download or save the original image, chart, video frame, table, or document asset when the page exposes it directly.
2. For webpages, capture the page with `cli tools web screenshot` and crop to the chart, figure, table, or card; use element screenshots instead when browser automation is available.
3. For videos or demos, capture the exact frame, GIF, or short clip that carries the point, with the timestamp in notes.
4. For flat screenshots, crop from the screenshot with normalized coordinates.
5. Use manual pixel offsets only as a fallback, and write the crop box down so it can be reproduced.

## Webpage Captures

For live pages, capture a full-page screenshot, find the crop box with a grid, then crop:

```sh
cli tools web screenshot "https://example.com/post" --output research/artifacts/page.png
cli tools image grid research/artifacts/page.png research/artifacts/page-grid.png
cli tools image crop research/artifacts/page.png outputs/assets/post-2-chart.png 0.18,0.33,0.67,0.44
```

If the screenshot is too tall to inspect accurately, do not guess from the thumbnail. Make a grid image, use browser automation for element screenshots, or crop section-by-section and inspect each crop before it becomes a final asset.

If browser automation (for example Playwright) is set up, element screenshots are less lossy than full-page crops. Good targets: `figure`, `img`, `svg`, a chart container found by heading text, a bordered card or table around the chart, or a video/canvas element.

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

## Screenshot Crops

For screenshot-only inputs, use a crop helper when the same page may be captured at different resolutions:

```sh
cli tools image crop \
  research/artifacts/source-screenshot.png \
  outputs/assets/post-2.png \
  0.189,0.339,0.671,0.444
```

If you need help finding the normalized crop box, generate a guide image first:

```sh
cli tools image grid \
  research/artifacts/source-screenshot.png \
  research/artifacts/source-screenshot-grid.png
```

Use the percentage labels and guide lines to choose the normalized `x,y,w,h` values for `cli tools image crop`.

## Video Frames And Clips

The `video` tools take any video URL (YouTube, X, Reddit, direct media links) or a local file. They extract without saving the raw video — only the frames, clips, and GIFs you request are written; never persist raw video files:

```sh
cli tools video info "VIDEO_URL"
cli tools video frames "VIDEO_URL" 00:01:23 00:02:10 --output-dir research/artifacts/video
cli tools video clip "VIDEO_URL" 00:01:23 6 outputs/assets/post-2-clip.mp4
cli tools video clip "VIDEO_URL" 00:01:23 6 outputs/assets/post-2-crop.mp4 --crop 960:540:160:90
cli tools video gif "VIDEO_URL" 00:01:23 4 outputs/assets/post-2.gif
```

## Final Assets

Final assets should be direct source extracts or crops:

- source screenshots, charts, product surfaces, repo views, tables, or diagrams
- video frames, GIFs, clips, or demo recordings
- paper figures, leaderboard crops, screenshots of comments, or issue excerpts

Before using a visual, inspect it at full size and thumbnail size; never attach the first crop without checking it. Crop the whole figure, table, card, frame, or comment needed for the claim: title, axes, labels, legend, caption or footnote when relevant. Adjacent prose, clipped text, missing labels, excess page chrome, or off-center framing means the crop is not final; recrop it or skip it. For reports, studies, dashboards, and long posts, inventory the figures first; extract each high-value chart or table separately instead of using one overview image. If a visual is only decorative, cut it.

Attach each visual to the post whose claim it supports.
