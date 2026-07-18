# 2 — Uploading documents (English)

Your assistant only knows what you feed it. There are three ways to feed it.

## Supported file types

| Kind | Extensions | How it's read |
|---|---|---|
| Documents | `.pdf`, `.docx`, `.txt`, `.md` | Mistral OCR for PDFs; direct reading otherwise |
| Images (scans, photos of pages) | `.png`, `.jpg`, `.jpeg`, `.webp`, `.avif` | Mistral OCR (very good with Arabic) |
| Audio | `.mp3`, `.wav`, `.m4a`, `.ogg`, `.flac`, `.opus` | Voxtral transcription |
| Video | `.mp4`, `.mkv`, `.webm`, `.mov`, `.avi` | ffmpeg extracts the audio → Voxtral |

## Way 1 — The uploads folder (best for many files)

Copy files into `uploads/`, then run:

```bash
python -m app.cli ingest
```

**Tip — organize by domain.** Create subfolders named `law`, `nko`, `islamic`, `cs` and the
system tags each file automatically:

```
uploads/
├── law/        jugement-2024.pdf, code-penal.docx
├── nko/        alphabet-nko.pdf
├── islamic/    tafsir-page-14.jpg, cours-fiqh.mp3
└── cs/         python-course.mp4
```

Files placed directly in `uploads/` get the domain `general`.

## Way 2 — Automatic watching

Leave this running in a terminal and every file you drop into `uploads/` is indexed within
seconds:

```bash
python -m app.cli watch
```

## Way 3 — Web page / Telegram

Use the 📎 upload button on the chat page (see [3 — Chat](03-chat.md)) or send a document to
your Telegram bot (see [4 — Telegram](04-telegram.md)).

## Managing the knowledge base

```bash
python -m app.cli list              # what does my assistant know?
python -m app.cli delete FILE.pdf   # forget one document
```

Re-uploading a file with the same name **replaces** its old content — no duplicates.

## Good to know

- A 100-page Arabic PDF takes ~1–2 minutes to OCR and index.
- A 1-hour audio lecture takes a few minutes to transcribe and costs about $0.18.
- If a file fails, the others continue; the error is shown and logged in `logs/app.log`.
- Original files stay in `uploads/` untouched; only extracted text goes into the database.

**Next:** [3 — Chatting with the consortium](03-chat.md)
