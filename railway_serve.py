"""Start Scrapling's MCP server in streamable-HTTP mode for Railway.

Adds two routes that need no token: /healthz (Railway health check) and / (a short note).
Everything else, including /mcp, needs `Authorization: Bearer $SCRAPLING_MCP_AUTH_TOKEN`.
"""
import os
import sys

from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse

from scrapling import __version__
from scrapling.core.ai import ScraplingMCPServer

TOKEN_ENV = "SCRAPLING_MCP_AUTH_TOKEN"


def _memory_limit_bytes():
    try:
        raw = open("/sys/fs/cgroup/memory.max").read().strip()
        return None if raw == "max" else int(raw)
    except (OSError, ValueError):
        return None


def _apply_low_memory_browser_flags():
    """On small plans, keep Chromium to fewer processes so one page fits in 0.5 GB.

    SCRAPLING_LOW_MEMORY=1 forces it, 0 turns it off; by default it is on when the
    container's memory limit is 1.5 GB or less. Site isolation starts a renderer
    process per site (iframes included), which pushed GitHub pages past 0.5 GB.
    """
    mode = os.environ.get("SCRAPLING_LOW_MEMORY", "auto").strip().lower()
    limit = _memory_limit_bytes()
    if mode in ("0", "false", "no", "off"):
        return False
    if mode not in ("1", "true", "yes", "on") and (limit is None or limit > 1536 * 1024 * 1024):
        return False
    from scrapling.engines._browsers import _base

    extra_disabled = "site-per-process,IsolateOrigins,BackForwardCache,MediaRouter,OptimizationHints"
    args = []
    for flag in _base.STEALTH_ARGS:
        # Chromium keeps only the last --disable-features switch, so merge into the existing one.
        if flag.startswith("--disable-features="):
            flag = f"{flag},{extra_disabled}"
        args.append(flag)
    if not any(a.startswith("--disable-features=") for a in args):
        args.append(f"--disable-features={extra_disabled}")
    args += [
        "--disable-site-isolation-trials",
        "--renderer-process-limit=1",
        "--js-flags=--max-old-space-size=192",
    ]
    _base.STEALTH_ARGS = tuple(args)
    return True


class RailwayScraplingServer(ScraplingMCPServer):
    def _build_server(self, host, port):
        server = super()._build_server(host, port)
        public = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "").strip()
        if public and server.settings.auth is not None:
            # Advertise the public HTTPS URL in the OAuth protected-resource metadata
            # instead of http://0.0.0.0:PORT.
            try:
                from mcp.server.auth.settings import AuthSettings
                from pydantic import AnyHttpUrl

                url = AnyHttpUrl(f"https://{public}")
                server.settings.auth = AuthSettings(issuer_url=url, resource_server_url=url)
            except Exception as exc:  # keep serving with the upstream default
                print(f"railway: could not set public auth URL: {exc}", file=sys.stderr)

        @server.custom_route("/healthz", methods=["GET"], include_in_schema=False)
        async def healthz(request: Request):
            return JSONResponse({"status": "ok", "version": __version__})

        @server.custom_route("/", methods=["GET"], include_in_schema=False)
        async def index(request: Request):
            return PlainTextResponse(
                f"Scrapling {__version__} MCP server.\n"
                "MCP endpoint: /mcp (streamable HTTP).\n"
                "Send the header 'Authorization: Bearer <SCRAPLING_MCP_AUTH_TOKEN>'.\n"
            )

        return server


def main() -> int:
    token = os.environ.get(TOKEN_ENV, "").strip()
    if len(token) < 16:
        print(f"railway: {TOKEN_ENV} must be set to a long random value; refusing to start.", file=sys.stderr)
        return 1
    port = int(os.environ.get("PORT") or 8000)
    host = os.environ.get("SCRAPLING_HOST", "0.0.0.0")
    allowed = [h.strip() for h in os.environ.get("SCRAPLING_ALLOWED_HOSTS", "").split(",") if h.strip()]

    data_dir = os.environ.get("SCRAPLING_DATA_DIR", "/data")
    os.makedirs(data_dir, exist_ok=True)
    os.chdir(data_dir)

    public = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "").strip()
    where = f"https://{public}/mcp" if public else f"http://{host}:{port}/mcp"
    print(f"railway: Scrapling {__version__} MCP server on {host}:{port}, endpoint {where}, data dir {data_dir}", flush=True)

    if _apply_low_memory_browser_flags():
        print("railway: low-memory Chromium flags on (one renderer process, no site isolation, 192 MB JS heap)", flush=True)

    server = RailwayScraplingServer(auth_token=token)
    server.serve(True, host, port, allowed_hosts=allowed, allow_unauthenticated=False)
    # uvicorn returned without a signal from Railway: treat it as a failure so the service restarts.
    print("railway: MCP server stopped unexpectedly", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
