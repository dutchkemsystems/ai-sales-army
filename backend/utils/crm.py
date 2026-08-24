import uuid
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field


@dataclass
class CRMContact:
    id: str
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    company: str = ""
    title: str = ""
    industry: str = ""
    linkedin_url: Optional[str] = None
    lead_score: int = 0
    status: str = "new"
    owner_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    notes: List[Dict] = field(default_factory=list)
    activities: List[Dict] = field(default_factory=list)
    custom_fields: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class CRMDeal:
    id: str
    contact_id: str
    title: str
    value: float = 0.0
    stage: str = "qualification"
    probability: float = 0.0
    expected_close: Optional[datetime] = None
    owner_id: Optional[str] = None
    notes: List[Dict] = field(default_factory=list)
    activities: List[Dict] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class CRMActivity:
    id: str
    contact_id: str
    deal_id: Optional[str]
    type: str
    subject: str
    description: str = ""
    outcome: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)


class LocalCRM:
    def __init__(self):
        self.contacts: Dict[str, CRMContact] = {}
        self.deals: Dict[str, CRMDeal] = {}
        self.activities: Dict[str, CRMActivity] = {}

    def create_contact(self, **kwargs) -> CRMContact:
        contact_id = str(uuid.uuid4())
        contact = CRMContact(id=contact_id, **kwargs)
        self.contacts[contact_id] = contact
        return contact

    def get_contact(self, contact_id: str) -> Optional[CRMContact]:
        return self.contacts.get(contact_id)

    def update_contact(self, contact_id: str, **kwargs) -> Optional[CRMContact]:
        contact = self.contacts.get(contact_id)
        if not contact:
            return None
        for key, value in kwargs.items():
            if hasattr(contact, key):
                setattr(contact, key, value)
        contact.updated_at = datetime.now()
        return contact

    def search_contacts(self, query: str = "", status: str = None, owner_id: str = None) -> List[CRMContact]:
        results = list(self.contacts.values())
        if query:
            query_lower = query.lower()
            results = [c for c in results if
                      query_lower in c.first_name.lower() or
                      query_lower in c.last_name.lower() or
                      query_lower in c.email.lower() or
                      query_lower in c.company.lower()]
        if status:
            results = [c for c in results if c.status == status]
        if owner_id:
            results = [c for c in results if c.owner_id == owner_id]
        return results

    def add_note(self, contact_id: str, content: str, author: str = "system") -> bool:
        contact = self.contacts.get(contact_id)
        if not contact:
            return False
        contact.notes.append({
            "id": str(uuid.uuid4()),
            "content": content,
            "author": author,
            "created_at": datetime.now().isoformat(),
        })
        contact.updated_at = datetime.now()
        return True

    def log_activity(self, contact_id: str, activity_type: str, subject: str, description: str = "", deal_id: str = None) -> Optional[CRMActivity]:
        if contact_id not in self.contacts:
            return None
        activity_id = str(uuid.uuid4())
        activity = CRMActivity(
            id=activity_id,
            contact_id=contact_id,
            deal_id=deal_id,
            type=activity_type,
            subject=subject,
            description=description,
            completed_at=datetime.now(),
        )
        self.activities[activity_id] = activity
        self.contacts[contact_id].activities.append({
            "id": activity_id,
            "type": activity_type,
            "subject": subject,
            "timestamp": datetime.now().isoformat(),
        })
        self.contacts[contact_id].updated_at = datetime.now()
        return activity

    def create_deal(self, contact_id: str, title: str, value: float = 0, stage: str = "qualification", **kwargs) -> Optional[CRMDeal]:
        if contact_id not in self.contacts:
            return None
        deal_id = str(uuid.uuid4())
        deal = CRMDeal(id=deal_id, contact_id=contact_id, title=title, value=value, stage=stage, **kwargs)
        self.deals[deal_id] = deal
        return deal

    def get_deal(self, deal_id: str) -> Optional[CRMDeal]:
        return self.deals.get(deal_id)

    def update_deal(self, deal_id: str, **kwargs) -> Optional[CRMDeal]:
        deal = self.deals.get(deal_id)
        if not deal:
            return None
        for key, value in kwargs.items():
            if hasattr(deal, key):
                setattr(deal, key, value)
        deal.updated_at = datetime.now()
        return deal

    def get_pipeline(self, stage: str = None) -> List[CRMDeal]:
        deals = list(self.deals.values())
        if stage:
            deals = [d for d in deals if d.stage == stage]
        return sorted(deals, key=lambda d: d.updated_at, reverse=True)

    def get_pipeline_stats(self) -> Dict:
        stages = ["qualification", "proposal", "negotiation", "closed_won", "closed_lost"]
        stats = {}
        total_value = 0
        for stage in stages:
            stage_deals = [d for d in self.deals.values() if d.stage == stage]
            stage_value = sum(d.value for d in stage_deals)
            stats[stage] = {
                "count": len(stage_deals),
                "value": stage_value,
            }
            if stage not in ("closed_lost",):
                total_value += stage_value
        stats["total_value"] = total_value
        stats["total_contacts"] = len(self.contacts)
        stats["total_deals"] = len(self.deals)
        return stats

    def get_contact_timeline(self, contact_id: str) -> List[Dict]:
        contact = self.contacts.get(contact_id)
        if not contact:
            return []
        timeline = []
        for note in contact.notes:
            timeline.append({"type": "note", "content": note["content"], "author": note["author"], "timestamp": note["created_at"]})
        for activity in contact.activities:
            timeline.append({"type": "activity", "subject": activity["subject"], "activity_type": activity["type"], "timestamp": activity["timestamp"]})
        timeline.sort(key=lambda x: x["timestamp"], reverse=True)
        return timeline

    def delete_contact(self, contact_id: str) -> bool:
        if contact_id in self.contacts:
            del self.contacts[contact_id]
            return True
        return False

    def import_leads(self, leads: List[Dict]) -> int:
        imported = 0
        for lead in leads:
            email = lead.get("email", lead.get("lead_email", ""))
            if not email:
                continue
            existing = [c for c in self.contacts.values() if c.email == email]
            if existing:
                continue
            self.create_contact(
                first_name=lead.get("first_name", lead.get("lead_first_name", "Unknown")),
                last_name=lead.get("last_name", lead.get("lead_last_name", "Unknown")),
                email=email,
                phone=lead.get("phone", lead.get("lead_phone")),
                company=lead.get("company", lead.get("company_name", "")),
                title=lead.get("title", lead.get("lead_title", "")),
                industry=lead.get("industry", lead.get("company_industry", "")),
                linkedin_url=lead.get("linkedin_url", lead.get("lead_linkedin_url")),
                status="imported",
            )
            imported += 1
        return imported
