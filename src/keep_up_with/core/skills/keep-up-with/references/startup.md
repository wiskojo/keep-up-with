# Startup And Onboarding

Read this when the agent starts, restarts, or resumes after a reset.

## Flow

1. Send a brief first signal:
   ```bash
   cli message send --text "Hey, I'm up. I'm going to take a few minutes to get situated and I'll follow up shortly."
   ```
2. Read `USER.md` and `MEMORY.md`.
3. Run `cli --help` and learn the available command groups.
4. Inspect configured sources and messaging space:
   ```bash
   cli subs list
   cli message channels
   cli space sections list
   cli space channels list
   cli inbox list
   ```
5. Follow up through `cli message send --text ...` once you have useful context.

## Follow-Up Shape

Keep it natural:

- say what you understand so far
- ask only what is important or unclear
- do not list internal files, commands, or setup steps unless the user asks

If everything is clear, say so and start working from events normally.
