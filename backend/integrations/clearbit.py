from typing import Dict, List, Optional
from config import get_settings
import httpx
from datetime import datetime, timedelta


settings = get_settings()


class ClearbitAPI:
    def __init__(self):
        self.api_key = settings.CLEARBIT_API_KEY
        self.base_url = "https://company.clearbit.com/v2"

    async def enrich_company(self, domain: str) -> Dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/companies/find",
                params={"domain": domain},
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            return response.json()

    async def enrich_person(self, email: str) -> Dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/people/find",
                params={"email": email},
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            return response.json()
