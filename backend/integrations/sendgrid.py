from typing import Dict, List, Optional
from config import get_settings
import httpx


settings = get_settings()


class SendGridAPI:
    def __init__(self):
        self.api_key = settings.SENDGRID_API_KEY
        self.from_email = settings.SENDGRID_FROM_EMAIL
        self.base_url = "https://api.sendgrid.com/v3"

    async def send_email(self, to_email: str, subject: str, html_content: str, plain_content: str = None) -> Dict:
        payload = {
            "personalizations": [{"to": [{"email": to_email}]}],
            "from": {"email": self.from_email},
            "subject": subject,
            "content": [
                {"type": "text/plain", "value": plain_content or html_content},
                {"type": "text/html", "value": html_content}
            ]
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/mail/send",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            )
            return {"success": response.status_code in [200, 202], "status_code": response.status_code}

    async def get_email_stats(self, message_id: str) -> Dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/messages/{message_id}",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            return response.json()

    async def create_contact(self, email: str, first_name: str = None, last_name: str = None, custom_fields: Dict = None) -> Dict:
        payload = {
            "list_ids": [],
            "email": email,
            "first_name": first_name,
            "last_name": last_name
        }
        if custom_fields:
            payload["custom_fields"] = custom_fields
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self.base_url}/marketing/contacts",
                json={"contacts": [payload]},
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            )
            return response.json()
