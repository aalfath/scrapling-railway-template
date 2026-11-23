# Scrapling MCP server for Railway: the official image, pinned by version and digest.
FROM ghcr.io/d4vinci/scrapling:0.5.1@sha256:b4e92cde7e7e2d9f5940e90ee796cbf7340843a6de7213c0c409fe3d2aadfd87

# tini as PID 1 reaps orphaned Chromium processes and passes the server's exit code on,
# so a crash exits non-zero and Railway's ON_FAILURE policy restarts the service.
RUN apt-get update \
 && apt-get install -y --no-install-recommends tini \
 && rm -rf /var/lib/apt/lists/*

COPY railway_serve.py /opt/railway/railway_serve.py

# /data is the Railway volume: the server's working directory, where browser_save_state
# writes saved logins (cookies, local storage) so they survive redeploys.
ENV HOME=/root \
    SCRAPLING_DATA_DIR=/data \
    PORT=8000
WORKDIR /data
EXPOSE 8000

ENTRYPOINT ["/usr/bin/tini", "-g", "--", "/app/.venv/bin/python", "/opt/railway/railway_serve.py"]
