import logging
import os
from configparser import ConfigParser

import pandas as pd
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from rreessyyBot.query import find_seat
from rreessyyBot.venue_slot import Venue


async def find_and_publish_seat(context: ContextTypes.DEFAULT_TYPE):
    dt = context.bot_data["dates"][context.bot_data["current_dt_idx"]]
    context.bot_data["current_dt_idx"] = (context.bot_data["current_dt_idx"] + 1) % len(context.bot_data["dates"])
    venues = context.bot_data["venues"]

    logging.debug(f"looking for seat on {dt}")
    for party_size in context.bot_data["party_size"]:
        seat_message, no_seat_flag = find_seat(
            context.bot_data["resy_api_key"],
            context.bot_data["resy_auth_token"],
            venues,
            dt,
            party_size,
            context.bot_data["start_time"],
            context.bot_data["end_time"],
            context.bot_data["venue_id_map"],
        )
        if no_seat_flag:
            logging.debug("no seats found")
        else:
            for chat_id in context.bot_data["notify_chat"]:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=seat_message,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                )


async def job_load_dynamic_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id == context.bot_data["notify_chat"][0]:
        await job_load_dynamic_config_job(context)
    else:
        logging.error(f"unauthorized operation from {update.effective_chat.id}")


async def job_load_dynamic_config_job(context: ContextTypes.DEFAULT_TYPE):
    config_parser = ConfigParser()
    config_parser.read(os.path.join(context.bot_data["config_dir"], context.bot_data["config_file"]))
    for field, to_type in [
        ("resy_api_key", str),
        ("resy_auth_token", str),
        ("start_time", pd.Timestamp),
        ("end_time", pd.Timestamp),
        ("date_offset", int),
    ]:
        context.bot_data[field] = to_type(config_parser["dynamic_config"][field])

    context.bot_data["dates"] = [
        pd.Timestamp(x)
        for x in pd.date_range(
            pd.Timestamp.now(), pd.Timestamp.now() + pd.Timedelta(context.bot_data["date_offset"], "Day")
        )
    ]
    context.bot_data["current_dt_idx"] = 0
    context.bot_data["party_size"] = [2, 4]  # for the time being..
    logging.info(
        f'updated search dates start:{context.bot_data["dates"][0].strftime("%m-%d")}, '
        f'end: {context.bot_data["dates"][-1].strftime("%m-%d")},'
        f'start_time:{context.bot_data["start_time"].time()}, end_time:{context.bot_data["end_time"].time()}'
    )
    await refresh_venue_list(context)
    await send_smoke_test(context)


async def refresh_venue_list(context: ContextTypes.DEFAULT_TYPE):
    venue_csv = pd.read_csv(os.path.join(context.bot_data["config_dir"], context.bot_data["venue_list_file"]))
    venue_csv = venue_csv[venue_csv["enable"] == 1]
    context.bot_data["venues"] = [Venue(row["id"], row["webname"], row["city"]) for idx, row in venue_csv.iterrows()]
    context.bot_data["venue_id_map"] = {venue.id: venue for venue in context.bot_data["venues"]}
    context.bot_data["venue_id_map"].update({50746: Venue(50746, "salinas", "ny")})  ## smoke test
    logging.info(f'updated venues: {[venue.webname for venue in context.bot_data["venues"]]}')


async def send_heart_beat(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=context.bot_data["heart_beat_chat"],
        text=f"heart beat from RReessyybot at {pd.Timestamp.utcnow().strftime('%Y-%m-%d %H:%M')}",
    )


async def send_smoke_test(context):
    today = pd.Timestamp.now().weekday()
    offset = (5 - today) if today < 5 else 12 - today
    next_saturday: pd.Timestamp = pd.Timestamp.now() + pd.Timedelta(offset, "days")

    seat_message, no_seat_flag = find_seat(
        context.bot_data["resy_api_key"],
        context.bot_data["resy_auth_token"],
        [Venue(50746, "salinas", "ny")],
        next_saturday,
        4,
        context.bot_data["start_time"],
        context.bot_data["end_time"],
        context.bot_data["venue_id_map"],
    )
    if no_seat_flag:
        logging.debug("no seats found")
    else:
        await context.bot.send_message(
            chat_id=context.bot_data["heart_beat_chat"],
            text="SmokeTest" + seat_message,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
