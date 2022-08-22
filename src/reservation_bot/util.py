# -*- coding: utf-8 -*-
import re
from enum import Enum

from selenium import webdriver


def remove_nonalphabet(s: str):
    return re.sub("[^a-zA-Z\-]+", "", s)


class Platform(Enum):
    Resy = "resy"
    Tock = "tock"


def get_geckodriver_firefox(geckodriver_file: str):
    profile = webdriver.FirefoxProfile()
    ## profile.add_extension(extension="c:/users/weiwe/geckodriver/bypasspaywalls.xpi")
    driver = webdriver.Firefox(firefox_profile=profile, executable_path=geckodriver_file)
    return driver


def get_chrome_driver(chrome_driver_file: str):
    return webdriver.Chrome(executable_path=chrome_driver_file)
