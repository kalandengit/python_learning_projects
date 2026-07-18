# 1 — Setup from zero (English)

*Goal: from a computer with nothing installed to your first conversation with your assistant.
Time: 30–45 minutes. No prior computer-science knowledge required — copy-paste each command.*

> Words in **bold italics** like ***terminal*** are explained in the
> [Glossary](08-glossary.md).

## Step 1 — Open a terminal

- **Windows:** press `Windows` key, type `PowerShell`, press Enter.
- **macOS:** press `Cmd+Space`, type `Terminal`, press Enter.
- **Linux:** press `Ctrl+Alt+T`.

A black/white window opens. You type commands into it and press Enter to run them.

## Step 2 — Install Python 3.11+

Check if you already have it:

```bash
python3 --version
```

If you see `Python 3.11` or higher, skip ahead. Otherwise install it from
<https://www.python.org/downloads/> (Windows: tick **"Add Python to PATH"** during install,
then close and reopen PowerShell).

## Step 3 — Install ffmpeg (needed for video files)

- **Windows (PowerShell):** `winget install ffmpeg`
- **macOS:** `brew install ffmpeg` (install Homebrew first from <https://brew.sh> if needed)
- **Linux (Debian/Ubuntu):** `sudo apt install ffmpeg`

Check: `ffmpeg -version` should print several lines.

## Step 4 — Get the project

If you received the project as a git repository:

```bash
git clone https://github.com/kalandengit/python_learning_projects.git
cd python_learning_projects/expert-consortium
```

## Step 5 — Create a virtual environment and install

A ***virtual environment*** is a private box for this project's Python libraries.

```bash
python3 -m venv .venv
source .venv/bin/activate      # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

The install takes a few minutes. You must re-run the `activate` line every time you open a
new terminal for this project (your prompt shows `(.venv)` when active).

## Step 6 — Get your Mistral API key (free)

1. Go to <https://console.mistral.ai> and create an account.
2. In the left menu, choose the free **Experiment** plan when asked (no credit card needed
   for development).
3. Open **API Keys** → **Create new key** → copy the key (it looks like a long random string).
   ⚠️ It is shown only once — copy it now.

## Step 7 — Configure the project

```bash
cp .env.example .env           # Windows PowerShell: copy .env.example .env
```

Open the new `.env` file with any text editor (Notepad is fine) and:

1. Paste your key after `MISTRAL_API_KEY=` (no spaces, no quotes).
2. Replace `change-me-please` after `WEB_PASSWORD=` with a password of your choice.

Save and close. **This file must never be shared or committed to git** — it contains your
secret key (the project's `.gitignore` already protects it).

## Step 8 — First run

Put one test file (any PDF or Word document) into the `uploads/` folder, then:

```bash
python -m app.cli ingest       # reads and indexes everything in uploads/
uvicorn app.main:app           # starts the web assistant
```

Open <http://localhost:8000> in your browser, enter your `WEB_PASSWORD`, and ask a question
about your test document. You should get an answer with the file cited underneath.

To stop the assistant: press `Ctrl+C` in the terminal.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `python3: command not found` | Use `python` instead of `python3`, or reinstall Python with "Add to PATH" |
| `MISTRAL_API_KEY is not set` | Step 7 was skipped or the `.env` file is in the wrong folder — it must sit next to `README.md` |
| `401 Unauthorized` from Mistral | The key was pasted with extra spaces/quotes, or is deactivated — create a new one |
| Page asks for password forever | Check `WEB_PASSWORD` in `.env`, restart `uvicorn` after editing `.env` |

**Next:** [2 — Uploading documents](02-upload.md)
