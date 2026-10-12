# GlintbaseResearch bot

If you saw requests with this user agent, they came from Glintbase's research harness:

```
GlintbaseResearch/1.0 (+https://glintbase.dev/research/bot; research@glintbase.dev)
```

## What it does

We run small, published measurement studies of how the public web and public AI-agent infrastructure behave for software agents. Each study's design is pre-registered in this repository before data collection.

| Study | What we request | Volume |
|---|---|---|
| [Remote MCP Server Reliability](benchmarks/production-mcp-reliability-crisis/PREREGISTRATION.md) | Protocol metadata from MCP endpoints listed in the official MCP Registry: `server/discover` or `initialize`, `tools/list`, one call to a tool that does not exist (to check error handling), and OAuth protected-resource metadata if the endpoint requires auth | ≤ 8 requests per endpoint per round, one endpoint per host at a time, two rounds |

## What it never does

- Call your real tools, or send data intended to change state.
- Send security payloads, attempt authentication, or try to bypass challenges, CAPTCHAs or rate limits.
- Pretend to be another company's crawler or a human browser.

## Opting out

Email **research@glintbase.dev** with the host name(s). We add them to the study's `optout.txt` and stop within 24 hours. You can also block the `GlintbaseResearch` user agent.

## Data we publish

Aggregate statistics plus per-endpoint derived fields, such as "handshake succeeded" or "tool count". We never publish raw responses, and we don't publish lists naming the worst servers.
