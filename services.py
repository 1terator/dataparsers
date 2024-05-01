import asyncio
import json
from typing import Optional

import requests
from requests import Response


I_PARAM: int = 0


class WhatsappService(object):
    Green_API_URL: str = "https://api.green-api.com/"

    def __init__(self, id_instance: int, api_token_instance: str):
        self.id_instance = id_instance
        self.api_token_instance = api_token_instance

    async def format_to_whatsapp_link(self, phone_number: str) -> Optional[str]:
        global I_PARAM
        I_PARAM += 1
        if not phone_number or not phone_number.isdigit():
            return None

        phone_number = str(int(phone_number))

        print(f"{I_PARAM}. Working with {phone_number}")

        url = self.Green_API_URL + f"waInstance{self.id_instance}/checkWhatsapp/{self.api_token_instance}"
        data = {"phoneNumber": phone_number}
        headers = {"Content-Type": "application/json"}

        r: Response = await asyncio.to_thread(requests.post, url=url, data=json.dumps(data), headers=headers)
        return f"https://wa.me/{phone_number}" if r.status_code == 200 and r.json()["existsWhatsapp"] else None
