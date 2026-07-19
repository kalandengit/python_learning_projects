# 3 — Discuter avec le consortium (Français)

## Démarrer l'assistant

```bash
cd expert-consortium
source .venv/bin/activate
uvicorn app.main:app
```

Ouvrez <http://localhost:8000>, entrez votre `WEB_PASSWORD`. L'interface a un bouton
**FR/EN** (en haut à droite) pour changer de langue.

## Qui vous répond

Vos questions vont à un consortium de quatre experts seniors (une seule IA jouant quatre
rôles) :

| Expert | Domaine |
|---|---|
| Maître Juriste | Droit & tribunaux |
| Karamoko N'Ko | Écriture N'Ko & langues mandingues |
| Cheikh 'Ilm | Sciences islamiques, sources arabes |
| Ingénieur Système | Informatique (adapté aux débutants) |

Les questions qui touchent plusieurs domaines reçoivent une réponse commune avec une courte
conclusion unifiée.

## La règle d'or : les réponses viennent de VOS documents

- Chaque réponse factuelle cite sa source, ex. `[jugement-2024.pdf]`, aussi listée sous le
  message.
- Si vos documents ne couvrent pas la question, le consortium le dit explicitement au lieu
  d'inventer. Les connaissances générales ajoutées sont clairement signalées.
- Utilisez le **sélecteur de domaine** (barre du haut) pour restreindre la recherche à un
  domaine — utile quand un même mot a des sens différents en droit et en religion.

## Noter les réponses — cela nourrit votre futur modèle personnalisé

Sous chaque réponse : 👍 / 👎. Appuyez sur 👍 pour les réponses excellentes — **seules
celles-ci** serviront plus tard au fine-tuning de votre modèle personnel
([5 — Fine-tuning](05-finetuning.md)). Appuyez sur 👎 pour exclure les mauvaises.

## Conseils pour de meilleures réponses

1. Posez vos questions dans n'importe quelle langue — français, anglais, arabe. Le
   consortium répond dans la langue de la question.
2. Soyez précis : « Quel délai fixe le jugement de 2024 pour l'appel ? » vaut mieux que
   « Parle-moi du jugement ».
3. La conversation a une mémoire dans la session de la page ; les questions de suivi
   fonctionnent (« et quel article cite-t-il ? »).
4. Si une réponse semble incomplète, vérifiez que le document est bien indexé :
   📚 Documents → le fichier doit apparaître avec son nombre d'extraits.

**Suite :** [4 — Bot Telegram](04-telegram.md)
