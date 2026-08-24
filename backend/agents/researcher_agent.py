import asyncio
import uuid
from typing import Dict, List
from langchain_openai import ChatOpenAI

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_settings
from models import ResearchProfile, Lead
from integrations.builtwith import BuiltWithAPI
from integrations.newsapi import NewsAPI
from integrations.crunchbase import CrunchbaseAPI
from integrations.clearbit import ClearbitAPI

settings = get_settings()


class ResearcherAgent:
    def __init__(self):
        self._llm = None
        self.builtwith = BuiltWithAPI()
        self.newsapi = NewsAPI()
        self.crunchbase = CrunchbaseAPI()
        self.clearbit = ClearbitAPI()

    async def research(self, lead: Lead) -> ResearchProfile:
        tech_stack, news, funding, pain_points = await asyncio.gather(
            self.get_tech_stack(lead.company_website or ""),
            self.get_company_news(lead.company_name),
            self.get_funding_info(lead.company_name),
            self.analyze_pain_points(lead),
        )

        summary_prompt = (
            f"You are a senior B2B sales researcher. Generate a concise, actionable "
            f"research summary for this lead.\n\n"
            f"Company: {lead.company_name}\n"
            f"Website: {lead.company_website}\n"
            f"Contact: {lead.lead_first_name} {lead.lead_last_name}, {lead.lead_title}\n"
            f"Industry: {lead.company_industry}\n"
            f"Tech Stack: {', '.join(tech_stack) if tech_stack else 'Unknown'}\n"
            f"Funding: {funding}\n"
            f"Pain Points: {', '.join(pain_points) if pain_points else 'None identified'}\n\n"
            f"Write a 3-5 sentence summary covering the company's position, likely "
            f"challenges, and the best approach to engage this lead."
        )

        try:
            summary_response = await self._get_llm().ainvoke(summary_prompt)
            summary = summary_response.content if hasattr(summary_response, "content") else str(summary_response)
        except Exception:
            summary = f"Research summary for {lead.company_name} - {lead.lead_title}"

        business_model = self._infer_business_model(tech_stack, news)
        competitors = self._find_competitors(lead)
        recent_activity = self._get_recent_activity(lead)
        achievements = self._extract_achievements(news)
        triggers = self._identify_triggers(news, funding)

        return ResearchProfile(
            id=str(uuid.uuid4()),
            lead_id=lead.id,
            company_description=f"{lead.company_name} operates in the {lead.company_industry} sector.",
            business_model=business_model,
            recent_news=news[:5] if news else [],
            tech_stack=tech_stack,
            pain_points=pain_points,
            competitors=competitors,
            recent_activity=recent_activity,
            key_achievements=achievements,
            trigger_events=triggers,
            research_summary=summary,
        )

    async def get_tech_stack(self, website: str) -> List[str]:
        if not website:
            return []
        try:
            result = await self.builtwith.get_tech_stack(website)
            return result if isinstance(result, list) else []
        except Exception:
            return []

    async def get_company_news(self, company_name: str) -> List[Dict]:
        if not company_name:
            return []
        try:
            result = await self.newsapi.get_company_news(company_name)
            return result if isinstance(result, list) else []
        except Exception:
            return []

    async def get_funding_info(self, company_name: str) -> Dict:
        if not company_name:
            return {}
        try:
            result = await self.crunchbase.get_funding_rounds(company_name)
            return result if isinstance(result, dict) else {}
        except Exception:
            return {}

    async def analyze_pain_points(self, lead: Lead) -> List[str]:
        prompt = (
            f"Identify 3-5 likely business pain points for {lead.lead_first_name} {lead.lead_last_name}, "
            f"{lead.lead_title} at {lead.company_name} ({lead.company_industry}). "
            f"Return ONLY a JSON array of strings."
        )
        try:
            response = await self._get_llm().ainvoke(prompt)
            content = response.content if hasattr(response, "content") else str(response)
            import json, re
            match = re.search(r"\[.*\]", content, re.DOTALL)
            if match:
                pain_points = json.loads(match.group())
                return [str(p) for p in pain_points] if isinstance(pain_points, list) else []
        except Exception:
            pass
        return []

    def _get_llm(self):
        if self._llm is None:
            api_key = settings.NVIDIA_NIM_API_KEY or settings.OPENAI_API_KEY
            base_url = settings.NVIDIA_NIM_BASE_URL if settings.NVIDIA_NIM_API_KEY else None
            self._llm = ChatOpenAI(model="meta/llama-3.1-70b-instruct", temperature=0.2, api_key=api_key, base_url=base_url)
        return self._llm

    def _infer_business_model(self, tech_stack: List[str], news: List[Dict]) -> str:
        tech_lower = [t.lower() for t in (tech_stack or [])]
        if any(x in tech_lower for x in ["shopify", "woocommerce", "magento"]):
            return "ecommerce"
        if any(x in tech_lower for x in ["stripe", "plaid", "square"]):
            return "fintech"
        if any(x in tech_lower for x in ["salesforce", "hubspot", "intercom"]):
            return "saas"
        return "unknown"

    def _find_competitors(self, lead: Lead) -> List[str]:
        industry = (lead.company_industry or "").lower()
        competitors_map = {
            "technology": ["Google", "Microsoft", "Amazon"],
            "saas": ["Salesforce", "HubSpot", "ServiceNow"],
            "fintech": ["Stripe", "Square", "PayPal"],
        }
        for keyword, names in competitors_map.items():
            if keyword in industry:
                return names[:3]
        return [f"Major player in {lead.company_industry}"]

    def _get_recent_activity(self, lead: Lead) -> List[Dict]:
        activities = []
        if lead.company_industry:
            activities.append({"type": "industry", "description": f"Operating in {lead.company_industry}"})
        if lead.company_website:
            activities.append({"type": "web", "description": f"Active at {lead.company_website}"})
        return activities

    def _extract_achievements(self, news: List[Dict]) -> List[str]:
        achievements = []
        keywords = ["award", "milestone", "growth", "launch", "leader"]
        for article in (news or [])[:10]:
            title = (article.get("title") or "").lower()
            if any(kw in title for kw in keywords):
                achievements.append(article.get("title", "Achievement noted"))
        return achievements[:5]

    def _identify_triggers(self, news: List[Dict], funding: Dict) -> List[Dict]:
        triggers = []
        if funding:
            if funding.get("total_funding"):
                triggers.append({"type": "funding", "description": f"Raised ${funding['total_funding']}", "urgency": "high"})
        trigger_keywords = {"hiring": "expansion", "acquisition": "strategic_shift", "partnership": "growth"}
        for article in (news or [])[:10]:
            title = (article.get("title") or "").lower()
            for keyword, trigger_type in trigger_keywords.items():
                if keyword in title:
                    triggers.append({"type": trigger_type, "description": article.get("title", ""), "urgency": "medium"})
                    break
        return triggers[:10]
