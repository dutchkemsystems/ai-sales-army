import uuid
from typing import Dict, Optional
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_settings
from models import PersonalizedMessage, ResearchProfile, OutreachChannel

settings = get_settings()


class PersonalizerAgent:
    def __init__(self):
        self._llm = None
        self.templates = {
            "linkedin": {
                "formal": PromptTemplate.from_template(
                    "You are crafting a LinkedIn connection request for {first_name} {last_name}, "
                    "{title} at {company}.\n\n"
                    "Research: {news} | Pain points: {pain_points} | Tech: {tech_stack}\n\n"
                    "Write a professional connection request (150-200 chars) that references their "
                    "work and offers value. Output ONLY the message."
                ),
                "casual": PromptTemplate.from_template(
                    "Write a casual LinkedIn message to {first_name} {last_name} at {company}.\n"
                    "Reference: {news}\nOffer value based on: {pain_points}\nKeep under 200 chars."
                ),
            },
            "email": {
                "formal": PromptTemplate.from_template(
                    "Write a cold email to {first_name} {last_name}, {title} at {company}.\n\n"
                    "Research: {news}\nPain points: {pain_points}\nTech stack: {tech_stack}\n"
                    "Competitors: {competitors}\n\n"
                    "Write a compelling email (150-200 words) with personalized opening, "
                    "value proposition, and clear CTA.\n\nFormat:\nSUBJECT: <subject>\nBODY: <body>"
                ),
                "casual": PromptTemplate.from_template(
                    "Write a casual cold email to {first_name} {last_name} at {company}.\n"
                    "Reference: {news}\nOffer: {pain_points}\nKeep under 200 words.\n"
                    "Format:\nSUBJECT: <subject>\nBODY: <body>"
                ),
            },
        }

    async def personalize(
        self, lead: Dict, research: ResearchProfile, channel: OutreachChannel, tone: str = "formal"
    ) -> PersonalizedMessage:
        channel_key = channel.value if isinstance(channel, OutreachChannel) else str(channel)
        template = self.templates.get(channel_key, {}).get(tone, self.templates["email"]["formal"])

        format_vars = {
            "first_name": lead.get("lead_first_name", "Unknown"),
            "last_name": lead.get("lead_last_name", "Unknown"),
            "title": lead.get("lead_title", "Unknown"),
            "company": lead.get("company_name", "Unknown"),
            "news": str(research.recent_news[:3]) if research.recent_news else "No recent news",
            "pain_points": str(research.pain_points[:3]) if research.pain_points else "None identified",
            "tech_stack": str(research.tech_stack[:5]) if research.tech_stack else "Unknown",
            "competitors": str(research.competitors[:3]) if research.competitors else "Unknown",
        }

        try:
            prompt_text = template.format(**format_vars)
            response = await self._get_llm().ainvoke(prompt_text)
            body = response.content.strip() if hasattr(response, "content") else str(response)
        except Exception:
            body = f"Hi {format_vars['first_name']}, I'd love to connect about how we can help {format_vars['company']}."

        subject = None
        if channel_key == "email" and "SUBJECT:" in body:
            parts = body.split("BODY:", 1)
            subject = parts[0].replace("SUBJECT:", "").strip()[:50]
            body = parts[1].strip() if len(parts) > 1 else body
        elif channel_key == "email":
            subject = f"Quick question for {format_vars['first_name']}"

        return PersonalizedMessage(
            id=str(uuid.uuid4()),
            lead_id=lead.get("id", str(uuid.uuid4())),
            channel=channel_key,
            subject=subject,
            body=body,
            tone=tone,
        )

    def _get_llm(self):
        if self._llm is None:
            api_key = settings.NVIDIA_NIM_API_KEY or settings.OPENAI_API_KEY
            base_url = settings.NVIDIA_NIM_BASE_URL if settings.NVIDIA_NIM_API_KEY else None
            self._llm = ChatOpenAI(model="meta/llama-3.1-70b-instruct", temperature=0.7, api_key=api_key, base_url=base_url)
        return self._llm

    async def _generate_subject_line(self, lead: Dict, research: ResearchProfile) -> str:
        try:
            response = await self._get_llm().ainvoke(
                f"Generate ONE email subject line for {lead.get('lead_first_name', '')} "
                f"at {lead.get('company_name', '')}. Under 50 chars. Return ONLY the subject."
            )
            return response.content.strip()[:50]
        except Exception:
            return f"Quick question for {lead.get('lead_first_name', 'you')}"

    def _validate_message(self, message: str, channel: OutreachChannel) -> bool:
        spam_words = ["free trial", "act now", "limited time", "guarantee", "click here", "buy now"]
        msg_lower = message.lower()
        if any(w in msg_lower for w in spam_words):
            return False
        word_count = len(message.split())
        if channel == OutreachChannel.LINKEDIN and (word_count < 30 or word_count > 400):
            return False
        if channel == OutreachChannel.EMAIL and (word_count < 40 or word_count > 500):
            return False
        return True
