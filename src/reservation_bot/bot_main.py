# -*- coding: utf-8 -*-
import logging
import os
from configparser import ConfigParser, SectionProxy
from typing import List, Union

import pandas as pd
from telegram.ext import CommandHandler, ApplicationBuilder

from reservation_bot.bot_handler import start, resume, pause, change_bot_search_target
from reservation_bot.resy_parser import ResyParser
from reservation_bot.tock_parser import TockParser
from reservation_bot.util import Platform, get_chrome_driver

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


def init_application_context(application, config: Union[dict, SectionProxy]):
    application.bot_data["platform"] = Platform.Tock
    application.bot_data["restaurant"]: List[str] = ["yoshinonewyork"]
    application.bot_data["party_size"] = [2]
    application.bot_data["start_time"] = pd.Timedelta("17:00:00")
    application.bot_data["cutoff_time"] = pd.Timedelta("22:30:00")
    application.bot_data["days"] = pd.Timedelta("14 D")

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
    application.add_handler(CommandHandler("change", change_bot_search_target))
    return application


def load_config_from_ini(config_ini_file: str, section_name: str) -> SectionProxy:
    config = ConfigParser()
    if not os.path.isfile(config_ini_file):
        raise RuntimeError(f"cannot find {config_ini_file}")
    config.read(config_ini_file)
    return config[section_name]


def main():
    config = load_config_from_ini("../../../reservation_bot.ini", "reservation_bot")
    application = ApplicationBuilder().token(config["token"]).build()
    init_application_context(application, config)
    init_application_handler(application)
    application.run_polling()


if __name__ == "__main__":
    main()
