import asyncio

from telegram import Update
from telegram.ext import ContextTypes, ApplicationBuilder, filters, CommandHandler, MessageHandler
import logging
from mistralai import Mistral
import re
import time
import redis.asyncio as redis
import json


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="This is the proxy for LLMs, currently working with Mistral. Send anything and you'll get an answer!"
    )


async def message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("User %s asked: %s", update.effective_user.name, update.effective_message.text)
    user_id = str(update.effective_user.id)
    # checking if already generating something
    user_is_generating = await redis_client.get(user_id)
    if user_is_generating is not None:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Please, wait the completion of the previous query."
        )
        return

    # therefore start generating
    print("setting user")
    await redis_client.set(user_id, "generating")

    response = await llm_client.chat.stream_async(
        model=model,
        messages=[
            {
                "role": "user",
                "content": update.message.text
            }
        ]
    )

    current_message = await context.bot.send_message(chat_id=update.effective_chat.id, text="Processing the message")
    edited = False
    time_limit = 1
    last_sent = None
    batch = ""
    cumulative = ""
    async for chunk in response:
        delta = chunk.data.choices[0].delta.content
        if delta is None:
            continue
        if re.search(r"\w", delta) is None:
            cumulative += delta
            continue

        delta = cumulative + delta
        cumulative = ''
        batch += delta

        if last_sent is None or time.time() - last_sent > time_limit:
            if not edited:
                current_message = await current_message.edit_text(batch)
                edited = True
            else:
                current_message = await current_message.edit_text(current_message.text + batch)
            batch = ''
            last_sent = time.time()
    if len(batch) > 0:
        await current_message.edit_text(current_message.text + batch)

    await redis_client.delete(user_id)


llm_client = None
model = "mistral-large-latest"
redis_client = None


if __name__ == "__main__":
    tokenValue = open("bot_token.csv", "r").readline()
    application = ApplicationBuilder().token(tokenValue).build()

    mistral_token = open("mistral_token.csv", "r").readline()
    llm_client = Mistral(mistral_token)

    redis_client = redis.Redis(host="redis", port=6379, db=0, decode_responses=True)
    redis_client.flushall(asynchronous=True)

    handlers = list()
    handlers.append(CommandHandler("start", start))
    handlers.append(MessageHandler(filters.TEXT, message))

    for handler in handlers:
        application.add_handler(handler)

    application.run_polling()