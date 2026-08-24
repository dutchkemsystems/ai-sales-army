from typing import Dict, List
from config import get_settings
import httpx


settings = get_settings()


class NewsAPI:
    def __init__(self):
        self.api_key = settings.CLEARBIT_API_KEY  # Placeholder - use newsapi.org key
        self.base_url = "https://newsapi.org/v2"

    async def get_company_news(self, company_name: str, limit: int = 10) -> List[Dict]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/everything",
                params={
                    "q": company_name,
                    "pageSize": limit,
                    "sortBy": "publishedAt",
                    "apiKey": self.api_key
                }
            )
            articles = response.json().get("articles", [])
            return [
                {
                    "title": a.get("title"),
                    "description": a.get("description"),
                    "url": a.get("url"),
                    "published_at": a.get("publishedAt")
                }
                for a in articles
            ]
