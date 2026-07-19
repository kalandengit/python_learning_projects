# 8 — Glossary for beginners (English)

Plain-language definitions of every technical term used in this project.

| Term | Meaning |
|---|---|
| **Terminal** | A window where you type text commands instead of clicking. Also called "command line" or "console". |
| **Command** | A line of text you type in the terminal and run by pressing Enter. |
| **Python** | The programming language this project is written in. You don't need to write it — just run it. |
| **Virtual environment (venv)** | A private folder holding this project's Python libraries so they don't conflict with other programs. Activated with the `source .venv/bin/activate` command. |
| **Library / dependency** | Ready-made code the project uses (listed in `requirements.txt`, installed with `pip`). |
| **API** | A way for programs to talk to a service over the internet. Our program sends your questions to Mistral's computers via their API and gets answers back. |
| **API key** | A secret password identifying *your* Mistral account. Anyone with your key can spend your money — keep it in `.env` only. |
| **LLM (Large Language Model)** | The AI "brain" (e.g., Mistral Large) that reads text and writes answers. |
| **Token** | The unit LLMs count text in — roughly ¾ of a word. API prices are per million tokens. |
| **RAG (Retrieval-Augmented Generation)** | Technique where the AI first *searches your documents* for relevant passages, then answers *using those passages*. That is how the assistant knows your files. |
| **Fine-tuning** | Retraining an AI model on your own examples so it adopts your style and expertise. Done on Mistral's servers — no GPU needed on your side. |
| **Embedding** | A list of numbers representing the *meaning* of a text. Two texts about the same idea get similar numbers — that's how search-by-meaning works. |
| **Vector database (Qdrant)** | A database designed to store embeddings and find "texts with similar meaning" very fast. |
| **Chunk** | A small piece (~a few paragraphs) that each document is cut into before indexing. The AI receives the most relevant chunks, not whole files. |
| **Hybrid search** | Combining meaning-based search (embeddings) with classic keyword search (BM25) — better than either alone. |
| **OCR (Optical Character Recognition)** | Turning images of text (scanned PDFs, photos) into real text. Mistral OCR handles Arabic very well. |
| **Transcription** | Turning speech in audio/video into text (done by Mistral's Voxtral model). |
| **ffmpeg** | A free tool that extracts the audio track from video files so it can be transcribed. |
| **FastAPI / uvicorn** | The Python tools that run the local web page you chat on. |
| **Server / VPS** | A computer in a datacenter that you rent (~€5/month) so your assistant is available from anywhere, 24/7. |
| **Docker** | A way to package the whole project so it runs identically on any computer or server. |
| **HTTPS / Caddy** | Encryption of the connection to your server (the padlock in the browser); Caddy is the tool that sets it up automatically. |
| **git / repository (repo)** | A system that saves the history of the project's code. GitHub hosts repositories online. |
| **`.env` file** | The file holding your secrets (API key, passwords). Never shared, never committed to git. |
| **JSONL** | A text file with one JSON record per line — the format Mistral requires for fine-tuning examples. |
| **N'Ko (ߒߞߏ)** | The script invented by Solomana Kanté in 1949 for Manding languages. Stored fine as Unicode text, but no current AI model *writes* it fluently — see PRD Phase 3. |
