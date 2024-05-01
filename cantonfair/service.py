import asyncio
from typing import Tuple, List, Dict

import requests
from bs4 import BeautifulSoup
from requests import Response

from abstract import AbstractParseService
from services import WhatsappService
from tools import parsing_emails_from_website, parsing_phone_numbers_from_website, recreate_phone_number


class CantonfairParseService(AbstractParseService):
    Cantonfair_API_URL: str = "https://www.cantonfair.org.cn"
    DEFAULT_COUNTRY_PHONE_CODE: str = "86"
    SIZE_PER_REQUEST: int = 200

    def __init__(self, auth: str, whatsapp: WhatsappService):
        self.auth = auth
        self.whatsapp = whatsapp

    @staticmethod
    def __get_parsed_data_names() -> Tuple:
        return "Name", "Status", "Country", "Country Code", "Company Person", "Email", "Phone Numbers", \
            "Whatsapp Links", "Fax", "Zip Code", "Website", "Detail Link", "Company Type", "Business Type", \
            "Product Type", "Address"

    async def __format_exhibitors_data(self, exhibitors: List) -> List:
        return [
            [
                exhibitor["name"],
                exhibitor["status"],
                exhibitor["country"],
                exhibitor["countryCode"],
                exhibitor["companyPerson"],
                exhibitor["email"],
                [phone for phone in {exhibitor["phoneNumber"], exhibitor["telephone"]} if phone],
                [
                    await self.whatsapp.format_to_whatsapp_link(
                        self.DEFAULT_COUNTRY_PHONE_CODE + phone if phone and len(phone) == 11 else phone
                    )
                    for phone in {exhibitor["phoneNumber"], exhibitor["telephone"]} if phone
                ],
                exhibitor["fax"],
                exhibitor["zipCode"],
                exhibitor["website"],
                exhibitor["detailLink"],
                exhibitor["companyType"],
                exhibitor["businessType"],
                exhibitor["productType"],
                exhibitor["address"],
            ] for exhibitor in exhibitors
        ]

    async def __parse_detail_exhibitor(self, code: str) -> Dict:
        url: str = self.Cantonfair_API_URL + "/b2bshop/api/themeRos/public/shopExt/searchByVariables"
        headers = {"X-User-Lan": "en-US"}
        params = {"shopCode": code, "lang": "en-US"}
        cookies = {"_authI": self.auth}

        print(f"Start to parse {code}")

        request: Response = await asyncio.to_thread(
            requests.get, url=url, params=params, cookies=cookies, headers=headers
        )

        exhibitor: Dict = request.json()["arrayData"]["0"]
        print(exhibitor["udfs"]["email"], exhibitor["udfs"]["mobilePhone"], exhibitor["udfs"]["telephone"])
        print(f"https://www.cantonfair.org.cn/en-US/shops/{code}")
        return {
            "name": exhibitor["name"],
            "country": exhibitor["address"]["country"]["name"] if exhibitor["address"]["country"] else None,
            "countryCode": exhibitor["address"]["country"]["code"] if exhibitor["address"]["country"] else None,
            "email": exhibitor["udfs"]["email"],
            "phoneNumber": recreate_phone_number(exhibitor["udfs"]["mobilePhone"]),
            "telephone": recreate_phone_number(exhibitor["udfs"]["telephone"]),
            "companyPerson": exhibitor["udfs"]["contactPerson"],
            "fax": exhibitor["udfs"]["fax"],
            "website": exhibitor["udfs"]["website"],
            "subsite": exhibitor["subsite"],
            "detailLink": f"https://www.cantonfair.org.cn/en-US/shops/{code}",
            "companyType": exhibitor["udfs"]["typeOfCompany"],
            "businessType": exhibitor["businessType"],
            "productType": exhibitor["udfs"]["mainProducts"],
            "address": exhibitor["address"]["fullAddress"] if "fullAddress" in exhibitor["address"] else None,
            "status": exhibitor["status"],
            "zipCode": exhibitor["udfs"]["zipCode"],
        }

    async def __parse_exhibitors(self) -> List:
        exhibitors: list = []
        url: str = self.Cantonfair_API_URL + "/b2bshop/api/themeRos/public/productShops/searchByVariables"
        params = {
            "productSearchable": False, "size": self.SIZE_PER_REQUEST, "scoreStrategy": "shop"
        }

        request: Response = await asyncio.to_thread(requests.get, url=url, params=params)
        codes: List = [company["code"] for company in request.json()["arrayData"]["0"]["_embedded"]["b2b:shops"]]
        count = request.json()["arrayData"]["0"]["page"]["totalPages"]
        elements = request.json()["arrayData"]["0"]["page"]["totalElements"]

        print(f"Pages: {count} Elements: {elements}")

        for _ in range(1, count):
            print(f"Parse {_} page in {count}")
            request: Response = await asyncio.to_thread(requests.get, url=url, params=params | {"page": _})
            codes.extend([company["code"] for company in request.json()["arrayData"]["0"]["_embedded"]["b2b:shops"]])

        background_tasks: list = [asyncio.create_task(self.__parse_detail_exhibitor(code)) for code in codes]
        for background_task in background_tasks:
            data: list = await background_task
            exhibitors.append(data),

        return await self.__format_exhibitors_data(exhibitors)

    async def parse(self) -> List:
        return await self.__parse_exhibitors()

    def get_parsed_data_names(self) -> Tuple:
        return self.__get_parsed_data_names()
