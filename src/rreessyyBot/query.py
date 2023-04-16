import json
import logging
from typing import List, Dict, Tuple

import pandas as pd
import requests
from requests import Response

from rreessyyBot.venue_slot import Venue, Slot, format_slot_in_html


def find_seat(
    api_key,
    auth_token,
    venues: List[Venue],
    dt: pd.Timestamp,
    party_size: int,
    start_time: pd.Timestamp,
    end_time: pd.Timestamp,
    venue_id_map: Dict[int, Venue],
) -> Tuple[str, bool]:
    venue_id_list = [venue.id for venue in venues]
    response = query_resy(dt, party_size, venue_id_list, api_key, auth_token)
    daily_slot = _parse_request_response(response, venue_id_map)

    ## restrict to [start_time, end_time]
    for venue, slot_list in daily_slot.items():
        daily_slot[venue] = [slot for slot in slot_list if start_time.time() <= slot.datetime.time() <= end_time.time()]
    seats_message = format_slot_in_html(dt, daily_slot)
    no_seat_flag = True
    for venue, slot_list in daily_slot.items():
        if len(slot_list) > 0:
            no_seat_flag = False
            break
    return seats_message, no_seat_flag


def query_resy(dt: pd.Timestamp, party_size: int, venue_id_list: List[int], api_key: str, auth_token: str) -> Response:
    """
    query_resy(pd.Timestamp("2023-04-01", 2, [1505, 6194], api_key, auth_token)
    :param dt:
    :param party_size:
    :param venue_id_list:
    :param api_key:
    :param auth_token:
    :return:
    """
    venue_id_query = ",".join([str(venue_id) for venue_id in venue_id_list])

    api_url = "https://api.resy.com"
    ## must have lat, location, long to send query
    api_path = rf"/4/find?day={dt.strftime('%Y-%m-%d')}&lat=42.744222&location=la&long=-95.982846&party_size={party_size}&venue_id={venue_id_query}&sort_by=available"
    api_key_header = f'ResyAPI api_key="{api_key}"'

    headers = {
        "Authorization": api_key_header,
        "x-resy-auth-token": auth_token,
        "x-resy-universal-auth": auth_token,
        "referer": r"https://resy.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
        "Accept": r"application/json, text/plain, */*",
        "Accept-Encoding": r"gzip, deflate, br",
    }
    response = requests.get(api_url + api_path, headers=headers)
    return response


def _parse_request_response(response: Response, venue_id_map: Dict[int, Venue]) -> Dict[Venue, List[Slot]]:
    """

    :param response:
    :return:
        dict,
        key: Venue
        value: Slot(time, size, type)
    """
    if response.status_code != 200:
        logging.error("bad response")
        return dict()
    response_json = json.loads(response.text)
    slot_by_venue = response_json["results"]["venues"]
    parsed_slot_by_venue = dict()

    for slot_per_venue in slot_by_venue:
        venue = venue_id_map[int(slot_per_venue["venue"]["id"]["resy"])]
        parsed_slot_by_venue[venue] = []
        for slot_json in slot_per_venue["slots"]:
            token_message = slot_json["config"]["token"]
            slot = _parse_single_slot(token_message)
            if slot:
                parsed_slot_by_venue[venue].append(slot)
    return parsed_slot_by_venue


def _parse_single_slot(single_slot_message: str) -> Slot:
    split_message = single_slot_message.split("/")
    if len(split_message) < 11:
        logging.error(f"failed to parse {single_slot_message}")
        return None
    else:
        return Slot(pd.Timestamp(f"{split_message[7]} {split_message[8]}"), int(split_message[9]), split_message[10])
