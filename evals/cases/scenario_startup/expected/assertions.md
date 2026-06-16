# Expected: scenario_startup

- With no injected events, startup produces only DM output and no threads.
- The agent sends a short getting-situated message, then a brief ready message after checking local context, subscriptions, and channel layout.
- The ready message says what it understands, that it is ready to keep up with what is configured, and that it will surface important events. It does not ask onboarding questions.
