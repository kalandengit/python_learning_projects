FROM python:3.12-slim AS base

# Run as a non-root user (least privilege).
RUN groupadd -r asa && useradd -r -g asa asa

WORKDIR /srv/app

COPY pyproject.toml ./
COPY app ./app
RUN pip install --no-cache-dir .

USER asa
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s CMD ["python", "-c", \
    "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz')"]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
