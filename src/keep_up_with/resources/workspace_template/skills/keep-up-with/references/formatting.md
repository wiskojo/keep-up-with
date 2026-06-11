# Formatting

User-facing messages render a limited Markdown set. Use it to break up text walls and make posts scannable. Do not use anything outside this list — unsupported syntax renders as literal characters.

## Supported

- Italics: `*text*` or `_text_`
- Bold: `**text**`; bold italics: `***text***`
- Underline: `__text__`
- Strikethrough: `~~text~~`
- Headers: `# H1`, `## H2`, `### H3` at line start
- Subtext: `-# small gray text` at line start
- Bullet lists: `-` or `*`; numbered lists: `1.`; indent two spaces to nest
- Quotes: `> quoted line`; `>>>` quotes everything after it
- Inline code: `` `code` ``; code blocks: triple backticks with an optional language
- Masked links: `[label](https://example.com)`
- Suppressed link previews: `<https://example.com>` — wrap bare URLs in angle brackets when an embed preview would add noise
- Spoilers: `||hidden until clicked||`
- Mentions: `<@user_id>` for a user, `<#channel_or_thread_id>` for a channel or thread — renders as a clickable reference

## Not supported

- Tables — use short bullets with bold labels, or attach a cropped image of the real table
- Horizontal rules, footnotes, and definition lists
- Inline images `![alt](url)` — attach the file instead
- HTML and LaTeX

## Use

- Prefer short paragraphs and blank lines over long blocks.
- Bold the few words that carry the point, not whole sentences.
- Use headers sparingly — they render large; reserve them for major sections of a long post.
- Use block quotes for quoted reactions and sources, and code blocks for code, commands, numbers, and raw output.
- Suppress link previews on secondary links; let the main link embed.
