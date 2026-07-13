# Python Learning Projects

A collection of practical Python applications and reusable AI-assistant skills.

## Projects

### N'Ko Voice Transcriptor

A FastAPI web application for recording or uploading Manding-language audio,
transcribing it, and displaying an editable N'Ko transliteration. It includes a
localized browser interface, authenticated history, a mock ASR engine for local
development, optional Meta MMS support, tests, and Docker deployment files.

See [`nko-voice-transcriptor/README.md`](nko-voice-transcriptor/README.md).

## Skills

- `planning-first`: structured planning before implementation.
- `it-prompt-specialist`: a multidisciplinary IT analysis and prompt workflow.

The canonical skill sources are under `skills/`; packaged Claude Code plugins
are under `claude-skills/plugins/`.

## Development

Each project documents its own setup. For the N'Ko application:

```bash
cd nko-voice-transcriptor
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pytest
ruff check app tests
```

## License

See [`LICENSE`](LICENSE).
