# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod
from typing import Tuple, List

import pandas as pd
from selenium.webdriver.remote.webdriver import WebDriver


class PlatformParser(ABC):
    def compose_message_found(
        self, meal_times: List[Tuple[pd.Timestamp, str]], restaurant: str, dt: pd.Timestamp, party_size: int
    ):
        try:
            link = self._compose_link(restaurant, dt, party_size)
            message = (
                f"{restaurant}: found seat for {party_size} on {dt.strftime('%Y-%m-%d')}, "
                f"{pd.Timestamp(meal_times[0][0]).strftime('%H:%M')}, {meal_times[0][1]}...{link}"
            )
        except Exception as E:
            message = f"found seat on {dt.strftime('%Y-%m-%d')}"
        return message

    def extract_available_spots_from_page(
        self, restaurant: str, dt: pd.Timestamp, party_size: int, driver: WebDriver
    ) -> Tuple[List[Tuple[pd.Timestamp, str]], str]:
        link = self._compose_link(restaurant, dt, party_size)
        content = self._extract_relevant_content_from_page(driver, link)
        spots = self._parse_spot_time_string(dt, content)
        return spots, content

    @abstractmethod
    def _compose_link(self, restaurant: str, dt: pd.Timestamp, party_size: int) -> str:
        """

        :param restaurant:  name of restaurant as on website
        :param dt: date
        :param party_size: size
        :return:
        """
        pass

    @abstractmethod
    def _extract_relevant_content_from_page(self, driver: WebDriver, link: str) -> str:
        """

        :param driver:
        :param link:
        :return: extract webpage text that has availability
        """
        pass

    @abstractmethod
    def _parse_spot_time_string(self, dt: pd.Timestamp, spot_content_string: str) -> List[Tuple[pd.Timestamp, str]]:
        """

        :param dt:
        :param spot_content_string:
        :return:  list of spots
        """
        pass
