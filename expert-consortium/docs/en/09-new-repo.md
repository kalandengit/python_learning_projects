# 9 — Moving the project to its own repository (English)

The project currently lives in a subfolder of `python_learning_projects`. When you want it
to have its own dedicated GitHub repository (cleaner history, its own issues, its own
deployments), follow these steps — about 5 minutes.

## Step 1 — Create the empty repository on GitHub

1. Go to <https://github.com/new>.
2. Repository name: `expert-consortium` (or any name you like).
3. Visibility: **Private** (recommended — this is your personal assistant).
4. Do **not** tick "Add a README" (we bring our own files).
5. Click **Create repository** and copy its URL, e.g.
   `https://github.com/kalandengit/expert-consortium.git`.

## Step 2 — Copy the project into it

In a terminal, from the folder that contains `python_learning_projects`:

```bash
# 1. Make a fresh copy of just the project folder
cp -r python_learning_projects/expert-consortium expert-consortium
cd expert-consortium

# 2. Start a new git history for it
git init
git add .
git commit -m "Initial commit: Expert Consortium v1.0"

# 3. Connect it to the GitHub repository you just created
git remote add origin https://github.com/kalandengit/expert-consortium.git
git branch -M main
git push -u origin main
```

Done. The project now lives at its own address.

## Step 3 — Point your deployments at the new repo

On your VPS (see [6 — Deployment](06-deploy-vps.md)), clone the new repository instead:

```bash
git clone https://github.com/kalandengit/expert-consortium.git
cd expert-consortium
```

…and continue as in the deployment guide. Your `.env`, `uploads/`, and backups are not in
git (on purpose) — copy them over manually or restore from a backup archive.

## Notes

- The copy in `python_learning_projects` can stay as an archive or be deleted later
  (`git rm -r expert-consortium` in that repo).
- If the repository is **private** and the VPS clone asks for a password, create a
  fine-grained **Personal Access Token** on GitHub (Settings → Developer settings) with
  read access to this repository, and use it as the password.
