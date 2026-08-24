from typing import Dict, List
from config import get_settings
import httpx


settings = get_settings()


class ApolloAPI:
    def __init__(self):
        self.api_key = settings.APOLLO_API_KEY
        self.base_url = "https://api.apollo.io/v1"

    async def search_leads(self, query: str, industry: str = None, company_size: str = None, limit: int = 25) -> List[Dict]:
        payload = {
            "api_key": self.api_key,
            "q_keywords": query,
            "page": 1,
            "per_page": limit
        }
        if industry:
            payload["organization_industry_tag_ids"] = [industry]
        if company_size:
            payload["organization_num_employees_ranges"] = [company_size]

        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.base_url}/mixed_people/search", json=payload)
            return response.json().get("people", [])

    async def search_companies(self, query: str, limit: int = 25) -> List[Dict]:
        payload = {
            "api_key": self.api_key,
            "q_organization_name": query,
            "page": 1,
            "per_page": limit
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.base_url}/mixed_companies/search", json=payload)
            return response.json().get("organizations", [])

    async def get_company_info(self, domain: str) -> Dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/organizations/find_by_domain",
                params={"api_key": self.api_key, "domain": domain}
            )
            return response.json().get("organization", {})

    async def enrich_person(self, email: str) -> Dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/people/match",
                json={"api_key": self.api_key, "email": email}
            )
            return response.json().get("person", {})
