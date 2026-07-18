# 1 — Installation depuis zéro (Français)

*Objectif : partir d'un ordinateur sans rien d'installé et arriver à votre première
conversation avec votre assistant. Durée : 30–45 minutes. Aucune connaissance en
informatique requise — copiez-collez chaque commande.*

> Les mots en **italique gras** comme ***terminal*** sont expliqués dans le
> [Glossaire](08-glossary.md).

## Étape 1 — Ouvrir un terminal

- **Windows :** touche `Windows`, tapez `PowerShell`, Entrée.
- **macOS :** `Cmd+Espace`, tapez `Terminal`, Entrée.
- **Linux :** `Ctrl+Alt+T`.

Une fenêtre noire/blanche s'ouvre. Vous y tapez des commandes puis appuyez sur Entrée.

## Étape 2 — Installer Python 3.11+

Vérifiez d'abord :

```bash
python3 --version
```

Si vous voyez `Python 3.11` ou plus, passez à l'étape suivante. Sinon, installez-le depuis
<https://www.python.org/downloads/> (Windows : cochez **« Add Python to PATH »** pendant
l'installation, puis fermez et rouvrez PowerShell).

## Étape 3 — Installer ffmpeg (nécessaire pour les vidéos)

- **Windows (PowerShell) :** `winget install ffmpeg`
- **macOS :** `brew install ffmpeg` (installez d'abord Homebrew depuis <https://brew.sh>)
- **Linux (Debian/Ubuntu) :** `sudo apt install ffmpeg`

Vérification : `ffmpeg -version` doit afficher plusieurs lignes.

## Étape 4 — Récupérer le projet

```bash
git clone https://github.com/kalandengit/python_learning_projects.git
cd python_learning_projects/expert-consortium
```

## Étape 5 — Créer un environnement virtuel et installer

Un ***environnement virtuel*** est une boîte privée pour les bibliothèques Python de ce projet.

```bash
python3 -m venv .venv
source .venv/bin/activate      # Windows PowerShell : .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

L'installation prend quelques minutes. Relancez la ligne `activate` chaque fois que vous
ouvrez un nouveau terminal pour ce projet (le préfixe `(.venv)` apparaît quand c'est actif).

## Étape 6 — Obtenir votre clé API Mistral (gratuit)

1. Allez sur <https://console.mistral.ai> et créez un compte.
2. Choisissez le plan gratuit **Experiment** quand on vous le demande (pas de carte bancaire
   nécessaire pour le développement).
3. Ouvrez **API Keys** → **Create new key** → copiez la clé (une longue chaîne aléatoire).
   ⚠️ Elle n'est affichée qu'une seule fois — copiez-la maintenant.

## Étape 7 — Configurer le projet

```bash
cp .env.example .env           # Windows PowerShell : copy .env.example .env
```

Ouvrez le fichier `.env` avec n'importe quel éditeur de texte (le Bloc-notes suffit) et :

1. Collez votre clé après `MISTRAL_API_KEY=` (sans espaces, sans guillemets).
2. Remplacez `change-me-please` après `WEB_PASSWORD=` par un mot de passe de votre choix.

Enregistrez et fermez. **Ce fichier ne doit jamais être partagé ni commité dans git** — il
contient votre clé secrète (le `.gitignore` du projet le protège déjà).

## Étape 8 — Premier lancement

Mettez un fichier de test (n'importe quel PDF ou document Word) dans le dossier `uploads/`,
puis :

```bash
python -m app.cli ingest       # lit et indexe tout le contenu de uploads/
uvicorn app.main:app           # démarre l'assistant web
```

Ouvrez <http://localhost:8000> dans votre navigateur, entrez votre `WEB_PASSWORD`, et posez
une question sur votre document de test. Vous devez obtenir une réponse avec le fichier cité
en dessous.

Pour arrêter l'assistant : `Ctrl+C` dans le terminal.

## Dépannage

| Symptôme | Solution |
|---|---|
| `python3: command not found` | Essayez `python`, ou réinstallez Python avec « Add to PATH » |
| `MISTRAL_API_KEY is not set` | L'étape 7 a été sautée ou `.env` est au mauvais endroit — il doit être à côté de `README.md` |
| `401 Unauthorized` de Mistral | Clé collée avec des espaces/guillemets, ou désactivée — créez-en une nouvelle |
| La page redemande le mot de passe | Vérifiez `WEB_PASSWORD` dans `.env`, redémarrez `uvicorn` après modification |

**Suite :** [2 — Ajouter des documents](02-upload.md)
