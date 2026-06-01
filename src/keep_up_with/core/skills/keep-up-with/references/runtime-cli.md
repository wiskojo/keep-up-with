# Runtime CLI

Run `cli --help` for details. Output is JSON/JSONL unless help text.

| Command | Use |
| --- | --- |
| `cli events list` | Event history |
| `cli events show ID` | One event |
| `cli inbox list` | Pending work |
| `cli inbox show ID` | One inbox item |
| `cli inbox dismiss ID` | Clear handled item |
| `cli subs list` | Enabled subscriptions |
| `cli tools` | Source tools |
| `cli message send --text ...` | Send message |
| `cli message list` | Recent messages |
| `cli message channels` | Channels |
| `cli thread create --channel ... --title ... --text ...` | New thread |
| `cli thread append --thread-id ... --text ...` | Thread update |
| `cli thread list --channel ...` | Channel threads |
| `cli thread show THREAD_ID` | Thread messages |
| `cli space channels list/create/rename/move` | Channels |
| `cli space sections list/create/rename/move` | Sections |

YouTube frames:

```bash
cli tools youtube frames URL 00:01:23 --output-dir threads/YYYY-MM-DD-HHMM-slug/research/artifacts
```

Rules:

- Inbox is the work queue.
- Events are durable history.
- Inspect primary artifacts before claims.
- DM for lightweight updates; channels/threads for stories.
