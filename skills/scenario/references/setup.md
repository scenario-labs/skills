# Connection setup

Endpoint: `https://mcp.scenario.com/mcp` (Streamable HTTP).

## OAuth (preferred)

Add the endpoint and sign in with a Scenario account when the client prompts; no credentials pass through the conversation.

Claude Code:

```bash
claude mcp add --transport http scenario https://mcp.scenario.com/mcp
```

Cursor / VSCode (`mcp.json`):

```json
{ "mcpServers": { "scenario": { "url": "https://mcp.scenario.com/mcp" } } }
```

## API keys (headless or CI)

Where nobody is present to complete the OAuth prompt, the same endpoint also authenticates with a Scenario API key, created at app.scenario.com/settings/api. Wiring one into a client is an operator task done by hand: the [connection guide](https://mcp.scenario.com/docs#using-an-api-key) carries the current steps for each client.

Credentials stay out of the conversation. An agent asked to set this up points to the guide and stops there. It does not ask for a key or secret, does not place one in a command, a config file, or a message, and does not repeat one that appears in its context.
