# 10 — Limites & comportement à l'échelle (Français)

Ce qui se passe quand vous poussez le système fort, et les réglages disponibles (tous dans
`.env`).

## Protections automatiques (rien à configurer)

| Situation | Ce que fait le système |
|---|---|
| Audio/vidéo de plus de ~100 min | Découpé automatiquement en segments, transcrits un à un, fusionnés — un cours de 5 h passe sans problème |
| Très gros document à indexer | Les requêtes d'embedding sont regroupées par taille pour ne jamais dépasser la limite de l'API |
| PDF/image de plus de 45 MB | Refusé avec un message clair et le conseil de découper le PDF d'abord |
| Téléversement web de plus de 500 MB | Refusé (413) ; les fichiers sont écrits en flux sur le disque, jamais chargés en RAM |
| Plus de 30 questions/minute | Refusé (429) — protège votre budget Mistral si le mot de passe fuit |
| 10 mots de passe erronés en 5 min | Connexion bloquée 5 minutes (protection force brute) |
| Fichier encore en cours de copie dans uploads/ | Le surveillant attend que la taille se stabilise avant d'ingérer |
| Fichier Telegram de plus de 20 MB | Refusé poliment (limite dure des bots Telegram) avec redirection vers le web/dossier |
| Un fichier échoue pendant un lot | Les autres continuent ; l'erreur est affichée et journalisée |
| Croissance des journaux | `logs/app.log` tourne à 5 MB, en gardant 3 anciens fichiers |

## La vraie contrainte : deux processus, une base locale

Le stockage embarqué (`QDRANT_URL` vide) n'autorise **qu'un processus à la fois**. Faire
tourner l'appli web ET le bot Telegram ensemble demande un serveur Qdrant :

- **Avec Docker (recommandé, c'est ce que fait le VPS) :** `docker compose up -d` — Qdrant
  tourne comme service et l'appli + le bot s'y connectent. Rien à configurer.
- **Sans Docker :** un seul processus à la fois, ou installez un serveur Qdrant local et
  mettez `QDRANT_URL=http://localhost:6333`.

Si cela vous arrive, le message d'erreur explique exactement cela.

## Réglages (`.env`)

```
MAX_UPLOAD_MB=500            # plafond de téléversement web
MAX_OCR_MB=45                # garde-fou de taille OCR
AUDIO_SEGMENT_MINUTES=100    # seuil de découpage des enregistrements longs
CHAT_RATE_PER_MIN=30         # questions par minute
EMBED_BATCH_CHAR_BUDGET=40000
```

## Capacité réaliste (usage personnel, VPS à 5 €)

- **Base de connaissances :** des dizaines de milliers d'extraits (≈ des milliers de
  documents) passent bien avec Qdrant sur 4 Go de RAM ; la recherche reste rapide.
- **Débit d'ingestion :** limité par les quotas Mistral (gratuit/payant), pas par la
  machine — les grosses archives prennent simplement du temps (les nouvelles tentatives
  automatiques gèrent les limites de débit).
- **Utilisateurs :** système mono-utilisateur par conception (un mot de passe partagé, un
  ID Telegram). Le multi-utilisateurs est hors périmètre v1 (voir PRD §3).
