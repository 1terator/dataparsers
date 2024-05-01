import asyncio
import re
from typing import List, Optional

import requests
from bs4 import BeautifulSoup
from requests import Response, exceptions
from requests.exceptions import InvalidURL
from urllib3.exceptions import LocationParseError


async def parsing_emails_from_website(url: str) -> List:
    print(f"Parse Website email {url}")
    try:
        request: Response = await asyncio.to_thread(requests.get, url=url)
    except Exception as exc:
        print(exc)
        return []
    print(f"Stop Parse Website {url}")
    soup = BeautifulSoup(request.content, "lxml")
    email_pattern = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,4}")
    return list(set(re.findall(email_pattern, soup.get_text()))) if request.status_code == 200 else []


async def parsing_phone_numbers_from_website(url: str) -> List:
    print(f"Parse Website phone {url}")
    try:
        request: Response = await asyncio.to_thread(requests.get, url=url)
    except:
        return []
    print(f"Stop Parse Website {url}")
    soup = BeautifulSoup(request.content, "lxml")
    phone_pattern = re.compile(r"([+]\w{13,20})")
    return list(set(re.findall(phone_pattern, soup.get_text()))) if request.status_code == 200 else []


def recreate_phone_number(phone_number: str) -> Optional[str]:
    if not phone_number or not any(ch.isdigit() for ch in phone_number):
        return None
    new_phone = str(int("".join(ch for ch in phone_number if ch.isdigit())))
    return new_phone if validate_phone_number(new_phone) else None


def validate_phone_number(phone_number: str) -> bool:

    if not phone_number or not any(ch.isdigit() for ch in phone_number) or any(ch.isalpha() for ch in phone_number):
        return False
    phone_number: str = str(int("".join(ch for ch in phone_number if ch.isdigit())))
    pattern = re.compile(r"(\+\d{1,3})?\s?\(?\d{1,4}\)?[\s.-]?\d{3}[\s.-]?\d{4}")
    return True if re.search(pattern, phone_number) and len(phone_number) <= 13 else False


def validate_email(email: str) -> bool:
    if not email:
        return False

    pattern = re.compile(r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4})")
    return True if re.search(pattern, email) else False
