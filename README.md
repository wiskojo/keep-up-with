<p align="center">
  <img src="assets/logo.png" alt="keep-up-with logo" width="120" />
</p>

<h1 align="center">keep-up-with</h1>

<p align="center">
  <strong>Keep up with everything that’s happening.</strong><br />
  Turn Codex into a 24/7 agent that reads your sources, tracks what changed, and helps you keep up with what’s going on.
</p>

---

## Why This Exists

Everything moves so fast these days that it’s hard to keep up, especially in AI. Keeping up with things can feel like a full-time job. The links keep piling up: X threads, Reddit posts, YouTube talks, papers, repos, changelogs, blog posts. You save the promising ones, then “read later” turns into never. **keep-up-with** does the work you don’t have time for: it opens the links, checks the source material, follows the context, and turns the useful parts into something you can understand quickly. Low-signal items get ignored. Small changes become short updates. Dense sources, public reactions, follow-ups, and related launches become threads, so the story is organized instead of becoming another tab you meant to read.

If [last30days-skill](https://github.com/mvanhorn/last30days-skill) is what you run when you finally ask "what did I miss?", **keep-up-with** is the always-on version. It keeps tabs on everything and updates you so you never fall behind. You can use it with your existing OpenAI (ChatGPT/Codex) subscription (OAuth) to keep watch while you focus on other things.

![How keep-up-with keeps watch](assets/overview.png)

Think of it like having a hard-working intern tracking noisy feeds all day, then sharing only the interesting and relevant updates.

- Small useful items become short posts.
- Bigger launches, papers, talks, reactions, or ongoing stories become threads.
- Follow-ups append to the existing story instead of starting over.
- Related events can become trend threads, so the bigger pattern is easier to see.

## What It Looks Like

**keep-up-with** sends updates into the messaging platform you already use (only Discord is supported for now). It lives next to your normal conversations, so you can read, reply, and share with other people.

| Shape | What shows up |
| --- | --- |
| **Short update** | One compact message with the source link and a useful visual when available. |
| **Deep-dive thread** | A focused thread for a launch, paper, talk, report, or messy public reaction. |
| **Story follow-up** | A new event gets appended to an existing thread when it changes the same story. |
| **Shared server** | Friends, teammates, or coworkers can use the same topic channels and nudge what gets covered. |

The result should be a stream that is easier to follow: fewer items, more context, useful visuals and artifacts, and updates that build on what you already know instead of repeating the whole story every time.

## How It Works

![keep-up-with workflow](assets/workflow.png)

Sources create events. Events land in an inbox. Codex triages them, checks the source, gathers artifacts, and chooses what to do: skip, post a quick update, open a new thread, or append to an existing story.

That last part matters. **keep-up-with** should connect follow-ups, reactions, and related launches over time instead of treating every link like a separate one-off. It knows what you already know so you don't keep seeing the same thing over and over again, only the meaningful deltas.

## Examples

TODO: 2x2 Grid of screenshots from Discord

## Sources

**keep-up-with** can watch sources directly, then inspect them again during research.

| Source | What it can use |
| --- | --- |
| **X** | Posts, self-threads, quoted posts, metrics, and media. |
| **Reddit** | Posts, comments, scores, links, and media. |
| **YouTube** | Videos, channels, transcripts, frames, clips, and short demos. |
| **Web and RSS** | Blogs, changelogs, launch pages, docs, screenshots, and linked pages. |
| **arXiv** | Papers, source bundles, figures, and Markdown exports. |
| **GitHub repos** | READMEs, releases, repo metadata, screenshots, and star-history charts. |
| **Personal Data** | Raindrop bookmarks and local browser history, when enabled. |

One basic AI preset is provided out of the box. The AI preset is tuned for AI news and technical updates out of the box: frontier labs, models, coding agents, developer tools, evals, research, security, business, and policy. It will help add subscriptions and configure your Discord server. You can edit the subscriptions and channel routing in `~/.keep-up-with/config.toml`, or ask the agent to update that file for you.

## Quickstart

From a local clone:

```bash
uv sync              # install the project dependencies
uv tool install -e . # expose the kup and kup-cli commands
```

Run setup:

```bash
kup setup # choose messaging, integrations, presets, and workspace defaults
```

Start it:

```bash
kup start # begin watching sources and handling events
```

## Commands

`kup` is for the person running **keep-up-with**.

```bash
kup setup  # run the setup wizard
kup start  # start the local service
kup status # check the daemon, gateway, thread, and event counts
kup stop   # stop the local service
kup reset  # reset local state while keeping setup files
```

`kup-cli` is the first-party command Codex uses while it works. It reads events, handles the inbox, fetches source material, and sends messages or threads. You can run it yourself for debugging.

```bash
kup-cli events list          # search or list stored events
kup-cli inbox list           # see pending events waiting for action
kup-cli tools --help         # list source and media tools
kup-cli message send --help  # inspect message publishing options
kup-cli thread create --help # inspect story thread options
```
