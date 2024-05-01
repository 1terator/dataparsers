import asyncio
from typing import List, Tuple, Dict

import requests
from requests import Response

from abstract import AbstractParseService
from services import WhatsappService
from tools import parsing_emails_from_website


class FiraBarcelonaParseService(AbstractParseService):
    ECatalogue_WEB_URL: str = "https://ecatalogue.firabarcelona.com"
    ECatalogue_SEARCH_API_URL: str = "https://ecatalogueusearch-api.firabarcelona.com/v1"
    ECatalogue_DETAIL_API_URL: str = "https://ecatalogue-api.firabarcelona.com/v1"

    LANGUAGE_DEFAULT_CODE: str = "en_EN"
    DEFAULT_COUNTRY_PHONE_CODE: str = "34"
    MAX_EXHIBITORS_PER_REQUEST: int = 1000

    def __init__(self, sap_code: str, catalog_id: int, catalog_name: str, whatsapp: WhatsappService):
        self.sap_code: str = sap_code
        self.catalog_id: int = catalog_id
        self.catalog_name: str = catalog_name
        self.whatsapp = whatsapp

    @staticmethod
    def __get_parsed_data_names() -> Tuple:
        return (
            "Name",
            "Country",
            "Whatsapp Link",
            "Contact Telephone",
            "Contact Email",
            "Contact Name",
            "Contact Post",
            "Emails",
            "Facebook url",
            "Company Website",
            "Detail link",
        )

    async def __get_country_name_by_id(self, country_id: int) -> str:
        country_name: str = "Undefined"
        url: str = self.ECatalogue_DETAIL_API_URL + f"/catalogues/{self.catalog_id}/countriesInUse"
        params: dict = {"language": self.LANGUAGE_DEFAULT_CODE}

        request: Response = await asyncio.to_thread(requests.get, url=url, params=params)
        countries: list = request.json()["_embedded"]["countries"] if request.status_code == 200 else []

        for country in countries:
            if country["id"] == country_id:
                country_name = country["name"]
                break

        return country_name

    def __format_phone_number(self, phone_number: str) -> str:
        if not phone_number:
            return phone_number

        # +(xxx or xx) xx xxx-xx-xx !!! min 11 chars
        phone_number: str = str(int("".join(ch for ch in phone_number if ch.isdigit())))

        return self.DEFAULT_COUNTRY_PHONE_CODE + phone_number if not 11 <= len(phone_number) else phone_number

    async def __format_exhibitors_data(self, exhibitors: List) -> List:
        return [
            [
                exhibitor["name"],
                await self.__get_country_name_by_id(exhibitor["countryId"]),
                [i for i in list(
                    {
                        await self.whatsapp.format_to_whatsapp_link(
                            self.__format_phone_number(exhibitor["contactTelephone"])
                        ),
                        await self.whatsapp.format_to_whatsapp_link(self.__format_phone_number(exhibitor["telephone"])),
                    }
                )if i],
                [i for i in list({exhibitor["contactTelephone"], exhibitor["telephone"]}) if i],
                [i for i in list({exhibitor["contactEmail"], exhibitor["email"]}) if i],
                exhibitor["contactName"],
                exhibitor["contactPost"],
                await parsing_emails_from_website(exhibitor["webSite"]),
                exhibitor["facebookUrl"],
                exhibitor["webSite"],
                self.ECatalogue_WEB_URL + f'/{self.catalog_name}/exhibitor/{exhibitor["id"]}/detail'
            ] for exhibitor in exhibitors
        ]

    async def __get_number_of_required_requests(self) -> int:
        url: str = self.ECatalogue_DETAIL_API_URL + f"/catalogues/{self.catalog_id}/countItems"
        params: dict = {"language": self.LANGUAGE_DEFAULT_CODE}

        request: Response = await asyncio.to_thread(requests.get, url=url, params=params)
        quantity: int = request.json()["EXHIBITORS"] if request.status_code == 200 else 0

        return quantity // self.MAX_EXHIBITORS_PER_REQUEST + (1 if quantity % self.MAX_EXHIBITORS_PER_REQUEST else 0)

    async def __parse_detail_exhibitor_information(self, exhibitor_id: int) -> List:
        url: str = self.ECatalogue_DETAIL_API_URL + f"/exhibitors/{exhibitor_id}"
        params: dict = {"projection": "detail", "language": self.LANGUAGE_DEFAULT_CODE}

        request: Response = await asyncio.to_thread(requests.get, url=url, params=params)
        return request.json() if request.status_code == 200 else []

    async def __parse_exhibitors_per_page(self, page: int) -> List:
        exhibitors: list = []
        url: str = self.ECatalogue_SEARCH_API_URL + "/us/unifiedSearch"
        js = {"sapCode": self.sap_code, "filter": "ONLY_EXHIBITORS"}
        params = {"page": page, "size": self.MAX_EXHIBITORS_PER_REQUEST, "language": self.LANGUAGE_DEFAULT_CODE}
        headers = {"Accept": "application/json, text/plain, */*"}

        request: Response = await asyncio.to_thread(requests.post, url=url, json=js, params=params, headers=headers)

        background_tasks: list = []
        for exhibitor_id in [_["entityId"] for _ in request.json()["list"]] if request.status_code == 200 else []:
            background_tasks.append(
                asyncio.create_task(self.__parse_detail_exhibitor_information(exhibitor_id=exhibitor_id))
            )

        for background_task in background_tasks:
            data: list = await background_task
            exhibitors.append(data),

        return exhibitors

    async def __parse_exhibitors(self) -> List:
        exhibitors: list = []
        background_tasks: list = []

        for _ in range(await self.__get_number_of_required_requests()):
            background_tasks.append(
                asyncio.create_task(self.__parse_exhibitors_per_page(page=_))
            )

        for background_task in background_tasks:
            data: list = await background_task
            exhibitors += *data,

        return await self.__format_exhibitors_data(exhibitors)

    async def parse(self) -> List:
        return await self.__parse_exhibitors()

    def get_parsed_data_names(self) -> Tuple:
        return self.__get_parsed_data_names()
