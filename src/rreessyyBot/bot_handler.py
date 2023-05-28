import logging
from typing import Set

import pandas as pd
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from hipo_telegram_bot_common.util import restricted
from rreessyyBot.query.query import find_seat
from rreessyyBot.query.venue_slot import Venue
from rreessyyBot.resy_bot_config import ResyBotConfig


@restricted
async def add_venue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_config: ResyBotConfig = context.bot_data["bot_config"]
    venue_webname = update.message.text.split(" ")[1]
    venue = bot_config.venue_webname_map.get(venue_webname, None)

    if venue is None:
        await update.effective_chat.send_message(f"{venue_webname} not supported")
    elif venue in bot_config.enabled_venues:
        await update.effective_chat.send_message(f"{venue_webname} already enabled")
    else:
        bot_config.enabled_venues.add(venue)
        await update.effective_chat.send_message(f"{venue_webname} added")
    return


@restricted
async def remove_venue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_config: ResyBotConfig = context.bot_data["bot_config"]
    venue_webname = update.message.text.split(" ")[1]
    venue = bot_config.venue_webname_map.get(venue_webname, None)

    if venue is not None and venue in bot_config.enabled_venues:
        bot_config.enabled_venues.remove(venue)
        await update.effective_chat.send_message(f"{venue} removed")
    else:
        await update.effective_chat.send_message(f"{venue} not enabled or not supported")
    return


@restricted
async def show_enabled_venue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_config: ResyBotConfig = context.bot_data["bot_config"]
    # if update and update.message and update.message.text:
    await update.effective_chat.send_message("\n".join([venue.webname for venue in bot_config.enabled_venues]))
    return


@restricted
async def show_all_venue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_config: ResyBotConfig = context.bot_data["bot_config"]
    # if update and update.message and update.message.text:
    await update.effective_chat.send_message("\n".join([webname for webname in bot_config.all_venue_df["webname"]]))
    return


@restricted
async def add_to_venue_list_csv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_config: ResyBotConfig = context.bot_data["bot_config"]
    split_msg = update.message.text.split(" ")
    webname = split_msg[1]
    id = int(split_msg[2])
    city = split_msg[3]

    venue = bot_config.venue_webname_map.get(webname, None)
    if venue is None:
        bot_config.add_venue_to_list_file(Venue(id, webname, city))
        await update.effective_chat.send_message(f"{webname} added to the list file")
    else:
        await update.effective_chat.send_message(f"{webname} already in the list")


async def find_and_publish_job(context: ContextTypes.DEFAULT_TYPE):
    bot_config: ResyBotConfig = context.bot_data["bot_config"]
    dt = bot_config.dates[bot_config.current_dt_idx]
    bot_config.current_dt_idx = (bot_config.current_dt_idx + 1) % len(bot_config.dates)
    enabled_venues: Set[Venue] = bot_config.enabled_venues

    logging.debug(f"querying {dt}")
    for party_size in bot_config.party_size:
        seat_message, no_seat_flag = find_seat(
            bot_config.resy_api_key,
            bot_config.resy_auth_token,
            enabled_venues,
            dt,
            party_size,
            bot_config.start_time,
            bot_config.end_time,
            bot_config.venue_id_map,
        )
        if no_seat_flag:
            logging.debug("no seats found")
        else:
            for chat_id in bot_config.publish_chat:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=seat_message,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                )
    return


async def smoke_test_job(context: ContextTypes.DEFAULT_TYPE):
    bot_config: ResyBotConfig = context.bot_data["bot_config"]
    today = pd.Timestamp.now().weekday()
    offset = (5 - today) if today < 5 else 12 - today
    next_saturday: pd.Timestamp = pd.Timestamp.now() + pd.Timedelta(offset, "days")

    seat_message, no_seat_flag = find_seat(
        bot_config.resy_api_key,
        bot_config.resy_auth_token,
        {Venue(50746, "salinas", "ny")},
        next_saturday,
        4,
        bot_config.start_time,
        bot_config.end_time,
        bot_config.venue_id_map,
    )
    if no_seat_flag:
        logging.debug("no seats found")
    else:
        await context.bot.send_message(
            chat_id=bot_config.heart_beat_chat,
            text="SmokeTest" + seat_message,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
    return
