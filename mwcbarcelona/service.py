import asyncio
import json
from typing import List, Tuple, Dict

import requests
from bs4 import BeautifulSoup
from lxml import html
from requests import Response

from abstract import AbstractParseService
from services import WhatsappService
from tools import validate_phone_number, validate_email, parsing_emails_from_website


class MVCBarcelonaParseService(AbstractParseService):
    MVCBarcelona_URL: str = "https://www.mwcbarcelona.com/"
    ALGOLIA_API_URl: str = "https://8vvb6vr33k-dsn.algolia.net/"
    DEFAULT_COUNTRY_PHONE_CODE: str = "34"
    MAX_EXHIBITORS_PER_REQUEST: int = 1000

    def __init__(self, algolia_api_key: str, algolia_application_id: str, whatsapp: WhatsappService):
        self.algolia_api_key: str = algolia_api_key
        self.algolia_application_id: str = algolia_application_id
        self.whatsapp = whatsapp

    @staticmethod
    def __get_parsed_data_names() -> Tuple:
        return "Name", "Country", "Whatsapp link", "Telephone", "Current Email", "Website Emails", "Website", "Detail"

    def __format_phone_number(self, phone_number: str) -> str:
        if not phone_number:
            return phone_number

        # +(xxx or xx) xx xxx-xx-xx !!! min 11 chars
        phone_number: str = str(int("".join(ch for ch in phone_number if ch.isdigit())))

        return self.DEFAULT_COUNTRY_PHONE_CODE + phone_number if not 11 <= len(phone_number) else phone_number

    async def __parse_mvc_barcelona_html(self, url: str) -> Dict:
        parsed_data: dict = {"phone_number": None, "email": None, "website": None}
        if not url:
            return parsed_data
        url: str = self.MVCBarcelona_URL + url[1:]
        print(f"Parse Detail {url}")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        try:
            request: Response = await asyncio.to_thread(
                requests.get, url=url, headers=headers, allow_redirects=False, timeout=(3, 5)
            )
        except:
            return parsed_data
        tree = html.fromstring(request.content)
        hrefs: list = [href for href in tree.xpath('//*[@id="exhibitor-container"]/aside/div/ul/li/a')]
        for href in hrefs:
            try:
                if validate_phone_number(href.attrib["href"].split(":")[1]) and not parsed_data["phone_number"]:
                    parsed_data["phone_number"] = href.attrib["href"].split(":")[1]
                elif validate_email(href.attrib["href"].split(":")[1]) and not parsed_data["email"]:
                    parsed_data["email"] = href.attrib["href"].split(":")[1]
                else:
                    parsed_data["website"] = href.attrib['href']
            except:
                continue
        print(f"Stop Parse Detail {url} {request.status_code}")
        return parsed_data

    async def __format_exhibitors_data(self, exhibitors: List) -> List:
        exhibitors = [
            exhibitor | {
                "contactData":
                asyncio.create_task(
                    self.__parse_mvc_barcelona_html(exhibitor["url"])
                )
            }
            for exhibitor in exhibitors
        ]
        return [
            [
                exhibitor["name"],
                exhibitor["country"],
                await self.whatsapp.format_to_whatsapp_link(
                    self.__format_phone_number(
                        (await exhibitor["contactData"])["phone_number"]
                    )
                ),
                (await exhibitor["contactData"])["phone_number"],
                (await exhibitor["contactData"])["email"],
                await parsing_emails_from_website((await exhibitor["contactData"])["website"]),
                (await exhibitor["contactData"])["website"],
                self.MVCBarcelona_URL + exhibitor["url"][1:] if exhibitor["url"] else None,
            ] for exhibitor in exhibitors
        ]

    async def __get_number_of_required_requests(self) -> int:
        url: str = self.ALGOLIA_API_URl + "1/indexes/*/queries"
        params: dict = {
            "x-algolia-api-key": self.algolia_api_key,
            "x-algolia-application-id": self.algolia_application_id
        }
        request_data_params: str = f"hitsPerPage={self.MAX_EXHIBITORS_PER_REQUEST}"
        data: dict = {
            "requests": [{"indexName": "exhibitors-default", "params": request_data_params}]
        }

        request: Response = await asyncio.to_thread(requests.post, url=url, data=json.dumps(data), params=params)
        return request.json()["results"][0]["nbPages"] if request.status_code == 200 else 0

    async def __parse_exhibitors(self) -> List:
        exhibitors_list: list = []
        url: str = self.ALGOLIA_API_URl + "1/indexes/*/queries"
        params: dict = {
            "x-algolia-api-key": self.algolia_api_key,
            "x-algolia-application-id": self.algolia_application_id
        }

        for _ in range(1):
            print(f"Page {_ + 1}")
            request_data_params: str = f"hitsPerPage={self.MAX_EXHIBITORS_PER_REQUEST}&page={3}"
            data: dict = {
                "requests": [{"indexName": "exhibitors-default", "params": request_data_params}]
            }
            request: Response = await asyncio.to_thread(requests.post, url=url, data=json.dumps(data), params=params)
            exhibitors_list.extend(
                await self.__format_exhibitors_data(
                    request.json()["results"][0]["hits"]
                ) if request.status_code == 200 else []
            )

        return exhibitors_list

    async def parse(self) -> List:
        return await self.__parse_exhibitors()

    def get_parsed_data_names(self) -> Tuple:
        return self.__get_parsed_data_names()
