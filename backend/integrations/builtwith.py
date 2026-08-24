from typing import Dict, List
from config import get_settings
import httpx


settings = get_settings()


class BuiltWithAPI:
    def __init__(self):
        self.api_key = settings.CLEARBIT_API_KEY  # Using same env var pattern
        self.base_url = "https://api.builtwith.com/free1/api.json"

    async def get_tech_stack(self, domain: str) -> List[str]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.base_url,
                params={"KEY": self.api_key, "LOOKUP": domain}
            )
            data = response.json()
            techs = []
            for category in data.get("results", []):
                for tech in category.get("matches", []):
                    techs.append(tech.get("name", ""))
            return techs

    async def get_company_technologies(self, domain: str) -> Dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.base_url,
                params={"KEY": self.api_key, "LOOKUP": domain}
            )
            return response.json()
