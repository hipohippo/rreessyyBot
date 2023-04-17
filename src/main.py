import logging
import os
import sys
from configparser import SectionProxy, ConfigParser
from typing import List, Union

from telegram.ext import ApplicationBuilder, CommandHandler, Application

from rreessyyBot.bot_handler import (
    find_and_publish_seat,
    send_heart_beat,
    send_smoke_test,
    job_load_dynamic_config,
    job_load_dynamic_config_job,
)


def load_config_from_ini(sysargv: List[str], section_name: str) -> SectionProxy:
    working_dir = sysargv[1]
    config_file_name = sysargv[2]
    config_ini_file = os.path.join(working_dir, config_file_name)
    config_parser = ConfigParser()
    if not os.path.isfile(config_ini_file):
        raise RuntimeError(f"cannot find {config_ini_file}")
    config_parser.read(config_ini_file)
    config = config_parser[section_name]
    return config


def init_application_context(
    application: Application, config: Union[dict, SectionProxy], sysargv: List[str]
) -> Application:
    application.bot_data["config_dir"] = sysargv[1]
    application.bot_data["config_file"] = sysargv[2]
    application.bot_data["venue_list_file"] = sysargv[3]
    application.bot_data["heart_beat_chat"] = config["heart_beat_chat"]
    application.bot_data["notify_chat"] = [int(chat_id.strip()) for chat_id in config["notify_chat"].split(",")]
    return application


def init_application_handler(application: Application) -> Application:
    application.job_queue.run_once(job_load_dynamic_config_job, when=2)
    application.job_queue.run_repeating(find_and_publish_seat, first=15, interval=15)
    application.job_queue.run_repeating(send_smoke_test, first=10, interval=4 * 60 * 60)
    application.job_queue.run_repeating(send_heart_beat, first=20, interval=60 * 60)
    application.add_handler(CommandHandler("refresh", job_load_dynamic_config))
    return application


if __name__ == "__main__":
    logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
    logger = logging.getLogger(__name__)

    config = load_config_from_ini(sys.argv, "rreessyy_bot")
    application = (
        ApplicationBuilder().token(config["token"]).http_version("1.1").get_updates_http_version("1.1").build()
    )
    application = init_application_context(application, config, sys.argv)
    application = init_application_handler(application)
    application.run_polling()
