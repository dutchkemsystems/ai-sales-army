import uuid
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_settings
from models import QualifiedLead, Meeting, MeetingStatus
from integrations.calendar import GoogleCalendarAPI

settings = get_settings()


class AppointmentSetterAgent:
    def __init__(self):
        self._llm = None
        self.calendar = GoogleCalendarAPI()
        self.bant_prompt = PromptTemplate.from_template(
            "Score this lead using BANT criteria (0-25 each).\n"
            "Lead: {first_name} {last_name}, {title} at {company}\n"
            "Research: {research_summary}\n\n"
            "Return: BUDGET: <score> AUTHORITY: <score> NEED: <score> TIMELINE: <score>"
        )

    async def qualify_lead(self, lead: Dict, conversation_history: str = "") -> QualifiedLead:
        try:
            response = await self._get_llm().ainvoke(
                self.bant_prompt.format(
                    first_name=lead.get("lead_first_name", "Unknown"),
                    last_name=lead.get("lead_last_name", "Unknown"),
                    title=lead.get("lead_title", "Unknown"),
                    company=lead.get("company_name", "Unknown"),
                    research_summary=conversation_history or "No prior conversation",
                )
            )
            text = response.content if hasattr(response, "content") else str(response)
            scores = self._parse_bant_scores(text)
        except Exception:
            scores = {"budget": 10, "authority": 10, "need": 10, "timeline": 10}

        total = sum(scores.values())
        return QualifiedLead(
            id=str(uuid.uuid4()),
            lead_id=lead.get("id", str(uuid.uuid4())),
            qualification_date=datetime.now(),
            budget_confirmed=scores["budget"] > 15,
            authority_confirmed=scores["authority"] > 15,
            need_confirmed=scores["need"] > 15,
            timeline_confirmed=scores["timeline"] > 15,
            bant_score=total,
            notes=f"BANT: {scores}",
        )

    async def book_meeting(
        self, lead: Dict, qualified_lead: QualifiedLead, available_slots: List[Dict] = None
    ) -> Meeting:
        now = datetime.now()
        start = now + timedelta(days=1, hours=10)
        end = start + timedelta(minutes=30)

        if available_slots:
            slot = available_slots[0]
            start = datetime.fromisoformat(slot.get("start", start.isoformat()))
            end = datetime.fromisoformat(slot.get("end", end.isoformat()))

        return Meeting(
            id=str(uuid.uuid4()),
            lead_id=lead.get("id", str(uuid.uuid4())),
            lead_first_name=lead.get("lead_first_name", "Unknown"),
            lead_last_name=lead.get("lead_last_name", "Unknown"),
            lead_email=lead.get("lead_email", ""),
            meeting_title=f"Discovery Call - {lead.get('company_name', 'Unknown')}",
            meeting_description=f"Meeting with {lead.get('lead_first_name', '')} {lead.get('lead_last_name', '')}. "
                                 f"BANT Score: {qualified_lead.bant_score}/100",
            scheduled_start=start,
            scheduled_end=end,
            duration_minutes=30,
            calendar_link=f"https://calendar.google.com/calendar/event/{uuid.uuid4().hex[:10]}",
            invitee_link=f"https://calendly.com/your-link/{start.strftime('%Y%m%d')}",
            status=MeetingStatus.PENDING,
        )

    async def send_reminder(self, meeting: Meeting) -> bool:
        return True

    async def get_upcoming_meetings(self, user_id: str) -> List[Meeting]:
        return []

    def _parse_bant_scores(self, response: str) -> Dict:
        scores = {"budget": 10, "authority": 10, "need": 10, "timeline": 10}
        for line in response.strip().split("\n"):
            line = line.strip().upper()
            if "BUDGET:" in line:
                scores["budget"] = self._extract_score(line)
            elif "AUTHORITY:" in line:
                scores["authority"] = self._extract_score(line)
            elif "NEED:" in line:
                scores["need"] = self._extract_score(line)
            elif "TIMELINE:" in line:
                scores["timeline"] = self._extract_score(line)
        return scores

    def _extract_score(self, line: str) -> int:
        try:
            parts = line.split(":", 1)
            return max(0, min(int(parts[1].strip().split()[0]), 25))
        except (ValueError, IndexError):
            return 10

    def _get_llm(self):
        if self._llm is None:
            api_key = settings.NVIDIA_NIM_API_KEY or settings.OPENAI_API_KEY
            base_url = settings.NVIDIA_NIM_BASE_URL if settings.NVIDIA_NIM_API_KEY else None
            self._llm = ChatOpenAI(model="meta/llama-3.1-70b-instruct", temperature=0.3, api_key=api_key, base_url=base_url)
        return self._llm

    def _generate_meeting_title(self, lead: Dict) -> str:
        return f"Discovery Call - {lead.get('company_name', 'Unknown')}"
