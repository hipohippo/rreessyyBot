import logging
import sys
from configparser import SectionProxy
from typing import Union

from telegram.ext import Application, CommandHandler

from hipo_telegram_bot_common.bot_config.bot_config_parser import parse_from_ini
from hipo_telegram_bot_common.bot_factory import BotBuilder
from rreessyyBot.bot_handler import (
    find_and_publish_job,
    smoke_test_job,
    add_venue,
    remove_venue,
    show_enabled_venue,
    show_all_venue,
    add_to_venue_list_csv,
    init_cmd,
)
from rreessyyBot.resy_bot_config import ResyBotConfig


def build_bot_app(bot_config_dict: Union[dict, SectionProxy]) -> Application:
    bot_config = ResyBotConfig(bot_config_dict)
    app = (
        BotBuilder(bot_config_dict["bot_token"], bot_config)
        .add_handlers(
            [
                CommandHandler("add", add_venue),
                CommandHandler("remove", remove_venue),
                CommandHandler("show", show_enabled_venue),
                CommandHandler("listall", show_all_venue),
                CommandHandler("listadd", add_to_venue_list_csv),
            ]
        )
        .add_onetime_jobs([(init_cmd, {"when": 2})])
        .add_repeating_jobs(
            [
                (find_and_publish_job, {"first": 15, "interval": int(bot_config_dict["search_interval"])}),
                (smoke_test_job, {"first": 5, "interval": 4 * 60 * 60}),
            ]
        )
        .build()
    )
    return app


if __name__ == "__main__":
    logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
    bot_app = build_bot_app(parse_from_ini(sys.argv[1]))
    bot_app.run_polling()
