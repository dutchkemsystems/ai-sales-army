from sqlalchemy import create_engine, Column, String, Float, Boolean, DateTime, Text, Integer, Date, JSON
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from datetime import datetime, date
from typing import Optional
from config import get_settings

settings = get_settings()

engine = create_async_engine(settings.DATABASE_URL, echo=True, future=True)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class LeadDB(Base):
    __tablename__ = "leads"

    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    company_name = Column(String, nullable=False)
    company_website = Column(String)
    company_industry = Column(String)
    company_size = Column(String)
    company_revenue = Column(Float, nullable=True)
    company_location = Column(String)
    lead_first_name = Column(String, nullable=False)
    lead_last_name = Column(String, nullable=False)
    lead_email = Column(String, nullable=False)
    lead_phone = Column(String, nullable=True)
    lead_linkedin_url = Column(String, nullable=True)
    lead_title = Column(String)
    lead_department = Column(String)
    lead_seniority = Column(String)
    status = Column(String, default="discovered")
    score = Column(String, default="unqualified")
    discovered_source = Column(String)
    discovered_at = Column(DateTime, default=datetime.now)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class ResearchProfileDB(Base):
    __tablename__ = "research_profiles"

    id = Column(String, primary_key=True)
    lead_id = Column(String, nullable=False, index=True)
    company_description = Column(Text)
    business_model = Column(Text)
    recent_news = Column(JSON, default=[])
    tech_stack = Column(JSON, default=[])
    pain_points = Column(JSON, default=[])
    competitors = Column(JSON, default=[])
    recent_activity = Column(JSON, default=[])
    key_achievements = Column(JSON, default=[])
    trigger_events = Column(JSON, default=[])
    research_summary = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class OutreachMessageDB(Base):
    __tablename__ = "outreach_messages"

    id = Column(String, primary_key=True)
    lead_id = Column(String, nullable=False, index=True)
    campaign_id = Column(String, index=True)
    channel = Column(String, nullable=False)
    subject = Column(String, nullable=True)
    body = Column(Text, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    opened_at = Column(DateTime, nullable=True)
    clicked_at = Column(DateTime, nullable=True)
    replied_at = Column(DateTime, nullable=True)
    is_bounced = Column(Boolean, default=False)
    is_spam = Column(Boolean, default=False)
    status = Column(String, default="queued")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class OutreachCampaignDB(Base):
    __tablename__ = "outreach_campaigns"

    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    target_leads = Column(JSON, default=[])
    channels = Column(JSON, default=[])
    message_sequence = Column(JSON, default=[])
    daily_limits = Column(JSON, default={})
    status = Column(String, default="draft")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class FollowUpScheduleDB(Base):
    __tablename__ = "follow_up_schedules"

    id = Column(String, primary_key=True)
    lead_id = Column(String, nullable=False, index=True)
    campaign_id = Column(String, index=True)
    scheduled_attempts = Column(Integer, default=4)
    successful_attempts = Column(Integer, default=0)
    last_attempt_at = Column(DateTime, nullable=True)
    next_attempt_at = Column(DateTime, nullable=True)
    follow_up_messages = Column(JSON, default=[])
    stop_after = Column(Integer, default=4)
    current_attempt = Column(Integer, default=0)
    status = Column(String, default="not_started")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class QualifiedLeadDB(Base):
    __tablename__ = "qualified_leads"

    id = Column(String, primary_key=True)
    lead_id = Column(String, nullable=False, index=True)
    qualification_date = Column(DateTime, default=datetime.now)
    budget_confirmed = Column(Boolean, default=False)
    authority_confirmed = Column(Boolean, default=False)
    need_confirmed = Column(Boolean, default=False)
    timeline_confirmed = Column(Boolean, default=False)
    bant_score = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class MeetingDB(Base):
    __tablename__ = "meetings"

    id = Column(String, primary_key=True)
    lead_id = Column(String, nullable=False, index=True)
    user_id = Column(String, nullable=False, index=True)
    lead_first_name = Column(String, nullable=False)
    lead_last_name = Column(String, nullable=False)
    lead_email = Column(String, nullable=False)
    meeting_title = Column(String, nullable=False)
    meeting_description = Column(Text)
    scheduled_start = Column(DateTime, nullable=False)
    scheduled_end = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, default=30)
    calendar_link = Column(String)
    invitee_link = Column(String)
    status = Column(String, default="pending")
    reminder_sent = Column(Boolean, default=False)
    meeting_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class UserDB(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    company_name = Column(String, nullable=True)
    subscription_tier = Column(String, default="starter")
    subscription_expires = Column(DateTime, nullable=True)
    settings = Column(JSON, default={})
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
