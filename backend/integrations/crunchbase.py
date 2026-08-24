from typing import Dict, List
from config import get_settings
import httpx


settings = get_settings()


class CrunchbaseAPI:
    def __init__(self):
        self.api_key = settings.CLEARBIT_API_KEY  # Placeholder
        self.base_url = "https://api.crunchbase.com/api/v4"

    async def get_company_info(self, company_name: str) -> Dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/organizations/{company_name}",
                headers={"X-cb-user-key": self.api_key}
            )
            return response.json()

    async def get_funding_rounds(self, company_name: str) -> List[Dict]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/organizations/{company_name}/funding_rounds",
                headers={"X-cb-user-key": self.api_key}
            )
            return response.json().get("items", [])

    async def get_investors(self, company_name: str) -> List[Dict]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/organizations/{company_name}/investors",
                headers={"X-cb-user-key": self.api_key}
            )
            return response.json().get("items", [])
