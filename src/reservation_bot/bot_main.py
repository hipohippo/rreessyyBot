# -*- coding: utf-8 -*-
import asyncio
import logging
from configparser import ConfigParser, SectionProxy
from typing import List, Union

import pandas as pd
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, ApplicationBuilder

from src.reservation_bot.platform_parser import PlatformParser
from src.reservation_bot.resy_parser import ResyParser
from src.reservation_bot.tock_parser import TockParser
from src.reservation_bot.util import remove_nonalphabet, Platform, get_chrome_driver

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(context.bot_data)
    await resume(update, context, "...start searching")


async def resume(update: Update, context: ContextTypes.DEFAULT_TYPE, message_prompt="...resume searching"):
    context.bot_data["enabled"] = True
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id=chat_id, text=message_prompt)
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


async def update_bot_search_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    received_text = update.message.text.split(" ")
    if "" in received_text:
        received_text.remove("")
    platform = remove_nonalphabet(received_text[1]).lower()
    context.bot_data["platform"] = Platform(platform)
    context.bot_data["restaurant"] = [remove_nonalphabet(received_text[2])]
    context.bot_data["parser"] = {Platform.Resy: ResyParser(), Platform.Tock: TockParser()}[
        context.bot_data["platform"]
    ]
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"{context.bot_data['restaurant']}: searching for spot on {context.bot_data['platform'].value}",
    )


def init_application_context(application, config: Union[dict, SectionProxy]):
    application.bot_data["platform"] = Platform.Tock
    application.bot_data["restaurant"]: List[str] = ["yoshinonewyork"]
    application.bot_data["party_size"] = [2]
    application.bot_data["start_time"] = pd.Timedelta("17:00:00")
    application.bot_data["cutoff_time"] = pd.Timedelta("21:30:00")
    application.bot_data["days"] = pd.Timedelta("10 D")

    application.bot_data["parser"] = {Platform.Resy: ResyParser(), Platform.Tock: TockParser()}[
        application.bot_data["platform"]
    ]

    application.bot_data["heartbeat_recipient_id"] = config["heartbeat_id"] if "heartbeat_id" in config else None
    application.bot_data["last_heart_beat"] = pd.Timestamp("2021-01-01")
    application.bot_data["heartbeat_interval"] = pd.Timedelta("4 hours")

    if not "webdriver" in application.bot_data:
        application.bot_data["webdriver"] = get_chrome_driver(config["chrome_driver"])

    return application


def init_application_handler(application):
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("pause", pause))
    application.add_handler(CommandHandler("resume", resume))
    application.add_handler(CommandHandler("update", update_bot_search_target))
    return application


def main():
    config = ConfigParser()
    config.read("sample_config.ini")
    config = config["reservation_bot"]

    application = ApplicationBuilder().token(config["token"]).build()
    init_application_context(application, config)
    init_application_handler(application)
    application.run_polling()


if __name__ == "__main__":
    main()
