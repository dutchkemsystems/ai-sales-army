from typing import Dict, List, Optional
from config import get_settings
import httpx


settings = get_settings()


class LinkedInAPI:
    def __init__(self):
        self.access_token = settings.LINKEDIN_ACCESS_TOKEN
        self.base_url = "https://api.linkedin.com/v2"

    async def search_companies(self, query: str, limit: int = 25) -> List[Dict]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/companySearch",
                params={"q": query, "count": limit},
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            return response.json().get("elements", [])

    async def get_company_info(self, company_id: str) -> Dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/companies/{company_id}",
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            return response.json()

    async def search_people(self, query: str, company_id: Optional[str] = None, limit: int = 25) -> List[Dict]:
        params = {"q": "people", "keywords": query, "count": limit}
        if company_id:
            params["companyId"] = company_id
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/search",
                params=params,
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            return response.json().get("elements", [])

    async def send_connection_request(self, person_id: str, message: str) -> Dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/invitations",
                json={
                    "invitee": {"personId": person_id},
                    "message": message
                },
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            return response.json()

    async def send_message(self, recipient_id: str, message: str) -> Dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/messages",
                json={
                    "recipients": [recipient_id],
                    "message": message
                },
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            return response.json()
