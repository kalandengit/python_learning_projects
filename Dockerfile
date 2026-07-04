# syntax=docker/dockerfile:1.7
# EMS API v3 — multi-stage: liboqs 0.12.0 compiled in builder, slim non-root runtime.

FROM python:3.13-slim AS builder

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential cmake ninja-build git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# liboqs (ML-DSA-65 / FIPS 204) — pinned tag, shared lib only.
RUN git clone --depth 1 --branch 0.12.0 https://github.com/open-quantum-safe/liboqs /tmp/liboqs \
    && cmake -S /tmp/liboqs -B /tmp/liboqs/build -GNinja \
        -DBUILD_SHARED_LIBS=ON -DOQS_BUILD_ONLY_LIB=ON -DCMAKE_BUILD_TYPE=Release \
    && cmake --build /tmp/liboqs/build \
    && cmake --install /tmp/liboqs/build --prefix /opt/liboqs

COPY --from=ghcr.io/astral-sh/uv:0.8.17 /uv /usr/local/bin/uv

WORKDIR /build
COPY pyproject.toml uv.lock ./
ENV UV_PYTHON_DOWNLOADS=never UV_PROJECT_ENVIRONMENT=/opt/venv
RUN uv sync --frozen --no-dev --no-install-project --extra pqc

COPY app ./app
COPY migrations ./migrations
COPY alembic.ini ./
RUN uv sync --frozen --no-dev --extra pqc


FROM python:3.13-slim AS runtime

RUN groupadd -g 10001 ems && useradd -u 10001 -g ems -m -s /usr/sbin/nologin ems

COPY --from=builder /opt/liboqs/lib/ /usr/local/lib/
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder --chown=ems:ems /build/app /srv/ems/app
COPY --from=builder --chown=ems:ems /build/migrations /srv/ems/migrations
COPY --from=builder --chown=ems:ems /build/alembic.ini /srv/ems/alembic.ini

ENV PATH=/opt/venv/bin:$PATH \
    LD_LIBRARY_PATH=/usr/local/lib \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /srv/ems
USER ems
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=15s --retries=3 \
    CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).status == 200 else 1)"]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-server-header"]
