# Multi-stage build: builder installs pinned deps, runtime stays slim & non-root.
# Pin the base image to a digest in production, e.g.:
#   FROM python:3.11-slim@sha256:<digest> AS builder
FROM python:3.11-slim AS builder

WORKDIR /build
COPY requirements-lock.txt requirements.txt ./
# Prefer the lock file (reproducibility, audit finding); fall back to ranges.
RUN pip install --no-cache-dir --prefix=/install \
      -r requirements-lock.txt || \
    pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.11-slim

RUN groupadd -g 1000 nko && useradd -m -u 1000 -g nko nko
WORKDIR /srv
COPY --from=builder /install /usr/local
COPY --chown=nko:nko app ./app
COPY --chown=nko:nko alembic ./alembic
COPY --chown=nko:nko alembic.ini ./

USER nko
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=4).status==200 else 1)"]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
