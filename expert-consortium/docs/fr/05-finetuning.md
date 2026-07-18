# 5 — Fine-tuning de votre modèle (Français)

Le fine-tuning crée **votre modèle Mistral personnel** — entraîné sur vos meilleurs échanges
pour qu'il adopte vos domaines, votre style, votre terminologie. Tout se passe sur les
serveurs de Mistral : **aucun GPU nécessaire chez vous.**

## Quand est-ce que ça vaut le coup ?

✅ Faites-le quand :
- Vous avez utilisé l'assistant un moment et noté **au moins 50–100 réponses 👍**
  (20 est le minimum technique ; 100+ donne de vrais résultats).
- Vous voulez qu'un modèle économique (`ministral-8b`) réponde aussi bien qu'un modèle cher
  sur *vos* sujets.
- Vous voulez une cohérence de style (ex. toujours citer les articles de la même façon).

❌ Inutile quand :
- Vous venez d'ajouter de nouveaux documents — c'est le rôle du RAG, aucun entraînement requis.
- Vous avez peu d'exemples notés — le modèle changera à peine.

**Important :** le fine-tuning ne remplace PAS la base documentaire. Votre modèle fine-tuné
continue d'utiliser le RAG ; il devient simplement meilleur pour *s'en servir* à votre façon.

## Étape 1 — Collecter les données (en continu)

Deux sources, mélangées automatiquement :

1. **Les 👍 dans le chat** — chaque réponse notée « good » devient un exemple d'entraînement.
2. **Les exemples manuels** — écrivez des paires question/réponse parfaites dans
   `finetune_data/manual/mes-exemples.jsonl`, un JSON par ligne, au format de
   `finetune_data/manual/example.jsonl`. C'est de l'or : 20 réponses parfaites écrites à la
   main valent mieux que 200 médiocres.

## Étape 2 — Construire le jeu de données

```bash
python -m app.finetune.dataset
```

Crée `finetune_data/train.jsonl` (90 %) et `finetune_data/eval.jsonl` (10 % mis de côté pour
mesurer honnêtement). Refuse de tourner avec moins de 20 exemples.

## Étape 3 — Lancer l'entraînement

```bash
python -m app.finetune.train
```

Téléverse le jeu de données et démarre la tâche sur les serveurs de Mistral (base par
défaut : `ministral-8b-latest` — économique et rapide ; `--model open-mistral-7b` ou autre
pour comparer). La commande suit la progression jusqu'à la fin (de quelques minutes à ~1 h ;
coût ~1–10 $). À la fin, elle affiche l'identifiant de votre modèle, du type
`ft:ministral-8b:xxxx:yyyy`.

## Étape 4 — Comparer honnêtement avant d'adopter

```bash
python -m app.finetune.evaluate --finetuned ft:ministral-8b:xxxx:yyyy
```

Les deux modèles répondent aux questions d'évaluation avec le même contexte documentaire ;
un modèle juge impartial choisit la meilleure réponse à chaque fois. Lisez le verdict et le
rapport détaillé côte à côte dans `finetune_data/evaluation_report.md`.

## Étape 5 — L'adopter (s'il a gagné)

Dans `.env` :

```
CHAT_MODEL=ft:ministral-8b:xxxx:yyyy
```

Redémarrez l'appli. Pour revenir en arrière : `CHAT_MODEL=mistral-large-latest`.

## À propos du N'Ko (Phase 3 du PRD)

Le fine-tuning sur vos échanges notés n'apprendra PAS au modèle un N'Ko fluide — il faut
pour cela un corpus parallèle dédié (paires de phrases N'Ko ↔ français) par milliers. Si
vous constituez un tel corpus (vos documents N'Ko ingérés sont un point de départ), le même
mécanisme `finetune_data/manual/` l'accepte : chaque ligne une paire de traduction ou
d'explication. Considérez les résultats comme expérimentaux et faites-les vérifier par un
lecteur lettré en N'Ko.

**Suite :** [6 — Déploiement](06-deploy-vps.md)
