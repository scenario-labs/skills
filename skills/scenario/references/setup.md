# Connection setup

Endpoint: `https://mcp.scenario.com/mcp` (Streamable HTTP). Every fact here is also on the public [connection guide](https://mcp.scenario.com/docs) and [troubleshooting page](https://mcp.scenario.com/docs/troubleshooting); when they disagree with this file, they win.

## Transport: native HTTP first

Clients with native Streamable HTTP support connect to the URL directly; that is the reliable path. `mcp-remote` (`npx mcp-remote@latest https://mcp.scenario.com/mcp`) is a stdio bridge for clients without native HTTP, it needs Node.js installed, and it is the usual source of repeated sign-in prompts and tokens that never persist. A client that offers both takes the native URL configuration.

## OAuth (preferred)

Add the endpoint and sign in with a Scenario account when the client prompts; no credentials pass through the conversation.

Claude Code (OAuth starts on first use; `/mcp` authenticates by hand):

```bash
claude mcp add --transport http scenario https://mcp.scenario.com/mcp
```

Claude Desktop (`claude_desktop_config.json`, then restart the app), Cursor (Settings, MCP; native OAuth and HTTP from 1.0), Windsurf (Cascade, Configure MCP):

```json
{ "mcpServers": { "scenario": { "url": "https://mcp.scenario.com/mcp" } } }
```

VS Code: Command Palette, `MCP: Add Server`, HTTP, the URL. Zed: `{ "context_servers": { "scenario": { "url": "https://mcp.scenario.com/mcp" } } }` in settings. Gemini CLI: the server in `~/.gemini/settings.json`, then `/mcp auth scenario`. claude.ai: Settings, Connectors, Add custom connector, the URL (paid plans). Codex and other clients: the standard URL through their CLI or configuration file.

Verify with a free call: "List my Scenario teams" should return `teams_list` output. `diagnostics_run` names the failing layer when it does not.

## Re-authenticating

A connection that worked and then fails, or a server-side authentication fix, needs a fresh handshake: clear the client's stored authorization and connect again before debugging anything else.

- Claude Code: `/mcp`, select Scenario, Clear authentication.
- Cursor: Settings, Tools & MCP, deactivate and reactivate the server.
- VS Code: Command Palette, `MCP: List Servers`, remove and re-add.
- Claude Desktop: Settings, Developer, Edit Config, remove and re-add the entry, restart.
- OpenCode: `opencode mcp logout scenario`, then `opencode mcp auth scenario`.

Claude Desktop reopening the browser on every message is orphaned `mcp-remote` processes: quit the app fully and reboot; if it persists, `pkill -f mcp-remote && rm -rf ~/.mcp-auth`; then switch to the native URL configuration above, which ends the problem for good.

## API keys (headless or CI)

Where nobody is present to complete the OAuth prompt, the same endpoint also authenticates with a Scenario API key as an `Authorization: Basic <base64 of KEY:SECRET>` header, and a client that takes no headers (Claude Desktop's native configuration) reaches it through `mcp-remote`. Keys are created in the Scenario portal (the `api_key_create` catalog tool returns the link and nothing else). Wiring one into a client is an operator task done by hand: the [connection guide](https://mcp.scenario.com/docs#using-an-api-key) carries the current steps for each client.

Credentials stay out of the conversation. An agent asked to set this up points to the guide and stops there. It does not ask for a key or secret, does not place one in a command, a config file, or a message, and does not repeat one that appears in its context.

## Server-side applications

OAuth from a web or server application fails with `redirect_uri must use a loopback address or custom URI scheme` until the application's origin is on the server's allowlist. Dynamic client re-registration does not help: only the origin is gated. An API key serves the application without OAuth for generation and project work; team-level administration (model access lists, member roles and caps) needs per-user OAuth with a team admin, since the server refuses API keys there. To get an origin allowlisted, contact support with the bare `https` origin, no path.
