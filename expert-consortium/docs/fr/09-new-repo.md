# 9 — Déplacer le projet vers son propre dépôt (Français)

Le projet vit actuellement dans un sous-dossier de `python_learning_projects`. Quand vous
voudrez lui donner son propre dépôt GitHub dédié (historique plus propre, ses propres
issues, ses propres déploiements), suivez ces étapes — environ 5 minutes.

## Étape 1 — Créer le dépôt vide sur GitHub

1. Allez sur <https://github.com/new>.
2. Nom du dépôt : `expert-consortium` (ou le nom de votre choix).
3. Visibilité : **Private** (recommandé — c'est votre assistant personnel).
4. Ne cochez **pas** « Add a README » (nous apportons nos propres fichiers).
5. Cliquez **Create repository** et copiez son URL, ex.
   `https://github.com/kalandengit/expert-consortium.git`.

## Étape 2 — Y copier le projet

Dans un terminal, depuis le dossier qui contient `python_learning_projects` :

```bash
# 1. Copie propre du seul dossier du projet
cp -r python_learning_projects/expert-consortium expert-consortium
cd expert-consortium

# 2. Démarrer un nouvel historique git
git init
git add .
git commit -m "Commit initial : Expert Consortium v1.0"

# 3. Le relier au dépôt GitHub créé à l'étape 1
git remote add origin https://github.com/kalandengit/expert-consortium.git
git branch -M main
git push -u origin main
```

Terminé. Le projet a maintenant sa propre adresse.

## Étape 3 — Pointer vos déploiements vers le nouveau dépôt

Sur votre VPS (voir [6 — Déploiement](06-deploy-vps.md)), clonez le nouveau dépôt à la
place :

```bash
git clone https://github.com/kalandengit/expert-consortium.git
cd expert-consortium
```

…et continuez comme dans le guide de déploiement. Vos `.env`, `uploads/` et sauvegardes ne
sont pas dans git (volontairement) — copiez-les manuellement ou restaurez une archive de
sauvegarde.

## Remarques

- La copie dans `python_learning_projects` peut rester comme archive ou être supprimée plus
  tard (`git rm -r expert-consortium` dans ce dépôt-là).
- Si le dépôt est **privé** et que le clone sur le VPS demande un mot de passe, créez un
  **Personal Access Token** granulaire sur GitHub (Settings → Developer settings) avec accès
  en lecture à ce dépôt, et utilisez-le comme mot de passe.
