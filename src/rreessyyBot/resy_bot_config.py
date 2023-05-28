import logging
from typing import List, Set, Tuple

import pandas as pd

from hipo_telegram_bot_common.bot_config.bot_config import BotConfig
from hipo_telegram_bot_common.util import format_white_list
from rreessyyBot.query.venue_slot import Venue


class ResyBotConfig(BotConfig):
    def __init__(self, config_dict: dict):
        super().__init__(
            config_dict["heart_beat_chat"],
            config_dict["error_notify_chat"],
            format_white_list(config_dict["white_list"]),
            "Resy Bot",
        )
        self.publish_chat: List[int] = format_white_list(config_dict["publish_chat"])
        self.resy_api_key: str = config_dict["resy_api_key"]
        self.resy_auth_token: str = config_dict["resy_auth_token"]
        self.start_time: pd.Timestamp = pd.Timestamp(config_dict["start_time"])
        self.end_time: pd.Timestamp = pd.Timestamp(config_dict["end_time"])
        self.venue_list_file: str = config_dict["venue_list_file"]
        self.date_range: int = int(config_dict["date_range"])
        # self.dynamic_config_file = config_dict["dynamic_config_file"]
        # dynamic
        self.dates: List[pd.Timestamp] = [
            pd.Timestamp(x)
            for x in pd.date_range(pd.Timestamp.now(), pd.Timestamp.now() + pd.Timedelta(self.date_range, "Day"))
        ]
        self.current_dt_idx: int = 0
        self.party_size: Tuple = (2, 3, 4)
        self._populate_venue_field()

    @property
    def venue_id_map(self):
        return self._venue_id_map

    @property
    def venue_webname_map(self):
        return self._venue_webname_map

    def add_venue_to_list_file(self, venue: Venue):
        new_df = pd.concat(
            [
                pd.read_csv(self.venue_list_file),
                pd.DataFrame({"webname": [venue.webname], "id": [venue.id], "city": [venue.city], "enable": [0]}),
            ]
        )
        new_df.reset_index(drop=True).to_csv(self.venue_list_file, index=False)
        self._populate_venue_field()

    def _populate_venue_field(self):
        self.all_venue_df: pd.DataFrame = pd.read_csv(self.venue_list_file)
        self.enabled_venues: Set[Venue] = {
            Venue(row["id"], row["webname"], row["city"])
            for idx, row in self.all_venue_df[self.all_venue_df["enable"] == 1].iterrows()
        }
        logging.info(
            f'updated search dates start:{self.dates[0].strftime("%m-%d")}, '
            f'end: {self.dates[-1].strftime("%m-%d")},'
            f"start_time:{self.start_time.time()}, end_time:{self.end_time.time()}"
        )
        self._venue_id_map = {
            int(row["id"]): Venue(row["id"], row["webname"], row["city"]) for idx, row in self.all_venue_df.iterrows()
        }
        self._venue_webname_map = {
            row["webname"]: Venue(row["id"], row["webname"], row["city"]) for idx, row in self.all_venue_df.iterrows()
        }
