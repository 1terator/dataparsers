import asyncio
from typing import Tuple, List

import requests
from bs4 import BeautifulSoup
from requests import Response

from abstract import AbstractParseService
from services import WhatsappService
from tools import parsing_emails_from_website, parsing_phone_numbers_from_website, validate_phone_number, \
    recreate_phone_number


class EccmidParseService(AbstractParseService):
    Eccmid_URL: str = "https://www.eccmid.org/sponsorship-and-exhibition/sponsor-list"
    DEFAULT_COUNTRY_PHONE_CODE: str = "34"

    def __init__(self, whatsapp: WhatsappService):
        self.whatsapp = whatsapp

    @staticmethod
    def __get_parsed_data_names() -> Tuple:
        return "Title", "Website", "Emails", "Phones"

    async def __format_exhibitors_data(self, exhibitors: List) -> List:
        exhibitors = [
            exhibitor | {
                "emails": asyncio.create_task(parsing_emails_from_website(exhibitor["website"]))
            } for exhibitor in exhibitors
        ]
        exhibitors = [
            exhibitor | {
                "phone_numbers": asyncio.create_task(
                    parsing_phone_numbers_from_website(exhibitor["website"])
                )
            } for exhibitor in exhibitors
        ]
        return [
            [
                exhibitor["title"],
                exhibitor["website"],
                await exhibitor["emails"],
                [recreate_phone_number(phone_number) for phone_number in await exhibitor["phone_numbers"]],
            ] for exhibitor in exhibitors
        ]

    async def __parse_exhibitors(self) -> List:
        request: Response = await asyncio.to_thread(requests.get, url=self.Eccmid_URL)
        soup = BeautifulSoup(request.content, "lxml")
        expositor_websites = soup.find_all("a", class_="linksside")
        exhibitors: list = [{"title": data.text, "website": data["href"]} for data in expositor_websites]
        return await self.__format_exhibitors_data(exhibitors) if request.status_code == 200 else []

    async def parse(self) -> List:
        return await self.__parse_exhibitors()

    def get_parsed_data_names(self) -> Tuple:
        return self.__get_parsed_data_names()
