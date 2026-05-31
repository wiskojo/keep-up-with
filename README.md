# Keep Up With

Keep Up With augments Codex with event streams, source tools, and communication tools for keeping up with topics over time.

Codex is the agent. This repo provides the local runtime around it: setup, config, integrations, subscriptions, events, inbox, communication tools, and the gateway that pushes notifications into the Codex thread.

## Install

```bash
uv sync
uv tool install -e .
```

## Commands

```bash
kuw setup
kuw start
kuw status
kuw stop
kuw reset
```
