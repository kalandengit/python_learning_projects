FROM python:3.12-slim

# ffmpeg is needed to extract audio from video files
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /srv/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY finetune_data/manual/example.jsonl ./finetune_data/manual/example.jsonl

RUN useradd --create-home appuser \
    && mkdir -p uploads data logs finetune_data/manual \
    && chown -R appuser:appuser /srv/app
USER appuser

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
