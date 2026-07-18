# 2 — Ajouter des documents (Français)

Votre assistant ne connaît que ce que vous lui donnez. Il y a trois façons de le nourrir.

## Types de fichiers pris en charge

| Genre | Extensions | Lecture |
|---|---|---|
| Documents | `.pdf`, `.docx`, `.txt`, `.md` | Mistral OCR pour les PDF ; lecture directe sinon |
| Images (scans, photos de pages) | `.png`, `.jpg`, `.jpeg`, `.webp`, `.avif` | Mistral OCR (très bon en arabe) |
| Audio | `.mp3`, `.wav`, `.m4a`, `.ogg`, `.flac`, `.opus` | Transcription Voxtral |
| Vidéo | `.mp4`, `.mkv`, `.webm`, `.mov`, `.avi` | ffmpeg extrait l'audio → Voxtral |

## Méthode 1 — Le dossier uploads (idéal pour beaucoup de fichiers)

Copiez vos fichiers dans `uploads/`, puis lancez :

```bash
python -m app.cli ingest
```

**Astuce — organisez par domaine.** Créez des sous-dossiers nommés `law`, `nko`, `islamic`,
`cs` et le système étiquette chaque fichier automatiquement :

```
uploads/
├── law/        jugement-2024.pdf, code-penal.docx
├── nko/        alphabet-nko.pdf
├── islamic/    tafsir-page-14.jpg, cours-fiqh.mp3
└── cs/         cours-python.mp4
```

Les fichiers placés directement dans `uploads/` reçoivent le domaine `general`.

## Méthode 2 — Surveillance automatique

Laissez tourner ceci dans un terminal et chaque fichier déposé dans `uploads/` est indexé en
quelques secondes :

```bash
python -m app.cli watch
```

## Méthode 3 — Page web / Telegram

Utilisez le bouton 📎 de la page de chat (voir [3 — Chat](03-chat.md)) ou envoyez un document
à votre bot Telegram (voir [4 — Telegram](04-telegram.md)).

## Gérer la base de connaissances

```bash
python -m app.cli list              # que sait mon assistant ?
python -m app.cli delete FICHIER.pdf # oublier un document
```

Re-téléverser un fichier du même nom **remplace** son ancien contenu — pas de doublons.

## Bon à savoir

- Un PDF arabe de 100 pages prend ~1–2 minutes à OCRiser et indexer.
- Un cours audio d'une heure prend quelques minutes à transcrire et coûte environ 0,18 $.
- Si un fichier échoue, les autres continuent ; l'erreur s'affiche et se retrouve dans `logs/app.log`.
- Les fichiers originaux restent intacts dans `uploads/` ; seul le texte extrait va dans la base.

**Suite :** [3 — Discuter avec le consortium](03-chat.md)
