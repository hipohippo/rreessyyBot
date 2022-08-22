# -*- coding: utf-8 -*-
import logging
import re
import time
from typing import Tuple, List

import pandas as pd
from selenium.webdriver.remote.webdriver import WebDriver

from src.reservation_bot.platform_parser import PlatformParser


class TockParser(PlatformParser):
    _time_regex = re.compile("(\d+):(\d+) ([AP]M)")

    def _compose_link(self, restaurant: str, dt: pd.Timestamp, party_size: int):
        return f"https://www.exploretock.com/{restaurant}/search?date={dt.strftime('%Y-%m-%d')}&size={party_size}&time=18:00"

    def _extract_relevant_content_from_page(self, driver: WebDriver, link: str) -> str:
        try:
            driver.get(link)
            time.sleep(2)
            content = driver.find_element_by_class_name("SearchModalExperiences-itemTimes").text
        except Exception as e:
            logging.info(e)
            content = ""
        return content

    def _parse_spot_time_string(self, dt: pd.Timestamp, spot_content_string: str) -> List[Tuple[pd.Timestamp, str]]:
        """
        :param dt: date
        :param spot_content_string:
        `sample message if no availability:
            Sold out for parties of 2 on Nov 14
            Next available
            Join waitlist
        `sample message if there is a spot:
            5:45 PM
            $495 x 2
            8:45 PM
            $495 x 2
        :return:
        """
        if spot_content_string.find("Sold out") >= 0:
            return []
        else:
            spots = []
            for content_line in spot_content_string.split("\n"):
                parsed_time = self._time_regex.search(content_line)
                if parsed_time:
                    hh = int(parsed_time[1])
                    mm = parsed_time[2]
                    if parsed_time[3] == "PM":
                        hh += 12
                    spots.append((dt + pd.Timedelta(f"{hh}:{mm}:00"), ""))
            return spots
