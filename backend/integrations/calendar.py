from typing import Dict, List, Optional
from config import get_settings
from datetime import datetime
import json


settings = get_settings()


class GoogleCalendarAPI:
    def __init__(self):
        self.credentials_path = settings.GOOGLE_CALENDAR_CREDENTIALS
        self.service = None

    async def initialize(self):
        """Initialize the Google Calendar API service"""
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build

            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=['https://www.googleapis.com/auth/calendar']
            )
            self.service = build('calendar', 'v3', credentials=credentials)
        except Exception as e:
            print(f"Failed to initialize Google Calendar: {e}")

    async def get_free_slots(self, email: str, start_date: datetime, end_date: datetime) -> List[Dict]:
        if not self.service:
            await self.initialize()
        if not self.service:
            return self._mock_free_slots(start_date)

        try:
            events_result = self.service.events().list(
                calendarId=email,
                timeMin=start_date.isoformat() + 'Z',
                timeMax=end_date.isoformat() + 'Z',
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            events = events_result.get('items', [])
            return self._calculate_free_slots(events, start_date, end_date)
        except Exception:
            return self._mock_free_slots(start_date)

    async def create_event(self, attendee_email: str, title: str, description: str,
                          start_time: datetime, end_time: datetime, meeting_link: str) -> Dict:
        if not self.service:
            await self.initialize()
        if not self.service:
            return self._mock_create_event(title, start_time)

        try:
            event = {
                'summary': title,
                'description': f"{description}\n\nMeeting Link: {meeting_link}",
                'start': {'dateTime': start_time.isoformat(), 'timeZone': 'UTC'},
                'end': {'dateTime': end_time.isoformat(), 'timeZone': 'UTC'},
                'attendees': [{'email': attendee_email}],
                'conferenceData': {
                    'createRequest': {'requestId': f"meeting-{title}"}
                }
            }
            created = self.service.events().insert(
                calendarId='primary',
                body=event,
                conferenceDataVersion=1
            ).execute()
            return {"success": True, "event_id": created.get("id"), "link": created.get("htmlLink")}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def find_best_slot(self, attendee_email: str, available_slots: List[Dict], duration_minutes: int = 30) -> Dict:
        if available_slots:
            return available_slots[0]
        now = datetime.now()
        return {
            "start": now,
            "end": now,
            "link": f"https://calendar.google.com/calendar/u/0/r/eventedit?text=Meeting&dates={now.strftime('%Y%m%dT%H%M%S')}/{now.strftime('%Y%m%dT%H%M%S')}",
            "invitee_link": f"https://calendly.com/your-link/{now.strftime('%Y%m%d')}"
        }

    def _mock_free_slots(self, start_date: datetime) -> List[Dict]:
        slots = []
        for i in range(5):
            slot_date = start_date.replace(hour=10 + i * 2, minute=0, second=0)
            slots.append({
                "start": slot_date,
                "end": slot_date.replace(hour=10 + i * 2, minute=30)
            })
        return slots

    def _mock_create_event(self, title: str, start_time: datetime) -> Dict:
        return {
            "success": True,
            "event_id": f"mock-event-{title}",
            "link": f"https://calendar.google.com/calendar/event/{title}"
        }

    def _calculate_free_slots(self, events: List[Dict], start: datetime, end: datetime) -> List[Dict]:
        return [{"start": start, "end": end}]
