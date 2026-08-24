import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import OutreachMessage, OutreachChannel, PersonalizedMessage
from integrations.sendgrid import SendGridAPI
from integrations.linkedin import LinkedInAPI
from integrations.twilio import TwilioAPI
from integrations.twitter import TwitterAPI


class OutreachAgent:
    def __init__(self):
        self.sendgrid = SendGridAPI()
        self.linkedin = LinkedInAPI()
        self.twilio = TwilioAPI()
        self.twitter = TwitterAPI()
        self.daily_counts: Dict[str, int] = {}
        self.limits = {"email": 50, "linkedin": 25, "twitter": 50, "sms": 20}

    async def send_outreach(self, message: PersonalizedMessage, campaign_id: str) -> OutreachMessage:
        if not self._check_rate_limit(message.channel):
            return OutreachMessage(
                id=str(__import__('uuid').uuid4()),
                lead_id=message.lead_id,
                campaign_id=campaign_id,
                channel=message.channel,
                subject=message.subject,
                body=message.body,
                status="rate_limited",
            )

        channel = message.channel if isinstance(message.channel, OutreachChannel) else OutreachChannel(message.channel)
        handlers = {
            OutreachChannel.EMAIL: self._send_email,
            OutreachChannel.LINKEDIN: self._send_linkedin,
            OutreachChannel.SMS: self._send_sms,
            OutreachChannel.TWITTER: self._send_twitter,
        }

        handler = handlers.get(channel, self._send_email)
        result = await handler(message.lead_id, message.subject or "", message.body)
        self._increment_count(message.channel)

        return OutreachMessage(
            id=str(__import__('uuid').uuid4()),
            lead_id=message.lead_id,
            campaign_id=campaign_id,
            channel=message.channel,
            subject=message.subject,
            body=message.body,
            sent_at=datetime.now() if result.get("success") else None,
            status="sent" if result.get("success") else "failed",
        )

    async def _send_email(self, recipient: str, subject: str, body: str) -> Dict:
        try:
            return await self.sendgrid.send_email(recipient, subject, body)
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _send_linkedin(self, recipient: str, subject: str, body: str) -> Dict:
        try:
            return await self.linkedin.send_message(recipient, body)
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _send_sms(self, recipient: str, subject: str, body: str) -> Dict:
        try:
            return await self.twilio.send_sms(recipient, body)
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _send_twitter(self, recipient: str, subject: str, body: str) -> Dict:
        try:
            return await self.twitter.send_dm(recipient, body)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _check_rate_limit(self, channel) -> bool:
        ch = channel.value if isinstance(channel, OutreachChannel) else str(channel)
        count = self.daily_counts.get(ch, 0)
        return count < self.limits.get(ch, 50)

    def _increment_count(self, channel) -> None:
        ch = channel.value if isinstance(channel, OutreachChannel) else str(channel)
        self.daily_counts[ch] = self.daily_counts.get(ch, 0) + 1

    async def send_batch(self, messages: List[PersonalizedMessage], campaign_id: str) -> List[OutreachMessage]:
        semaphore = asyncio.Semaphore(5)
        async def _send_one(msg):
            async with semaphore:
                return await self.send_outreach(msg, campaign_id)
        return await asyncio.gather(*[_send_one(m) for m in messages])
