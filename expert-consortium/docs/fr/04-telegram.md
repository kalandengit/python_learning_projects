# 4 — Bot Telegram (Français)

Parlez à votre consortium depuis votre téléphone. Installation en ~5 minutes, gratuite.

## Étape 1 — Créer votre bot avec BotFather

1. Dans Telegram, cherchez **@BotFather** (coche bleue vérifiée) et ouvrez-le.
2. Envoyez `/newbot`.
3. Donnez-lui un nom d'affichage, ex. `Mon Consortium`.
4. Donnez-lui un identifiant se terminant par `bot`, ex. `kalan_consortium_bot`.
5. BotFather répond avec un **token** du type `1234567890:AAF...xyz`. Copiez-le.

## Étape 2 — Trouver votre ID Telegram personnel

1. Cherchez **@userinfobot** et ouvrez-le.
2. Envoyez `/start` — il répond avec votre **Id** numérique (ex. `987654321`). Copiez-le.

Cet ID verrouille le bot sur vous : toute autre personne qui trouve votre bot est refusée.
Sans lui, le bot refuse tout le monde.

## Étape 3 — Configurer et démarrer

Ajoutez les deux valeurs dans votre fichier `.env` :

```
TELEGRAM_BOT_TOKEN=1234567890:AAF...xyz
TELEGRAM_ALLOWED_USER_ID=987654321
```

Puis démarrez le bot (dans son propre terminal, en parallèle de l'appli web ou seul) :

```bash
source .venv/bin/activate
python -m app.bots.telegram_bot
```

## Étape 4 — Utilisation

Ouvrez votre bot dans Telegram (cherchez son identifiant), appuyez sur **Démarrer**, puis :

- **Posez vos questions** en tapant — même consortium, même base de connaissances, sources
  affichées avec 📎.
- **Envoyez un fichier** (PDF, Word, image, audio, vidéo, ou même un message vocal) — il est
  ajouté automatiquement à la base de connaissances.
- `/docs` — liste ce que l'assistant connaît.
- `/reset` — nouvelle conversation (oublie le contexte du fil en cours).

## Remarques

- Le bot doit *tourner* sur votre ordinateur (ou votre serveur, voir
  [6 — Déploiement](06-deploy-vps.md)) pour répondre.
- Les fichiers envoyés depuis Telegram reçoivent le domaine `general` ; utilisez les
  sous-dossiers de uploads/ ou la page web pour des étiquettes de domaine précises.
- Si le bot répond « Bot privé » avec un nombre : ce nombre est votre vrai ID — mettez-le
  dans `TELEGRAM_ALLOWED_USER_ID` et redémarrez le bot.

**Suite :** [5 — Fine-tuning](05-finetuning.md)
