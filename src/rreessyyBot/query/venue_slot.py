from typing import Dict, List

import pandas as pd


class Venue:
    def __init__(self, id: int, webname: str, city: str):
        self.id = id
        self.webname = webname
        self.city = city

    def __str__(self):
        return f"{self.webname}, {self.id}"

    def __eq__(self, other):
        return self.id == other.id and self.webname == other.webname and self.city == other.city

    def __hash__(self):
        return hash((self.id, self.webname, self.city))


class SlotField:
    datetime = "datetime"
    date = "date"
    time = "time"
    party_size = "party_size"
    table_type = "table_type"


class Slot:
    def __init__(self, datetime: pd.Timestamp, party_size: int, table_type: str):
        self.datetime = datetime
        self.party_size = party_size
        self.table_type = table_type

    def __str__(self):
        return f"datetime={self.datetime}, partysize={self.party_size}, tabletype={self.table_type}"


def format_slot_in_html(dt: pd.Timestamp, all_slots: Dict[Venue, List[Slot]]) -> str:
    """
    example: format_slot_in_html(pd.Timestamp("2023-04-12"), {Venue(50746, "salinas", ): [Slot(pd.Timestamp("2023-04-12 18:30"), 2, "indoor")]})
    :param dt:
    :param all_slots:
    :return:
    """
    html_links = []
    for venue, slot_list in all_slots.items():
        if len(slot_list) > 0:
            html_link = f"<b>{venue.webname}</b>:\n" + " ".join(
                [
                    f'<a href="{get_link(venue, slot.party_size, slot.datetime)}">{slot.datetime.strftime("%I:%M%p")}_{slot.party_size}</a>'
                    for slot in slot_list
                ]
            )
            html_links.append(html_link)
    return f"~~~~~~~~<b>{dt.strftime('%m-%d %a')}</b>~~~~~~~~\n" + "\n\n".join(html_links)


def get_link(venue: Venue, party_size: int, datetime: pd.Timestamp) -> str:
    """

    :param venue:
    :param party_size:
    :param datetime:
    :return: https://resy.com/cities/jsc/hamilton-pork?date=2023-04-21&seats=2"
    """
    return (
        f"https://resy.com/cities/{venue.city}/{venue.webname}?date={datetime.strftime('%Y-%m-%d')}&seats={party_size}"
    )
