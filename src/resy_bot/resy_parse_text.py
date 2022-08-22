# -*- coding: utf-8 -*-
from typing import Tuple, List

import pandas as pd


def compose_message_found(
    meal_times: List[Tuple[pd.Timestamp, str]], restaurant: str, dt: pd.Timestamp, party_size: int, link: str
):
    try:
        message = f"{restaurant}: found seat for {party_size} on {dt.strftime('%Y-%m-%d')}, {pd.Timestamp(meal_times[0][0]).strftime('%H:%M')}, {meal_times[0][1]}...{link}"
    except Exception as E:
        message = f"found seat on {dt.strftime('%Y-%m-%d')}"
    return message


def parse_spot(dt: pd.Timestamp, spot_time_str: str):
    spot_time_str = spot_time_str.split("\n")
    spot_time_str = [s for s in spot_time_str if s != ""]
    spot_times = []

    for idx in range(0, len(spot_time_str) - 1, 2):
        spot_time = spot_time_str[idx]
        spot_type = spot_time_str[idx + 1]
        parsed_time = regex_time.search(spot_time)
        if parsed_time:
            hh = int(parsed_time[1])
            mm = parsed_time[2]
            if parsed_time[3] == "PM":
                hh += 12
            spot_times.append((dt + pd.Timedelta(f"{hh}:{mm}:00"), spot_type))
    return spot_times
