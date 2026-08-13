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

The same endpoint accepts `Authorization: Basic base64(key:secret)`; create keys at app.scenario.com/settings/api. Build the header per the [connection guide](https://mcp.scenario.com/docs) and keep it out of the conversation: reference an environment variable in the client config (`--header "Authorization: Basic $SCENARIO_MCP_AUTH"`) or edit the config file directly. Never ask an agent to collect, encode, or echo a key or secret.
