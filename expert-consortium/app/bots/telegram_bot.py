"""Telegram interface to the Expert Consortium.

Run with:  python -m app.bots.telegram_bot
Requires TELEGRAM_BOT_TOKEN and TELEGRAM_ALLOWED_USER_ID in .env
(setup guide: docs/en/04-telegram.md / docs/fr/04-telegram.md).
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from pathlib import Path

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from app.config import settings, setup_logging
from app.ingestion import indexer, router as ingest_router
from app.rag import chat as rag_chat

logger = setup_logging()

# Per-chat conversation history, capped in rag_chat.ask
_histories: dict[int, list[dict]] = defaultdict(list)

WELCOME = (
    "🧠 *Expert Consortium*\n\n"
    "Posez-moi une question sur vos documents / Ask me about your documents.\n"
    "Envoyez un fichier (PDF, Word, image, audio, vidéo) pour l'ajouter à la base.\n\n"
    "Commandes : /start  /docs  /reset"
)


def is_allowed(user_id: int | None) -> bool:
    allowed = settings.telegram_allowed_user_id.strip()
    return bool(allowed) and str(user_id) == allowed


async def _guard(update: Update) -> bool:
    user = update.effective_user
    if user is None or not is_allowed(user.id):
        if update.message:
            await update.message.reply_text(
                "⛔ Private bot. / Bot privé.\n"
                f"Your Telegram id: {user.id if user else '?'} — put it in "
                "TELEGRAM_ALLOWED_USER_ID in .env to authorize yourself."
            )
        logger.warning("Rejected Telegram user %s", user.id if user else None)
        return False
    return True


async def cmd_start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    if await _guard(update):
        await update.message.reply_text(WELCOME, parse_mode="Markdown")


async def cmd_reset(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    if await _guard(update):
        _histories.pop(update.effective_chat.id, None)
        await update.message.reply_text("🧹 Conversation reset.")


async def cmd_docs(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _guard(update):
        return
    docs = await asyncio.to_thread(indexer.list_documents)
    if not docs:
        await update.message.reply_text("📚 Base vide / Knowledge base is empty.")
        return
    lines = [f"• {d['source_file']} — {d['chunks']} chunks [{d['domain']}]" for d in docs]
    await update.message.reply_text("📚\n" + "\n".join(lines[:60]))


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _guard(update):
        return
    question = update.message.text or ""
    chat_id = update.effective_chat.id
    await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
    try:
        result = await asyncio.to_thread(
            rag_chat.ask, question, None, _histories[chat_id]
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Telegram chat failed")
        await update.message.reply_text(f"⚠ Erreur / Error: {exc}")
        return
    _histories[chat_id].extend(
        [{"role": "user", "content": question},
         {"role": "assistant", "content": result.answer}]
    )
    text = result.answer
    if result.sources:
        text += "\n\n📎 " + ", ".join(result.sources)
    # Telegram caps messages at 4096 chars
    for i in range(0, len(text), 4000):
        await update.message.reply_text(text[i : i + 4000])


async def on_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _guard(update):
        return
    msg = update.message
    if msg.document:
        tg_file, name = msg.document, msg.document.file_name or "document"
    elif msg.audio:
        tg_file, name = msg.audio, msg.audio.file_name or "audio.mp3"
    elif msg.voice:
        tg_file, name = msg.voice, f"voice-{msg.id}.ogg"
    elif msg.photo:
        tg_file, name = msg.photo[-1], f"photo-{msg.id}.jpg"
    elif msg.video:
        tg_file, name = msg.video, msg.video.file_name or f"video-{msg.id}.mp4"
    else:
        return

    name = Path(name).name
    if Path(name).suffix.lower() not in ingest_router.SUPPORTED_EXTS:
        await msg.reply_text(f"⚠ Type non pris en charge / Unsupported type: {name}")
        return

    # Telegram bots cannot download files larger than 20 MB.
    size = getattr(tg_file, "file_size", None)
    if size and size > 20 * 1024 * 1024:
        await msg.reply_text(
            f"⚠ {name} fait {size / 1_000_000:.0f} MB — Telegram limite les bots à "
            "20 MB. / Telegram caps bot downloads at 20 MB.\n"
            "→ Utilisez la page web ou le dossier uploads/ pour ce fichier. / "
            "Use the web page or the uploads/ folder for this file."
        )
        return

    await msg.reply_text(f"⏳ Ingestion de {name}…")
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    target = settings.uploads_dir / name
    file_obj = await context.bot.get_file(tg_file.file_id)
    await file_obj.download_to_drive(str(target))
    try:
        doc = await asyncio.to_thread(ingest_router.extract, target)
        n = await asyncio.to_thread(indexer.index_document, doc)
        await msg.reply_text(
            f"✅ {name}: {n} chunks (domain={doc.domain}, lang={doc.language})"
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Telegram ingestion failed for %s", name)
        await msg.reply_text(f"✗ Échec / Failed: {exc}")


def build_application() -> Application:
    if not settings.telegram_bot_token:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is not set in .env — see docs/en/04-telegram.md"
        )
    app = Application.builder().token(settings.telegram_bot_token).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("reset", cmd_reset))
    app.add_handler(CommandHandler("docs", cmd_docs))
    app.add_handler(
        MessageHandler(
            filters.Document.ALL | filters.AUDIO | filters.VOICE | filters.PHOTO
            | filters.VIDEO,
            on_file,
        )
    )
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    return app


def main() -> None:
    application = build_application()
    logger.info("Telegram bot starting (polling)...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
