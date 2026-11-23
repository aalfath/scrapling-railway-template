# Deploy and Host Scrapling on Railway

Scrapling is an open-source (BSD-3-Clause) adaptive web-scraping library for Python. Its built-in MCP server gives AI agents such as Claude Code, Cursor or your own agent tools to fetch pages over fast HTTP with browser fingerprints or through a stealthy headless Chromium, and returns clean Markdown, text or HTML trimmed by CSS selector.

## About Hosting Scrapling

This template runs the official Scrapling 0.5.1 image (pinned by digest) as a remote MCP server on the streamable-HTTP transport at `/mcp`. Chromium is inside the image, so browser tools need no extra service. A server that fetches any URL must not be open, so a 64-character bearer token is generated at deploy and the server refuses to start without it. `/healthz` answers Railway's health check without a token. A volume at `/data` is the server's working directory, so login state saved with `browser_save_state` survives redeploys. The service builds from a public GitHub repo, so Railway offers you each version bump as an update.

## Common Use Cases

* Give a coding agent a hosted web-fetch tool that returns Markdown instead of raw HTML
* Scrape JavaScript-heavy or bot-protected pages through a stealthy headless Chromium
* Keep logged-in browser sessions for agents: save cookies and storage to the volume and load them later
* Share one scraping endpoint with a team instead of installing browsers on every laptop

## Dependencies for Scrapling Hosting

* One service built from `aalfath/scrapling-railway-template` (official `ghcr.io/d4vinci/scrapling` image plus a small start script)
* A Railway volume mounted at `/data`
* An MCP client that can send an `Authorization` header (Claude Code, Cursor, VS Code, most agent frameworks)

### Deployment Dependencies

* [Scrapling MCP server documentation](https://scrapling.readthedocs.io/en/latest/ai/mcp-server.html)
* [Scrapling on GitHub](https://github.com/D4Vinci/Scrapling) and its [v0.5.1 release](https://github.com/D4Vinci/Scrapling/releases/tag/v0.5.1)
* [Template repo](https://github.com/aalfath/scrapling-railway-template)
* [Model Context Protocol](https://modelcontextprotocol.io)

### Implementation Details

No prompts: everything is generated or fixed.

| Variable | Value | What it does |
|---|---|---|
| `SCRAPLING_MCP_AUTH_TOKEN` | `${{secret(64,"abcdef0123456789")}}` | Bearer token every MCP request must send |
| `PORT` | `8000` | Port the server listens on (the domain targets it) |
| `MCP_ENDPOINT_URL` | `https://${{RAILWAY_PUBLIC_DOMAIN}}/mcp` | The URL to paste into your client (read-only convenience) |

**After deploy:** open the service's Variables tab, copy `MCP_ENDPOINT_URL` and `SCRAPLING_MCP_AUTH_TOKEN`, and add the server to your client. Claude Code:

```sh
claude mcp add --transport http scrapling https://YOUR-DOMAIN/mcp --header "Authorization: Bearer YOUR-TOKEN"
```

Cursor, VS Code and other clients that take JSON:

```json
{ "mcpServers": { "scrapling": { "url": "https://YOUR-DOMAIN/mcp", "headers": { "Authorization": "Bearer YOUR-TOKEN" } } } }
```

Then ask your agent to fetch a page with `make_request`, or with `browser_fetch_once` for pages that need JavaScript. Saved browser state files are written relative to `/data`.

**Memory:** the server idles at about 80 MB. On Railway's 0.5 GB Free-plan limit the HTTP tools and light browser pages (Wikipedia) work, but a heavy page such as a GitHub repo crashes the Chromium tab: the tool returns a "Page crashed" error and the server stays up. For browser tools on modern sites give the service 1 GB (our 1 GB test peaked at about 590 MB with every tool passing). A crash exits non-zero, so Railway restarts the service.

**Security:** anyone with the token can make this service fetch any URL, including private addresses of other services in the same Railway project, so deploy it in its own project and treat the token like a password. To rotate it, change `SCRAPLING_MCP_AUTH_TOKEN` and redeploy. Respect each site's terms of service and robots.txt.

**Updates:** when we bump the pinned Scrapling version in the template repo, Railway shows you an update notice; read `CHANGELOG.md` there before you apply it.

## Why Deploy Scrapling on Railway?

<!-- Recommended: Keep this section as shown below -->
Railway is a singular platform to deploy your infrastructure stack. Railway will host your infrastructure so you don't have to deal with configuration, while allowing you to vertically and horizontally scale it.

By deploying Scrapling on Railway, you are one step closer to supporting a complete full-stack application with minimal burden. Host your servers, databases, AI agents, and more on Railway.
<!-- End recommended section -->
