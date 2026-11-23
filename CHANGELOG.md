# Changelog

## 0.5.1 (2026-11-23)

First release of the Railway template.

* Scrapling 0.5.1, official image `ghcr.io/d4vinci/scrapling:0.5.1@sha256:b4e92cde7e7e2d9f5940e90ee796cbf7340843a6de7213c0c409fe3d2aadfd87`.
* MCP server in streamable-HTTP mode at `/mcp`, bearer token required (generated at deploy), `/healthz` for Railway's health check.
* Volume at `/data` (working directory for saved browser state).
* `tini` as PID 1; unexpected stops exit non-zero so Railway restarts the service.
* Low-memory Chromium flags (one renderer process, no site isolation) when the memory limit is 1.5 GB or less, so one browser page fits the 0.5 GB Free plan. `SCRAPLING_LOW_MEMORY=0` turns them off.
