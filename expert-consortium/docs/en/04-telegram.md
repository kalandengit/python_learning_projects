# 4 — Telegram bot (English)

Talk to your consortium from your phone. Setup takes ~5 minutes and is free.

## Step 1 — Create your bot with BotFather

1. In Telegram, search for **@BotFather** (blue verified check) and open it.
2. Send `/newbot`.
3. Give it a display name, e.g. `Mon Consortium`.
4. Give it a username ending in `bot`, e.g. `kalan_consortium_bot`.
5. BotFather replies with a **token** like `1234567890:AAF...xyz`. Copy it.

## Step 2 — Find your personal Telegram ID

1. Search for **@userinfobot** and open it.
2. Send `/start` — it replies with your numeric **Id** (e.g. `987654321`). Copy it.

This ID locks the bot to you: anyone else who finds your bot gets refused. Without it the
bot refuses everyone.

## Step 3 — Configure and start

Add both values to your `.env` file:

```
TELEGRAM_BOT_TOKEN=1234567890:AAF...xyz
TELEGRAM_ALLOWED_USER_ID=987654321
```

Then start the bot (in its own terminal, alongside the web app or alone):

```bash
source .venv/bin/activate
python -m app.bots.telegram_bot
```

## Step 4 — Use it

Open your bot in Telegram (search its username), press **Start**, and:

- **Ask anything** by typing — same consortium, same knowledge base, sources shown with 📎.
- **Send a file** (PDF, Word, image, audio, video, or even a voice message) — it is ingested
  into the knowledge base automatically.
- `/docs` — list what the assistant knows.
- `/reset` — start a fresh conversation (forgets the current thread's context).

## Notes

- The bot must be *running* on your computer (or your server, see
  [6 — Deployment](06-deploy-vps.md)) to answer.
- Files sent from Telegram get the domain `general`; use uploads/ subfolders or the web page
  when you want precise domain tags.
- If the bot answers "Private bot" with a number: that number is your real ID — put it in
  `TELEGRAM_ALLOWED_USER_ID` and restart the bot.

**Next:** [5 — Fine-tuning](05-finetuning.md)
