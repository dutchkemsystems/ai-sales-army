from datetime import datetime, date
from typing import Optional, List, Dict
from pydantic import BaseModel, EmailStr
from enum import Enum


class LeadStatus(str, Enum):
    DISCOVERED = "discovered"
    RESEARCHED = "researched"
    PERSONALIZED = "personalized"
    OUTREACH_SENT = "outreach_sent"
    FOLLOWING_UP = "following_up"
    INTERESTED = "interested"
    MEETING_BOOKED = "meeting_booked"
    QUALIFIED = "qualified"
    LOST = "lost"
    CLOSED_WON = "closed_won"


class LeadScore(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNQUALIFIED = "unqualified"


class OutreachChannel(str, Enum):
    EMAIL = "email"
    LINKEDIN = "linkedin"
    TWITTER = "twitter"
    SMS = "sms"


class FollowUpStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    RESPONDED = "responded"
    BOOKED = "booked"
    STOPPED = "stopped"
    UNSUBSCRIBED = "unsubscribed"


class MeetingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    RESCHEDULED = "rescheduled"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


# ============================================
# CORE MODELS
# ============================================

class Lead(BaseModel):
    id: str
    company_name: str
    company_website: str
    company_industry: str
    company_size: str
    company_revenue: Optional[float] = None
    company_location: str
    lead_first_name: str
    lead_last_name: str
    lead_email: EmailStr
    lead_phone: Optional[str] = None
    lead_linkedin_url: Optional[str] = None
    lead_title: str
    lead_department: str
    lead_seniority: str
    status: LeadStatus = LeadStatus.DISCOVERED
    score: LeadScore = LeadScore.UNQUALIFIED
    discovered_source: str
    discovered_at: datetime = datetime.now()
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()


class ResearchProfile(BaseModel):
    id: str
    lead_id: str
    company_description: str
    business_model: str
    recent_news: List[Dict] = []
    tech_stack: List[str] = []
    pain_points: List[str] = []
    competitors: List[str] = []
    recent_activity: List[Dict] = []
    key_achievements: List[str] = []
    trigger_events: List[Dict] = []
    research_summary: str
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()


class PersonalizedMessage(BaseModel):
    id: str
    lead_id: str
    channel: OutreachChannel
    subject: Optional[str] = None
    body: str
    tone: str
    template_id: Optional[str] = None
    version: int = 1
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()


class OutreachCampaign(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    target_leads: List[str] = []
    channels: List[OutreachChannel] = []
    message_sequence: List[Dict] = []
    daily_limits: Dict = {}
    status: str = "draft"
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()


class OutreachMessage(BaseModel):
    id: str
    lead_id: str
    campaign_id: str
    channel: OutreachChannel
    subject: Optional[str] = None
    body: str
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None
    replied_at: Optional[datetime] = None
    is_bounced: bool = False
    is_spam: bool = False
    status: str = "queued"
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()


class FollowUpSchedule(BaseModel):
    id: str
    lead_id: str
    campaign_id: str
    scheduled_attempts: int = 4
    successful_attempts: int = 0
    last_attempt_at: Optional[datetime] = None
    next_attempt_at: Optional[datetime] = None
    follow_up_messages: List[Dict] = []
    stop_after: int = 4
    current_attempt: int = 0
    status: FollowUpStatus = FollowUpStatus.NOT_STARTED
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()


class QualifiedLead(BaseModel):
    id: str
    lead_id: str
    qualification_date: datetime = datetime.now()
    budget_confirmed: bool = False
    authority_confirmed: bool = False
    need_confirmed: bool = False
    timeline_confirmed: bool = False
    bant_score: float = 0.0
    notes: Optional[str] = None
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()


class Meeting(BaseModel):
    id: str
    lead_id: str
    lead_first_name: str
    lead_last_name: str
    lead_email: EmailStr
    meeting_title: str
    meeting_description: str
    scheduled_start: datetime
    scheduled_end: datetime
    duration_minutes: int = 30
    calendar_link: str
    invitee_link: str
    status: MeetingStatus = MeetingStatus.PENDING
    reminder_sent: bool = False
    meeting_notes: Optional[str] = None
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()


class PipelineAnalytics(BaseModel):
    id: str
    date: date
    total_leads: int = 0
    researched: int = 0
    personalized: int = 0
    outreach_sent: int = 0
    replied: int = 0
    interested: int = 0
    meetings_booked: int = 0
    meetings_completed: int = 0
    closed_won: int = 0
    conversion_rate: float = 0.0
    avg_time_to_book: float = 0.0
    revenue_forecast: float = 0.0


class AgentPerformance(BaseModel):
    agent_name: str
    leads_processed: int = 0
    success_count: int = 0
    fail_count: int = 0
    avg_time_per_lead: float = 0.0
    success_rate: float = 0.0
    last_run: Optional[datetime] = None


# ============================================
# USER MODELS
# ============================================

class User(BaseModel):
    id: str
    email: EmailStr
    password_hash: str
    first_name: str
    last_name: str
    company_name: Optional[str] = None
    subscription_tier: str = "starter"
    subscription_expires: Optional[datetime] = None
    settings: Dict = {}
    is_admin: bool = False
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()


# ============================================
# API REQUEST/RESPONSE MODELS
# ============================================

class DiscoverRequest(BaseModel):
    linkedin_query: Optional[str] = None
    apollo_query: Optional[str] = None
    twitter_query: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    location: Optional[str] = None
    keywords: Optional[List[str]] = None


class CampaignCreate(BaseModel):
    name: str
    description: Optional[str] = None
    target_leads: List[str] = []
    channels: List[OutreachChannel] = [OutreachChannel.EMAIL]
    daily_limits: Dict = {"email": 50, "linkedin": 25, "twitter": 50, "sms": 20}


class MeetingCreate(BaseModel):
    lead_id: str
    preferred_date: Optional[datetime] = None
    duration_minutes: int = 30
    notes: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    company_name: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
