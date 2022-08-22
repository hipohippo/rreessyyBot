# -*- coding: utf-8 -*-
import re
import time
from typing import List, Tuple

import pandas as pd
from selenium.webdriver.remote.webdriver import WebDriver

from src.reservation_bot.platform_parser import PlatformParser


class ResyParser(PlatformParser):

    _resy_regex = re.compile("Dinner([.\s\S\r]*)Notify")
    _time_regex = re.compile("(\d+):(\d+)([AP]M)")

    def _compose_link(self, restaurant: str, dt: pd.Timestamp, party_size: int):
        return f"https://resy.com/cities/ny/{restaurant}?date={dt.strftime('%Y-%m-%d')}&seats={party_size}"

    def _extract_relevant_content_from_page(self, driver: WebDriver, link: str) -> str:
        try:
            driver.get(link)
        except:
            print("connection closed. wait")
            time.sleep(120)
        time.sleep(2)
        content = driver.find_element_by_tag_name("body").text
        regex_matched = self._resy_regex.search(content)

        if regex_matched:
            return regex_matched[1]
        else:
            return ""

    def _parse_spot_time_string(self, dt: pd.Timestamp, spot_content_string: str) -> List[Tuple[pd.Timestamp, str]]:
        spot_content_string = spot_content_string.split("\n")
        spot_content_string = [s for s in spot_content_string if s != ""]
        spot_times = []
        for idx in range(0, len(spot_content_string) - 1, 2):
            spot_time = spot_content_string[idx]
            spot_type = spot_content_string[idx + 1]
            parsed_time = self._time_regex.search(spot_time)
            if parsed_time:
                hh = int(parsed_time[1])
                mm = parsed_time[2]
                if parsed_time[3] == "PM":
                    hh += 12
                spot_times.append((dt + pd.Timedelta(f"{hh}:{mm}:00"), spot_type))
        return spot_times
