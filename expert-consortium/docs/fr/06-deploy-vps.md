# 6 — Déployer sur un serveur cloud (Français)

Objectif : votre assistant disponible 24h/24 depuis partout — page web **et** Telegram — sur
un petit serveur loué (VPS) à 5–9 €/mois. Durée : ~45 minutes.

## Étape 1 — Louer un VPS

Recommandé : **Hetzner** (hetzner.com/cloud, CX22 : 2 vCPU / 4 Go / ~5 €) ou
**DigitalOcean** (droplet basique 2 Go / ~12 $). À la création, choisissez :

- Image : **Ubuntu 24.04 LTS**
- Authentification : **clé SSH** si proposée (plus sûr) — sinon un mot de passe root solide
- Notez l'**adresse IP** du serveur (ex. `203.0.113.50`)

## Étape 2 — Se connecter et sécuriser le serveur

```bash
ssh root@203.0.113.50
```

Puis, sur le serveur, créez un utilisateur normal et un pare-feu :

```bash
adduser kalan                     # choisissez un mot de passe solide
usermod -aG sudo kalan
ufw allow OpenSSH && ufw allow 80 && ufw allow 443 && ufw enable
```

Déconnectez-vous (`exit`) et reconnectez-vous avec le nouvel utilisateur :
`ssh kalan@203.0.113.50`.

## Étape 3 — Installer Docker

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
exit    # puis reconnectez-vous pour que le groupe docker s'applique
```

## Étape 4 — Installer le projet

```bash
git clone https://github.com/kalandengit/python_learning_projects.git
cd python_learning_projects/expert-consortium
cp .env.example .env
nano .env      # remplissez MISTRAL_API_KEY, WEB_PASSWORD, TELEGRAM_* (Ctrl+O sauver, Ctrl+X quitter)
```

## Étape 5 — Tout démarrer

```bash
docker compose up -d --build
```

Le premier build prend quelques minutes. Vérifiez : `docker compose ps` — `web`, `bot` et
`qdrant` doivent être « running ». Votre assistant est maintenant sur
`http://203.0.113.50:8000` et votre bot Telegram est en ligne.

Ré-indexez vos documents sur le serveur (copiez-les d'abord dans `uploads/`, ex. avec
`scp -r ./uploads kalan@203.0.113.50:~/python_learning_projects/expert-consortium/`) :

```bash
docker compose exec web python -m app.cli ingest
```

## Étape 6 (recommandée) — Vrai HTTPS avec votre propre domaine

1. Achetez un domaine (~10 €/an) et ajoutez un **enregistrement DNS A** :
   `consortium.votredomaine.com → 203.0.113.50`.
2. Dans `.env`, ajoutez : `DOMAIN=consortium.votredomaine.com`
3. Dans `docker-compose.yml`, décommentez tout le bloc du service `caddy:`.
4. `docker compose up -d` — Caddy obtient le certificat automatiquement.

Votre assistant est alors sur `https://consortium.votredomaine.com` avec le cadenas. Sinon,
continuez avec `http://IP:8000` — mais préférez HTTPS avant de l'utiliser depuis un Wi-Fi
public.

## Sauvegardes

```bash
./scripts/backup.sh              # écrit des archives dans backups/ (base + logs + uploads)
```

Lancez-le avant chaque mise à jour, et copiez de temps en temps les archives hors du serveur
(`scp kalan@IP:~/python_learning_projects/expert-consortium/backups/*.tar.gz .`).

## Mettre à jour l'appli

```bash
git pull
docker compose up -d --build
```

## Liste de contrôle sécurité

- [ ] `.env` n'existe que sur le serveur et votre ordinateur — jamais dans git (déjà protégé).
- [ ] `WEB_PASSWORD` est long (12+ caractères).
- [ ] `TELEGRAM_ALLOWED_USER_ID` est renseigné (sinon le bot refuse tout le monde).
- [ ] Pare-feu actif (`sudo ufw status` → 22, 80, 443 seulement ; fermez 8000 dès que Caddy
      tourne : supprimez les lignes `ports:` du service `web` puis `docker compose up -d`).
- [ ] Qdrant n'a aucun port public (défaut de notre fichier compose).
- [ ] Un plafond de dépenses est fixé dans la console Mistral.
- [ ] Des sauvegardes existent et ont été testées une fois.
