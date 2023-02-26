import asyncio
import logging

import pandas as pd
from telegram import Update
from telegram.ext import ContextTypes

from reservation_bot.platform_parser import PlatformParser
from reservation_bot.resy_parser import ResyParser
from reservation_bot.tock_parser import TockParser
from reservation_bot.util import remove_nonalphabet, Platform


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(context.bot_data)
    await resume(update, context, "...start searching")


async def resume(update: Update, context: ContextTypes.DEFAULT_TYPE, message_prompt="...resume searching"):
    context.bot_data["enabled"] = True
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id=chat_id, text=f"{message_prompt} {context.bot_data['restaurant']}")
    context.job_queue.run_once(find_spot_polling, when=0, name="find_spot_polling", chat_id=chat_id)


async def pause(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    context.bot_data["enabled"] = False
    await context.bot.send_message(chat_id=chat_id, text="...pause searching")


async def find_spot_polling(context):
    parser: PlatformParser = context.bot_data["parser"]
    while True:
        for dt in pd.date_range(pd.Timestamp.now().date(), pd.Timestamp.now().date() + context.bot_data["days"]):
            for restaurant in context.bot_data["restaurant"]:
                for party_size in context.bot_data["party_size"]:
                    await asyncio.sleep(1)
                    if not context.bot_data["enabled"]:
                        return
                    spots, content = parser.extract_available_spots_from_page(
                        restaurant, dt, party_size, context.bot_data["webdriver"]
                    )
                    spots_filtered = [
                        spot
                        for spot in spots
                        if dt + context.bot_data["start_time"]
                        <= pd.Timestamp(spot[0])
                        <= dt + context.bot_data["cutoff_time"]
                    ]
                    if len(spots_filtered) > 0:
                        message = parser.compose_message_found(spots_filtered, restaurant, dt, party_size)
                        await context.bot.send_message(chat_id=context.job.chat_id, text=message)
                    else:
                        logging.info(f"{restaurant} on {dt} for {party_size} not found")
                    await send_heart_beat(None, context)


async def send_heart_beat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if pd.Timestamp.now() - context.bot_data["last_heart_beat"] >= context.bot_data["heartbeat_interval"]:
        context.bot_data["last_heart_beat"] = pd.Timestamp.now()
        if context.bot_data["heartbeat_recipient_id"]:
            await context.bot.send_message(context.bot_data["heartbeat_recipient_id"], text=f"heartbeat")


async def change_bot_search_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    received_text = update.message.text.split(" ")
    if "" in received_text:
        received_text.remove("")
    if len(received_text) != 3:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="/change need at least 2 arguments. Example: __/change resy don-angies__",
        )
    else:
        platform = remove_nonalphabet(received_text[1]).lower()
        if platform not in [v.value for v in Platform]:
            await context.bot.send_message(
                chat_id=update.effective_chat.id, text=f"cannot recognize {platform}",
            )
        context.bot_data["platform"] = Platform(platform)
        context.bot_data["restaurant"] = [remove_nonalphabet(received_text[2])]
        context.bot_data["parser"] = {Platform.Resy: ResyParser(), Platform.Tock: TockParser()}[
            context.bot_data["platform"]
        ]
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"{context.bot_data['restaurant']}: searching for spot on {context.bot_data['platform'].value}",
        )
