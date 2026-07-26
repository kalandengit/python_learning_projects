# N'KO Voice Transcriptor — multi-stage, non-root image
FROM python:3.11-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.11-slim
RUN groupadd -r nko && useradd -r -g nko -d /app nko
WORKDIR /app
COPY --from=builder /install /usr/local
COPY app/ app/
COPY pyproject.toml .
USER nko
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s \
  CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8000/api/health')"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
