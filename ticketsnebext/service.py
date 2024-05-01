import asyncio
from typing import Tuple, List, Dict

import requests
from requests import Response

from abstract import AbstractParseService
from services import WhatsappService
from tools import parsing_emails_from_website


class TicketsNebextParseService(AbstractParseService):
    TicketsNebext_API_URL: str = "https://des.ticketsnebext.com"
    DEFAULT_COUNTRY_PHONE_CODE: str = "34"

    def __init__(self, catalog_name: str, whatsapp: WhatsappService):
        self.catalog_name: str = catalog_name
        self.whatsapp = whatsapp

    @staticmethod
    def __get_parsed_data_names() -> Tuple:
        return "Name", "Country", "Whatsapp Link", "Phone number", "Current Email", "Emails", "Website", "Detail Link"

    def __get_detail_exhibitor_web_link(self, exhibitor_id: int) -> str:
        return self.TicketsNebext_API_URL + f"/{self.catalog_name}/en/Company/Details/{exhibitor_id}"

    def __format_phone_number(self, phone_number: str) -> str:
        if not phone_number:
            return phone_number

        # +(xxx or xx) xx xxx-xx-xx !!! min 11 chars
        phone_number: str = str(int("".join(ch for ch in phone_number if ch.isdigit())))

        return self.DEFAULT_COUNTRY_PHONE_CODE + phone_number if not 11 <= len(phone_number) else phone_number

    @staticmethod
    def __format_website(url: str) -> str:
        if not isinstance(url, str):
            return url
        return url if url[:8] == "https://" or url[:7] == "http://" else "https://" + url

    async def __format_exhibitors_data(self, exhibitors: List) -> List:
        exhibitors = [
            exhibitor | {
                "Emails": asyncio.create_task(parsing_emails_from_website(self.__format_website(exhibitor["Web"])))
            } for exhibitor in exhibitors
        ]
        return [
            [
                exhibitor["Name"],
                exhibitor["Country"],
                await self.whatsapp.format_to_whatsapp_link(self.__format_phone_number(exhibitor["Telephone"])),
                exhibitor["Telephone"],
                exhibitor["Email"],
                await exhibitor["Emails"],
                self.__format_website(exhibitor["Web"]),
                self.__get_detail_exhibitor_web_link(exhibitor["IdAccount"]),
            ] for exhibitor in exhibitors
        ]

    async def __parse_exhibitors(self) -> List:
        url: str = self.TicketsNebext_API_URL + f"/{self.catalog_name}/en/Company/Companies_Read"
        data: dict = {"sort": "corder-asc~Name-asc"}

        request: Response = await asyncio.to_thread(requests.post, url=url, data=data)
        return await self.__format_exhibitors_data(request.json()["Data"]) if request.status_code == 200 else []

    async def parse(self) -> List:
        return await self.__parse_exhibitors()

    def get_parsed_data_names(self) -> Tuple:
        return self.__get_parsed_data_names()
