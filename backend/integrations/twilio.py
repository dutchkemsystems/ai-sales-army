from typing import Dict, List
from config import get_settings
import httpx


settings = get_settings()


class TwilioAPI:
    def __init__(self):
        self.account_sid = settings.TWILIO_ACCOUNT_SID
        self.auth_token = settings.TWILIO_AUTH_TOKEN
        self.phone_number = settings.TWILIO_PHONE_NUMBER
        self.base_url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}"

    async def send_sms(self, to_number: str, body: str) -> Dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/Messages.json",
                data={
                    "To": to_number,
                    "From": self.phone_number,
                    "Body": body
                },
                auth=(self.account_sid, self.auth_token)
            )
            return {"success": response.status_code == 201, "data": response.json()}

    async def get_message_status(self, message_sid: str) -> Dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/Messages/{message_sid}.json",
                auth=(self.account_sid, self.auth_token)
            )
            return response.json()
