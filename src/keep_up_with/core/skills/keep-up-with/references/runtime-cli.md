# Runtime CLI

Use `cli --help` when command details are uncertain. CLI output is JSON or JSONL unless the command is help text.

## Commands

| Command | Use |
| --- | --- |
| `cli events list` | Read durable event history, oldest first. |
| `cli events show ID_OR_PREFIX` | Inspect one event. |
| `cli inbox list` | Review pending items that still need attention. |
| `cli inbox show ID_OR_PREFIX` | Inspect one pending item. |
| `cli inbox dismiss ID_OR_PREFIX` | Remove a handled item from the inbox. |
| `cli subs list` | Inspect enabled source subscriptions and watched values. |
| `cli tools` | Inspect source-specific tools. |
| `cli message send --text ...` | Send a user-facing message. Defaults to DM. |
| `cli message list` | Read recent messages. Defaults to DM. |
| `cli message channels` | List available messaging channels. |
| `cli thread create --channel ... --title ... --text ...` | Create a story thread in a channel. |
| `cli thread append --thread-id ... --text ...` | Add an update to an existing thread. |
| `cli thread list --channel ...` | List threads in a channel. |
| `cli thread show THREAD_ID` | Read a thread and recent messages. |
| `cli space channels list` | List channels in the communication space. |
| `cli space channels create/rename/move` | Manage channels. |
| `cli space sections list` | List channel sections. |
| `cli space sections create/rename/move` | Manage sections. |

## Rules

- Treat the inbox as a work queue. Dismiss an item only after it is handled or intentionally ignored.
- Treat events as durable history. Do not delete or rewrite events from the agent.
- Use source tools to inspect primary artifacts before making claims.
- For messaging commands, prefer the default DM only for lightweight updates. Use configured channels and threads when a story has a natural home.
