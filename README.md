<p align="center">
  <img src="https://raw.githubusercontent.com/wiskojo/keep-up-with/main/assets/logo.png" alt="keep-up-with logo" width="120" />
</p>

<h1 align="center">keep-up-with</h1>

<p align="center">
  <strong>Don’t fall behind. Keep up with everything that’s happening.</strong><br />
  Turn Codex into your personal 24/7 assistant for staying on top of the latest developments.
</p>

---

## Why This Exists

Everything moves so fast these days that it’s hard to keep up, especially in AI. Keeping up with things can feel like a full-time job. The links keep piling up: X threads, Reddit posts, YouTube talks, papers, repos, changelogs, blog posts. You save the promising ones, then “read later” turns into never. **keep-up-with** does the work you don’t have time for: it opens the links, checks the source material, follows the context, and turns the useful parts into something you can understand quickly, and sends it to you on Discord. Low-signal items get ignored. Small changes become short updates. Dense sources, public reactions, follow-ups, and related launches become threads, so the story is organized instead of becoming another tab you meant to read.

If [last30days-skill](https://github.com/mvanhorn/last30days-skill) is what you run when you finally ask "what did I miss?", **keep-up-with** is the always-on version. It keeps tabs on everything and updates you so you never fall behind. You can use it with your existing OpenAI (ChatGPT/Codex) subscription (OAuth) to keep watch while you focus on other things.

![How keep-up-with keeps watch](https://raw.githubusercontent.com/wiskojo/keep-up-with/main/assets/overview.png)

Think of it like having a hard-working intern tracking noisy feeds all day, then sharing only the interesting and relevant updates.

- Small useful items become short posts.
- Bigger launches, papers, talks, reactions, or ongoing stories become threads.
- Follow-ups append to the existing story instead of starting over.
- Related events can also become stories, so bigger trends and patterns are easier to spot.

## What It Looks Like

**keep-up-with** shares updates in the messaging platform you already use (only Discord for now). It lives alongside your normal conversations, so it feels familiar, works from everywhere, and can be shared with friends, teammates, or coworkers when you want a common space.

| Shape | What shows up |
| --- | --- |
| **Short update** | One compact message with the source link and a useful visual when available. |
| **Deep-dive thread** | A focused thread for a launch, paper, talk, report, or messy public reaction. |
| **Story follow-up** | A new event gets appended to an existing thread when it changes the same story. |
| **Shared server** | Friends, teammates, or coworkers can use the same topic channels and nudge what gets covered. |

The result should be a stream that is easier to follow: fewer items, more context, useful visuals and artifacts, and updates that build on what you already know instead of repeating the whole story every time.

## How It Works

![keep-up-with workflow](https://raw.githubusercontent.com/wiskojo/keep-up-with/main/assets/workflow.png)

The sources you configure are watched continuously. When something new appears, it becomes an event in the inbox. Codex investigates the event, checks the surrounding context, gathers useful artifacts, and decides what should happen next: skip it, share a quick update, open a new thread, or append to an existing story.

Importantly, **keep-up-with** connects follow-ups, reactions, and related stories over time instead of treating every event like a separate one-off. It keeps track of what you have already seen, so updates can focus on what changed instead of repeating the whole story.

## Integrations

**keep-up-with** comes with built-in integrations. You can enable or disable them based on what you want it to watch, fetch, and inspect. Subscribed events arrive through the bridge, and the agent uses configured tools through the agent-facing `kup-cli`.

| Source | What it is good for | Requires |
| --- | --- | --- |
| **X** | Fast reactions, expert threads, launch posts, quote-post debate, and early attention signals. | `X_BEARER_TOKEN` |
| **Reddit** | Practitioner reactions, skeptical comments, troubleshooting, product complaints, and aggregate sentiment from people actually trying things. | `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET` |
| **YouTube** | Talks, demos, explainers, launch walkthroughs, and long-form context that is easier to search through transcripts than watch end to end. | `YOUTUBE_API_KEY` |
| **Web and RSS** | Official announcements, changelogs, engineering blogs, research posts, docs, and source pages that anchor the story. | None |
| **arXiv** | Papers, figures, source bundles, and technical claims that need direct inspection instead of summary-by-headline. | None |
| **GitHub repos** | What actually shipped: README, releases, examples, star history, issues, and whether a project looks real or abandoned. | None |
| **Images** | Cropping, inspecting, and preparing source visuals so updates are easier to understand at a glance. | None |
| **Video** | Pulling frames, clips, transcripts, and short demos from video sources or local files. | None |
| **Raindrop** | Your saved links and bookmarks, so the agent can connect new items to things you already cared enough to save. It can also act as an ingestion path if you want to use **keep-up-with** as a lightweight second brain. | `RAINDROP_TOKEN` |
| **Browser history** | Local context from what you have recently read or revisited, when you choose to enable it. | None |

A starter AI preset is included out of the box. It is tuned for AI news and technical updates, and it sets up both subscriptions and a Discord channel layout so you have a useful starting point instead of a blank config.

> [!NOTE]
> The default AI preset is tuned for ChatGPT Pro users on the 5x or 20x plan and can consume substantial usage.

## Quickstart

Install **keep-up-with**:

```bash
uv tool install keep-up-with
```

Run setup:

```bash
kup setup  # set up Discord, integrations, presets, and workspace defaults
```

Setup writes your config to `~/.keep-up-with/config.toml`. You can edit it directly, or ask the agent to update it for you after startup.

Start it:

```bash
kup start  # begin watching sources and handling events
```

If everything is configured and working correctly, your agent should greet you on Discord shortly.

## Commands

`kup` is for the human running **keep-up-with**.

```bash
kup setup  # run the setup wizard
kup start  # start the local service
kup status # check the daemon, gateway, thread, and event counts
kup stop   # stop the local service
kup reset  # reset local state while keeping setup files
```

`kup-cli` is for the agent. It is the first-party command Codex uses while working: reading events, handling the inbox, fetching source material, and sending messages or threads. You can also run it yourself for debugging.

```bash
kup-cli events list          # search or list stored events
kup-cli inbox list           # see pending events waiting for action
kup-cli tools --help         # list configured tools
kup-cli message send --help  # inspect message publishing options
kup-cli thread create --help # inspect story thread options
```

## License

MIT. See [LICENSE](LICENSE).
