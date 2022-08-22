# -*- coding: utf-8 -*-
import logging
import os
import re
import time
from typing import Tuple, List

import pandas as pd
from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, ApplicationBuilder

from src.resy_bot.resy_parse_text import parse_spot, compose_message_found

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

web_regex = re.compile("Dinner([.\s\S\r]*)Notify")
regex_time = re.compile("(\d+):(\d+)([AP]M)")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(context.bot_data)
    if not "webdriver" in context.bot_data:
        geckodriver = "c:/users/weiwe/geckodriver/geckodriver.exe"
        profile = webdriver.FirefoxProfile()
        profile.add_extension(extension="c:/users/weiwe/geckodriver/bypasspaywalls.xpi")
        driver = webdriver.Firefox(firefox_profile=profile, executable_path=geckodriver)
        context.bot_data["webdriver"] = driver

    context.bot_data["restaurants"] = ["don-angie"]
    context.bot_data["party_size"] = [2, 4]
    context.bot_data["start_time"] = pd.Timedelta("16:00:00")
    context.bot_data["cutoff_time"] = pd.Timedelta("20:30:00")
    context.bot_data["days"] = pd.Timedelta("6 D")

    context.bot_data["myId"] = 352871339
    context.bot_data["last_heart_beat"] = pd.Timestamp("2021-01-01")
    await resume(update, context)


async def resume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.bot_data["enabled"] = True
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id=chat_id, text="...resume polling job")
    context.job_queue.run_once(find_spot_polling, when=0, name="find_spot_polling", chat_id=chat_id)


async def pause(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    context.bot_data["enabled"] = False
    await context.bot.send_message(chat_id=chat_id, text="...pause polling job")


async def find_spot_polling(context):
    while True:
        if not context.bot_data["enabled"]:
            break
        for dt in pd.date_range(pd.Timestamp.now().date(), pd.Timestamp.now().date() + context.bot_data["days"]):
            for restaurant in context.bot_data["restaurants"]:
                for party_size in context.bot_data["party_size"]:
                    link = compose_link(restaurant, dt, party_size)
                    meal_times, content = search_spot(context.bot_data["webdriver"], dt, link)
                    meal_times_filtered = [
                        meal_time
                        for meal_time in meal_times
                        if dt + context.bot_data["start_time"]
                        <= pd.Timestamp(meal_time[0])
                        <= dt + context.bot_data["cutoff_time"]
                    ]
                    if len(meal_times_filtered) > 0:
                        message = compose_message_found(meal_times_filtered, restaurant, dt, party_size, link)
                        await context.bot.send_message(chat_id=context.job.chat_id, text=message)
                    else:
                        logging.info(f"{restaurant} on {dt} for {party_size} not found")
                    await send_heart_beat(context)


def compose_link(restaurant: str, dt: pd.Timestamp, party_size: int):
    return f"https://resy.com/cities/ny/{restaurant}?date={dt.strftime('%Y-%m-%d')}&seats={party_size}"




def search_spot(driver: WebDriver, dt: pd.Timestamp, link: str) -> Tuple[List[Tuple[pd.Timestamp, str]], str]:
    try:
        driver.get(link)
    except:
        print("connection closed. wait")
        time.sleep(120)
    time.sleep(5)
    content = driver.find_element_by_tag_name("body").text
    regex_matched = web_regex.search(content)
    if regex_matched:
        meal_times = parse_spot(dt, regex_matched[1])
    else:
        meal_times = []
    return meal_times, content


async def send_heart_beat(context):
    if (pd.Timestamp.now().minute in [0, 1, 30, 31]) and pd.Timestamp.now() - context.bot_data[
        "last_heart_beat"
    ] >= pd.Timedelta("15 min"):
        # context.bot.send_message(chat_id=update.effective_chat.id, text=f"heartbeat")
        await context.bot.send_message(context.bot_data["myId"], text=f"heartbeat")
        context.bot_data["last_heart_beat"] = pd.Timestamp.now()


def main():
    token_file = os.path.join(os.path.dirname(__file__), "../../../../resy_bot.token")
    with open(token_file, "r") as token:
        resy_bot_token = token.readline()[:-1]
    application = ApplicationBuilder().token(resy_bot_token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("pause", pause))
    application.add_handler(CommandHandler("resume", resume))
    application.run_polling()


if __name__ == "__main__":
    main()
