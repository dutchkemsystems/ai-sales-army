import uuid
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_settings
from models import FollowUpSchedule, FollowUpStatus, OutreachMessage, OutreachChannel

settings = get_settings()


class FollowUpAgent:
    def __init__(self):
        self._llm = None
        self.followup_prompt = PromptTemplate.from_template(
            "Generate a follow-up message for {first_name} {last_name} at {company}.\n"
            "Previous message: {previous_message}\nAttempt: {attempt_number} of {max_attempts}\n\n"
            "Write a concise follow-up that references previous communication, adds value, "
            "creates urgency, and includes a CTA. Keep under 150 words. Output ONLY the message."
        )

    async def schedule_followups(self, lead: Dict, initial_message: OutreachMessage) -> FollowUpSchedule:
        now = datetime.now()
        return FollowUpSchedule(
            id=str(uuid.uuid4()),
            lead_id=lead.get("id", str(uuid.uuid4())),
            campaign_id=initial_message.campaign_id,
            scheduled_attempts=4,
            successful_attempts=0,
            next_attempt_at=now + timedelta(days=2),
            follow_up_messages=[],
            stop_after=4,
            current_attempt=0,
            status=FollowUpStatus.IN_PROGRESS,
        )

    async def generate_followup(
        self, lead: Dict, previous_message: str, attempt_number: int, max_attempts: int,
        channel: OutreachChannel = OutreachChannel.EMAIL
    ) -> str:
        try:
            response = await self._get_llm().ainvoke(
                self.followup_prompt.format(
                    first_name=lead.get("lead_first_name", "there"),
                    last_name=lead.get("lead_last_name", ""),
                    company=lead.get("company_name", "your company"),
                    previous_message=previous_message or "Initial outreach",
                    attempt_number=attempt_number,
                    max_attempts=max_attempts,
                )
            )
            return response.content.strip() if hasattr(response, "content") else str(response)
        except Exception:
            return self._get_fallback(lead, attempt_number)

    async def process_followups(self, schedule: FollowUpSchedule) -> Dict:
        now = datetime.now()
        if schedule.next_attempt_at and now < schedule.next_attempt_at:
            return {"status": "waiting", "next_attempt": str(schedule.next_attempt_at)}

        if schedule.current_attempt >= schedule.stop_after:
            schedule.status = FollowUpStatus.STOPPED
            return {"status": "completed", "reason": "max_attempts_reached"}

        schedule.current_attempt += 1
        schedule.last_attempt_at = now
        schedule.next_attempt_at = now + timedelta(days=[2, 5, 10, 17][min(schedule.current_attempt, 3)])
        return {"status": "processed", "attempt": schedule.current_attempt}

    def _get_llm(self):
        if self._llm is None:
            api_key = settings.NVIDIA_NIM_API_KEY or settings.OPENAI_API_KEY
            base_url = settings.NVIDIA_NIM_BASE_URL if settings.NVIDIA_NIM_API_KEY else None
            self._llm = ChatOpenAI(model="meta/llama-3.1-70b-instruct", temperature=0.6, api_key=api_key, base_url=base_url)
        return self._llm

    async def should_stop_followup(self, schedule: FollowUpSchedule, reply_received: bool) -> bool:
        if reply_received:
            return True
        if schedule.status in (FollowUpStatus.RESPONDED, FollowUpStatus.STOPPED, FollowUpStatus.UNSUBSCRIBED):
            return True
        return schedule.current_attempt >= schedule.stop_after

    def _detect_interest(self, message: str) -> bool:
        if not message:
            return False
        signals = ["interested", "schedule", "demo", "meeting", "pricing", "yes", "sounds good"]
        msg_lower = message.lower()
        return any(s in msg_lower for s in signals)

    def _create_urgency(self, attempt: int, max_attempts: int) -> str:
        if attempt <= 1:
            return ""
        elif attempt == 2:
            return "Following up on my previous message."
        elif attempt == 3:
            return "Haven't heard back - would love to connect before this opportunity closes."
        return "Final follow-up. This will be our last outreach unless we hear from you."

    def _get_fallback(self, lead: Dict, attempt: int) -> str:
        name = lead.get("lead_first_name", "there")
        company = lead.get("company_name", "your team")
        if attempt == 1:
            return f"Hi {name}, following up on my previous message about helping {company}. Would you be open to a quick call?"
        elif attempt == 2:
            return f"Hi {name}, just circling back. I have some ideas that could benefit {company}. Can I share a brief case study?"
        return f"Hi {name}, this is my final follow-up. If you'd like to connect in the future, I'm here. Wishing {company} success."
