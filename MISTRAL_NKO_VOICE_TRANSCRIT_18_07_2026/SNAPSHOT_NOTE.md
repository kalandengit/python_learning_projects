# Snapshot of MISTRAL_NKO_VOICE_TRANSCRIT_18_07_2026

This directory is a **flat snapshot** of the integrated `develop` branch of
the rebuilt N'Ko Voice Transcriptor, stored here because the session's
GitHub credentials cannot create new repositories.

The real project uses a **branch-per-component** layout
(`main` / `develop` / `backend` / `android` / `ios`). The complete
multi-branch git history is preserved in **`project.bundle`**. To restore
it into the dedicated repository:

```bash
# 1. Create the empty repo on GitHub (no README):
#    https://github.com/new  →  name: MISTRAL_NKO_VOICE_TRANSCRIT_18_07_2026

# 2. Restore all branches from the bundle and push:
git clone project.bundle MISTRAL_NKO_VOICE_TRANSCRIT_18_07_2026
cd MISTRAL_NKO_VOICE_TRANSCRIT_18_07_2026
git remote set-url origin https://github.com/kalandengit/MISTRAL_NKO_VOICE_TRANSCRIT_18_07_2026.git
for b in main develop backend android ios; do git checkout $b; done
git push -u origin main develop backend android ios
```

Backend quickstart, architecture, security model: see `README.md` and
`docs/` in this snapshot.
