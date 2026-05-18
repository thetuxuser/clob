# ── Build stage ───────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

RUN pip install --no-cache-dir hatchling

COPY pyproject.toml README.md .
COPY clob/ clob/

RUN pip install --no-cache-dir ".[dev]" --prefix=/install

# ── Runtime stage ──────────────────────────────────────────────
FROM python:3.12-slim

LABEL org.opencontainers.image.title="clob"
LABEL org.opencontainers.image.description="Universal AI in your terminal"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.source="https://github.com/crishacks/clob"

WORKDIR /app

COPY --from=builder /install /usr/local
COPY --from=builder /app /app

# Config dir
RUN mkdir -p /root/.config/clob

ENV PYTHONUNBUFFERED=1
ENV TERM=xterm-256color

ENTRYPOINT ["clob"]
CMD []
