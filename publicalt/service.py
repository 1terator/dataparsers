import asyncio
from typing import List, Tuple

import requests
from requests import Response

from abstract import AbstractParseService
from services import WhatsappService


class PublicaltParseService(AbstractParseService):
    Publicalt_URL: str = "https://publicalt.xeria.es/"
    DEFAULT_COUNTRY_PHONE_CODE: str = "34"

    def __init__(self, catalog_name: str, whatsapp: WhatsappService):
        self.catalog_name: str = catalog_name
        self.whatsapp = whatsapp

    @staticmethod
    def __get_parsed_data_names() -> Tuple:
        return "Name", "Website", "Email", "Phone number", "Whatsapp Link", "Country", "Detail Link"

    def __format_phone_number(self, phone_number: str) -> str:
        if not phone_number:
            return phone_number

        # +(xxx or xx) xx xxx-xx-xx !!! min 11 chars
        phone_number: str = str(int("".join(ch for ch in phone_number if ch.isdigit())))

        return self.DEFAULT_COUNTRY_PHONE_CODE + phone_number if not 11 <= len(phone_number) else phone_number

    async def __format_exhibitors_data(self, exhibitors: List) -> List:
        return [
            [
                exhibitor["Name"],
                exhibitor["Web"],
                exhibitor["Email"],
                exhibitor["Telephone"],
                await self.whatsapp.format_to_whatsapp_link(self.__format_phone_number(exhibitor["Telephone"])),
                exhibitor["Country"],
                self.Publicalt_URL + f"{self.catalog_name}/es/company/Details/" + str(exhibitor["IdAccount"]),
            ] for exhibitor in exhibitors
        ]

    async def __parse_exhibitors(self) -> List:
        url: str = self.Publicalt_URL + f"{self.catalog_name}/es/Company/Companies_Read"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        request: Response = await asyncio.to_thread(requests.post, url=url, data="sort=Name-asc", headers=headers)
        return await self.__format_exhibitors_data(request.json()["Data"]) if request.status_code == 200 else []

    async def parse(self) -> List:
        return await self.__parse_exhibitors()

    def get_parsed_data_names(self) -> Tuple:
        return self.__get_parsed_data_names()
