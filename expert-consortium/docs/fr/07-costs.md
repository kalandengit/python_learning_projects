# 7 — Coûts (Français)

*Prix de juillet 2026 — vérifiez toujours <https://mistral.ai/pricing/> pour les chiffres à jour.*

## Développement : 0 $

Le palier gratuit **Experiment** de Mistral donne un accès (limité en débit) à tous les
modèles de l'API (≈1 milliard de tokens/mois). Il couvre toute l'installation, les tests et
un usage personnel léger.

## Usage personnel en production — estimation mensuelle typique

| Poste | Base de prix | Usage personnel typique | Coût estimé |
|---|---|---|---|
| OCR (PDF, images) | ~1–3 $ / 1 000 pages | 200 pages/mois | < 1 $ |
| Transcription audio/vidéo (Voxtral) | 0,003 $ / minute | 10 h/mois | ~1,80 $ |
| Embeddings (`mistral-embed`) | ~0,10 $ / 1M tokens | indexation + requêtes | < 0,50 $ |
| Chat (`mistral-large-latest`) | 2 $ entrée / 6 $ sortie par 1M | ~50 questions/jour | 3–8 $ |
| Chat (`mistral-small-latest`) — alternative économique | 0,10 $ / 0,30 $ par 1M | même usage | < 1 $ |
| Tâche de fine-tuning | ponctuel | occasionnel | 1–10 $ par exécution |
| VPS (Hetzner CX22 ou équivalent) | mensuel | allumé 24h/24 | 5–9 € |
| Bot Telegram | gratuit | — | 0 $ |

**Total réaliste : 6–18 € / mois.** Passez `CHAT_MODEL` à `mistral-small-latest` dans `.env`
pour diviser le coût du chat par ~10 (un Small fine-tuné égale souvent Large sur vos domaines
précis — c'est l'une des principales raisons de faire du fine-tuning).

## Conseils pour maîtriser les coûts

1. Commencez sur le palier gratuit ; n'ajoutez un moyen de paiement qu'en cas de limite atteinte.
2. Fixez un **plafond de dépenses** dans la console Mistral (Billing → Limits).
3. L'indexation est l'étape coûteuse pour les grosses archives — l'OCR de 5 000 pages coûte
   ~5–15 $, mais c'est payé **une seule fois** ; les questions ensuite coûtent très peu.
4. Surveillez la consommation dans le tableau de bord de la console Mistral.
