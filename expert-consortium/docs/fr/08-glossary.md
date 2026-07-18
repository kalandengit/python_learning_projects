# 8 — Glossaire pour débutants (Français)

Définitions en langage simple de tous les termes techniques du projet.

| Terme | Signification |
|---|---|
| **Terminal** | Une fenêtre où l'on tape des commandes texte au lieu de cliquer. Aussi appelé « ligne de commande » ou « console ». |
| **Commande** | Une ligne de texte tapée dans le terminal, exécutée avec Entrée. |
| **Python** | Le langage de programmation du projet. Pas besoin de l'écrire — seulement de l'exécuter. |
| **Environnement virtuel (venv)** | Un dossier privé contenant les bibliothèques Python du projet, pour éviter les conflits. Activé avec `source .venv/bin/activate`. |
| **Bibliothèque / dépendance** | Du code prêt à l'emploi utilisé par le projet (listé dans `requirements.txt`, installé avec `pip`). |
| **API** | Un moyen pour des programmes de parler à un service sur internet. Notre programme envoie vos questions aux ordinateurs de Mistral via leur API. |
| **Clé API** | Un mot de passe secret identifiant *votre* compte Mistral. Quiconque a votre clé peut dépenser votre argent — gardez-la uniquement dans `.env`. |
| **LLM (grand modèle de langage)** | Le « cerveau » IA (ex. Mistral Large) qui lit du texte et rédige des réponses. |
| **Token** | L'unité de comptage du texte pour les LLM — environ ¾ d'un mot. Les prix API sont par million de tokens. |
| **RAG (génération augmentée par récupération)** | Technique où l'IA *cherche d'abord dans vos documents* les passages pertinents, puis répond *à partir de ces passages*. C'est ainsi que l'assistant connaît vos fichiers. |
| **Fine-tuning** | Ré-entraîner un modèle IA sur vos propres exemples pour qu'il adopte votre style et votre expertise. Réalisé sur les serveurs de Mistral — aucun GPU nécessaire chez vous. |
| **Embedding** | Une liste de nombres représentant le *sens* d'un texte. Deux textes sur la même idée obtiennent des nombres proches — c'est la recherche par le sens. |
| **Base vectorielle (Qdrant)** | Une base de données conçue pour stocker les embeddings et trouver très vite « les textes au sens proche ». |
| **Chunk (morceau)** | Un petit fragment (~quelques paragraphes) : chaque document est découpé avant indexation. L'IA reçoit les morceaux les plus pertinents, pas les fichiers entiers. |
| **Recherche hybride** | Combiner la recherche par le sens (embeddings) et la recherche classique par mots-clés (BM25) — meilleure que chacune seule. |
| **OCR (reconnaissance optique de caractères)** | Transformer des images de texte (PDF scannés, photos) en vrai texte. Mistral OCR gère très bien l'arabe. |
| **Transcription** | Transformer la parole d'un audio/vidéo en texte (fait par le modèle Voxtral de Mistral). |
| **ffmpeg** | Un outil gratuit qui extrait la piste audio des vidéos pour permettre la transcription. |
| **FastAPI / uvicorn** | Les outils Python qui font tourner la page web locale de discussion. |
| **Serveur / VPS** | Un ordinateur dans un datacenter, loué (~5 €/mois), pour que votre assistant soit disponible partout, 24h/24. |
| **Docker** | Un moyen d'empaqueter tout le projet pour qu'il tourne à l'identique sur n'importe quelle machine. |
| **HTTPS / Caddy** | Le chiffrement de la connexion vers votre serveur (le cadenas du navigateur) ; Caddy le configure automatiquement. |
| **git / dépôt (repo)** | Un système qui sauvegarde l'historique du code. GitHub héberge les dépôts en ligne. |
| **Fichier `.env`** | Le fichier contenant vos secrets (clé API, mots de passe). Jamais partagé, jamais commité dans git. |
| **JSONL** | Un fichier texte avec un enregistrement JSON par ligne — le format exigé par Mistral pour les exemples de fine-tuning. |
| **N'Ko (ߒߞߏ)** | L'écriture inventée par Solomana Kanté en 1949 pour les langues mandingues. Parfaitement stockable en Unicode, mais aucun modèle IA actuel ne l'*écrit* couramment — voir la Phase 3 du PRD. |
