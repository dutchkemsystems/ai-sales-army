from typing import Dict, List
from config import get_settings
import httpx


settings = get_settings()


class TwitterAPI:
    def __init__(self):
        self.api_key = settings.TWITTER_API_KEY
        self.api_secret = settings.TWITTER_API_SECRET
        self.access_token = settings.TWITTER_ACCESS_TOKEN
        self.access_secret = settings.TWITTER_ACCESS_SECRET
        self.base_url = "https://api.twitter.com/2"

    async def search_prospects(self, query: str, limit: int = 25) -> List[Dict]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/tweets/search/recent",
                params={"query": query, "max_results": limit},
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            return response.json().get("data", [])

    async def get_user_info(self, username: str) -> Dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/users/by/username/{username}",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            return response.json().get("data", {})

    async def send_dm(self, recipient_id: str, message: str) -> Dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/dm_conversations/with/{recipient_id}/messages",
                json={"text": message},
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            return response.json()
