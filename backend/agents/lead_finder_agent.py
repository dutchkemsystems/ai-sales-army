import asyncio
import uuid
from typing import List, Dict, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_settings
from models import Lead, LeadScore, LeadStatus
from integrations.linkedin import LinkedInAPI
from integrations.apollo import ApolloAPI
from integrations.twitter import TwitterAPI
from integrations.clearbit import ClearbitAPI

settings = get_settings()


class LeadFinderAgent:
    def __init__(self):
        self._llm = None
        self.linkedin = LinkedInAPI()
        self.apollo = ApolloAPI()
        self.twitter = TwitterAPI()
        self.clearbit = ClearbitAPI()

    async def discover(self, filters: Dict) -> List[Lead]:
        search_tasks = []
        for source, query_filters in filters.items():
            query = query_filters if isinstance(query_filters, str) else str(query_filters)
            if source in ("linkedin", "apollo", "twitter"):
                search_tasks.append((source, query))

        if not search_tasks:
            search_tasks = [("linkedin", str(filters)), ("apollo", str(filters))]

        async def _run_search(source: str, query: str) -> List[Dict]:
            loop = asyncio.get_event_loop()
            if source == "linkedin":
                return await loop.run_in_executor(None, lambda: self._search_linkedin_sync(query))
            elif source == "apollo":
                return await loop.run_in_executor(None, lambda: self._search_apollo_sync(query))
            elif source == "twitter":
                return await loop.run_in_executor(None, lambda: self._search_twitter_sync(query))
            return []

        gathered = await asyncio.gather(
            *[_run_search(source, query) for source, query in search_tasks],
            return_exceptions=True,
        )

        all_leads: List[Dict] = []
        for result in gathered:
            if isinstance(result, list):
                all_leads.extend(result)

        unique_leads = self._deduplicate(all_leads)
        qualified_leads: List[Lead] = []
        for lead_data in unique_leads:
            score = self._calculate_score(lead_data)
            if score in (LeadScore.HIGH, LeadScore.MEDIUM):
                lead = self._create_lead(lead_data, score)
                qualified_leads.append(lead)

        return qualified_leads

    def _search_linkedin_sync(self, query: str) -> List[Dict]:
        try:
            import httpx
            response = httpx.get(
                f"https://api.linkedin.com/v2/search",
                params={"q": "people", "keywords": query},
                headers={"Authorization": f"Bearer {self.linkedin.access_token}"}
            )
            return response.json().get("elements", [])
        except Exception:
            return []

    def _search_apollo_sync(self, query: str) -> List[Dict]:
        try:
            import httpx
            response = httpx.post(
                "https://api.apollo.io/v1/mixed_people/search",
                json={"api_key": self.apollo.api_key, "q_keywords": query, "per_page": 25}
            )
            return response.json().get("people", [])
        except Exception:
            return []

    def _search_twitter_sync(self, query: str) -> List[Dict]:
        try:
            import httpx
            response = httpx.get(
                "https://api.twitter.com/2/tweets/search/recent",
                params={"query": query, "max_results": 25},
                headers={"Authorization": f"Bearer {self.twitter.api_key}"}
            )
            return response.json().get("data", [])
        except Exception:
            return []

    def _calculate_score(self, lead: Dict) -> LeadScore:
        points = 0
        company_size = str(lead.get("organization_num_employees_ranges", lead.get("company_size", ""))).lower()
        if any(x in company_size for x in ("1000+", "5000", "10000")):
            points += 3
        elif any(x in company_size for x in ("201", "501", "1000")):
            points += 2
        elif any(x in company_size for x in ("11", "51", "200")):
            points += 1

        title = str(lead.get("title", lead.get("lead_title", ""))).lower()
        if any(x in title for x in ("ceo", "cto", "vp", "director", "founder", "owner")):
            points += 4
        elif any(x in title for x in ("manager", "head", "lead")):
            points += 3
        elif any(x in title for x in ("senior", "principal")):
            points += 2

        if points >= 7:
            return LeadScore.HIGH
        elif points >= 4:
            return LeadScore.MEDIUM
        return LeadScore.LOW

    def _create_lead(self, lead_data: Dict, score: LeadScore) -> Lead:
        return Lead(
            id=str(uuid.uuid4()),
            company_name=lead_data.get("organization_name", lead_data.get("company_name", "Unknown")),
            company_website=lead_data.get("website", lead_data.get("company_website", "")),
            company_industry=lead_data.get("industry", lead_data.get("company_industry", "Unknown")),
            company_size=lead_data.get("organization_num_employees_ranges", lead_data.get("company_size", "Unknown")),
            company_location=lead_data.get("city", lead_data.get("company_location", "Unknown")),
            lead_first_name=lead_data.get("first_name", lead_data.get("lead_first_name", "Unknown")),
            lead_last_name=lead_data.get("last_name", lead_data.get("lead_last_name", "Unknown")),
            lead_email=lead_data.get("email", lead_data.get("lead_email", "")),
            lead_phone=lead_data.get("phone", lead_data.get("lead_phone")),
            lead_linkedin_url=lead_data.get("linkedin_url", lead_data.get("lead_linkedin_url")),
            lead_title=lead_data.get("title", lead_data.get("lead_title", "Unknown")),
            lead_department=lead_data.get("department", lead_data.get("lead_department", "Unknown")),
            lead_seniority=lead_data.get("seniority", lead_data.get("lead_seniority", "Unknown")),
            score=score,
            status=LeadStatus.DISCOVERED,
            discovered_source=lead_data.get("source", "apollo"),
        )

    def _get_llm(self):
        if self._llm is None:
            api_key = settings.NVIDIA_NIM_API_KEY or settings.OPENAI_API_KEY
            base_url = settings.NVIDIA_NIM_BASE_URL if settings.NVIDIA_NIM_API_KEY else None
            self._llm = ChatOpenAI(model="meta/llama-3.1-70b-instruct", temperature=0.1, api_key=api_key, base_url=base_url)
        return self._llm

    def _deduplicate(self, leads: List[Dict]) -> List[Dict]:
        seen_emails: set = set()
        unique: List[Dict] = []
        for lead in leads:
            email = str(lead.get("email", lead.get("lead_email", ""))).strip().lower()
            if not email or email in seen_emails:
                continue
            seen_emails.add(email)
            unique.append(lead)
        return unique
