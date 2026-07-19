# 3 — Chatting with the consortium (English)

## Start the assistant

```bash
cd expert-consortium
source .venv/bin/activate
uvicorn app.main:app
```

Open <http://localhost:8000>, enter your `WEB_PASSWORD`. The interface has an **FR/EN**
button (top right) to switch language.

## Who answers you

Your questions go to a consortium of four senior experts (a single AI playing four roles):

| Expert | Domain |
|---|---|
| Maître Juriste | Law & courts |
| Karamoko N'Ko | N'Ko writing & Manding languages |
| Cheikh 'Ilm | Islamic sciences, Arabic sources |
| Ingénieur Système | Computer science (beginner-friendly) |

Questions that span domains get a joint answer with a short unified conclusion.

## The golden rule: answers come from YOUR documents

- Every factual answer cites its source like `[jugement-2024.pdf]`, also listed under the
  message.
- If your documents don't cover the question, the consortium says so explicitly instead of
  inventing an answer. General knowledge, when added, is clearly labelled.
- Use the **domain selector** (top bar) to restrict the search to one domain — useful when
  the same word means different things in law and religion.

## Rating answers — this feeds your future custom model

Under each answer: 👍 / 👎. Press 👍 on answers you find excellent — **only those** are used
later to fine-tune your personal model ([5 — Fine-tuning](05-finetuning.md)). Press 👎 on bad
ones so they are excluded.

## Tips for better answers

1. Ask in any language — French, English, Arabic. The consortium answers in the language of
   the question.
2. Be specific: "What deadline does the 2024 ruling set for the appeal?" beats "Tell me about
   the ruling".
3. The conversation has memory within the page session; follow-up questions work
   ("and what article does it cite?").
4. If an answer seems incomplete, check the document was actually indexed:
   📚 Documents → the file should appear with its chunk count.

**Next:** [4 — Telegram bot](04-telegram.md)
