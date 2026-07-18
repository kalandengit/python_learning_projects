# Expert Consortium — Your Personal Multi-Expert AI

**English** | [Français plus bas ⬇](#français)

A personalized AI assistant built on the **Mistral API** (no GPU needed) that acts as a
**Multi-Expert Consortium**: four senior experts with 25 years of experience in
**Law & Courts**, **N'Ko writing**, **Islamic sciences (Arabic documents)**, and
**Computer Science** — answering from *your own* documents, audio, and video.

## What it does

1. **You drop files** (PDF, Word, images, audio, video) into an `uploads/` folder — or upload
   them from the web page or Telegram.
2. The system **reads everything**: Mistral OCR for PDFs/images (excellent Arabic support),
   Voxtral for audio/video transcription.
3. Everything is stored in a **searchable knowledge database** (Qdrant).
4. You **chat** with the consortium — in your browser or on Telegram. Answers cite your
   documents.
5. Your best conversations become **fine-tuning data** to create your own custom Mistral model.

## Quick start

```bash
cd expert-consortium
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then put your MISTRAL_API_KEY inside
python -m app.cli ingest    # index everything in uploads/
uvicorn app.main:app        # open http://localhost:8000
```

Full beginner walkthrough: **[docs/en/01-setup.md](docs/en/01-setup.md)**

## Documentation

| # | English | Français |
|---|---------|----------|
| 1 | [Setup from zero](docs/en/01-setup.md) | [Installation depuis zéro](docs/fr/01-setup.md) |
| 2 | [Uploading documents](docs/en/02-upload.md) | [Ajouter des documents](docs/fr/02-upload.md) |
| 3 | [Chatting with the consortium](docs/en/03-chat.md) | [Discuter avec le consortium](docs/fr/03-chat.md) |
| 4 | [Telegram bot](docs/en/04-telegram.md) | [Bot Telegram](docs/fr/04-telegram.md) |
| 5 | [Fine-tuning your own model](docs/en/05-finetuning.md) | [Fine-tuning de votre modèle](docs/fr/05-finetuning.md) |
| 6 | [Deploying to a cloud server](docs/en/06-deploy-vps.md) | [Déployer sur un serveur](docs/fr/06-deploy-vps.md) |
| 7 | [Costs](docs/en/07-costs.md) | [Coûts](docs/fr/07-costs.md) |
| 8 | [Glossary for beginners](docs/en/08-glossary.md) | [Glossaire pour débutants](docs/fr/08-glossary.md) |
| 9 | [Moving to your own repo](docs/en/09-new-repo.md) | [Créer votre propre dépôt](docs/fr/09-new-repo.md) |

Product vision and requirements: **[PRD.md](PRD.md)** ·
Autonomous-agent playbook: **[AGENT.md](AGENT.md)**

---

# Français

Un assistant IA personnalisé construit sur l'**API Mistral** (aucun GPU nécessaire) qui agit
comme un **Consortium Multi-Experts** : quatre experts seniors avec 25 ans d'expérience en
**Droit & Tribunaux**, **Écriture N'Ko**, **Sciences islamiques (documents arabes)** et
**Informatique** — répondant à partir de *vos propres* documents, audios et vidéos.

## Ce que ça fait

1. **Vous déposez des fichiers** (PDF, Word, images, audio, vidéo) dans le dossier `uploads/` —
   ou vous les envoyez depuis la page web ou Telegram.
2. Le système **lit tout** : Mistral OCR pour les PDF/images (excellent support de l'arabe),
   Voxtral pour la transcription audio/vidéo.
3. Tout est stocké dans une **base de connaissances interrogeable** (Qdrant).
4. Vous **discutez** avec le consortium — dans votre navigateur ou sur Telegram. Les réponses
   citent vos documents.
5. Vos meilleures conversations deviennent des **données de fine-tuning** pour créer votre
   propre modèle Mistral personnalisé.

## Démarrage rapide

```bash
cd expert-consortium
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # puis mettez votre MISTRAL_API_KEY dedans
python -m app.cli ingest    # indexe tout le contenu de uploads/
uvicorn app.main:app        # ouvrez http://localhost:8000
```

Guide complet pour débutants : **[docs/fr/01-setup.md](docs/fr/01-setup.md)**

## Note importante sur le N'Ko

Aucun grand modèle de langage ne génère aujourd'hui du N'Ko fluide. Le système peut **stocker,
rechercher et retrouver** vos documents N'Ko (texte Unicode ߒߞߏ), mais la *génération* de texte
N'Ko reste un objectif de recherche — voir la Phase 3 du [PRD](PRD.md).
