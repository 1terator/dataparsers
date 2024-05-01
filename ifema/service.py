import asyncio
from typing import Tuple, List, Dict

import requests
from requests import Response

from abstract import AbstractParseService
from services import WhatsappService
from tools import parsing_emails_from_website


class IFemaParseService(AbstractParseService):
    IFema_API_URL: str = "https://lc-events-web-public.ifema.es/api/v1"
    DEFAULT_COUNTRY_PHONE_CODE: str = "34"

    def __init__(self, tenant_id: str, edition_id: str, whatsapp: WhatsappService):
        self.tenant_id: str = tenant_id
        self.edition_id: str = edition_id
        self.whatsapp = whatsapp

    @staticmethod
    def __get_parsed_data_names() -> Tuple:
        return "Name", "Country", "Current Email", "Emails", "Website"

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
                "Emails": asyncio.create_task(parsing_emails_from_website(self.__format_website(exhibitor["link"])))
            } for exhibitor in exhibitors
        ]
        return [
            [
                exhibitor["name"],
                exhibitor["country"],
                exhibitor["email"],
                await exhibitor["Emails"],
                self.__format_website(exhibitor["link"]),
            ] for exhibitor in exhibitors
        ]

    async def __parse_detail_exhibitor(self, exhibitor_id: str) -> Dict:
        url: str = f"{self.IFema_API_URL}/tenants/{self.tenant_id}/editions/{self.edition_id}/exhibitors/{exhibitor_id}"
        request: Response = await asyncio.to_thread(requests.get, url=url)
        return {
            "name": request.json()["name"],
            "country": request.json()["location"]["countryCode"],
            "link": request.json()["link"],
        } if request.status_code == 200 else []

    async def __parse_exhibitors(self) -> List:
        url: str = self.IFema_API_URL + f"/tenants/{self.tenant_id}/editions/{self.edition_id}/exhibitors/search"
        data: dict = {"page": 0, "pageSize": 1000}

        request: Response = await asyncio.to_thread(requests.post, url=url, json=data)
        exhibitors: list = []
        for ls in request.json()["data"]:
            exh_det = await self.__parse_detail_exhibitor(ls["id"])
            exhibitors.append(exh_det | {"email": ls["email"]})
        return await self.__format_exhibitors_data(exhibitors) if request.status_code == 200 else []

    async def parse(self) -> List:
        return await self.__parse_exhibitors()

    def get_parsed_data_names(self) -> Tuple:
        return self.__get_parsed_data_names()
