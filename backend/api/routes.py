from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uuid
import asyncio

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_settings
from models import (
    Lead, LeadStatus, LeadScore, DiscoverRequest, CampaignCreate,
    MeetingCreate, LoginRequest, RegisterRequest, TokenResponse,
    OutreachChannel, ResearchProfile, PersonalizedMessage
)
from database.db import get_db, init_db, UserDB, LeadDB, MeetingDB, OutreachCampaignDB
from orchestrator.orchestrator import OrchestratorAgent
from sqlalchemy.ext.asyncio import AsyncSession

app = FastAPI(title="AI Sales Army API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

settings = get_settings()
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"])
orchestrator = OrchestratorAgent()


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    try:
        payload = jwt.decode(credentials.credentials, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"id": user_id, "email": payload.get("email")}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


@app.on_event("startup")
async def startup():
    await init_db()


@app.post("/api/auth/register", response_model=TokenResponse)
async def register(req: RegisterRequest):
    user_id = str(uuid.uuid4())
    password_hash = pwd_context.hash(req.password)
    token = create_access_token({"sub": user_id, "email": req.email})
    return TokenResponse(access_token=token, user_id=user_id, email=req.email)


@app.post("/api/auth/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    token = create_access_token({"sub": str(uuid.uuid4()), "email": req.email})
    return TokenResponse(access_token=token, user_id=str(uuid.uuid4()), email=req.email)


@app.get("/api/leads")
async def list_leads(
    status: Optional[LeadStatus] = None,
    score: Optional[LeadScore] = None,
    limit: int = 100,
    user: dict = Depends(get_current_user)
):
    leads = [l for l in orchestrator.pipeline if not status or l.status == status]
    if score:
        leads = [l for l in leads if l.score == score]
    return {"leads": [l.dict() for l in leads[:limit]], "total": len(leads)}


@app.post("/api/leads/discover")
async def discover_leads(
    filters: DiscoverRequest,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user)
):
    search_filters = {}
    if filters.linkedin_query:
        search_filters["linkedin"] = filters.linkedin_query
    if filters.apollo_query:
        search_filters["apollo"] = filters.apollo_query
    if filters.twitter_query:
        search_filters["twitter"] = filters.twitter_query
    if filters.industry:
        search_filters["industry"] = filters.industry
    if filters.company_size:
        search_filters["company_size"] = filters.company_size
    if filters.location:
        search_filters["location"] = filters.location

    background_tasks.add_task(
        orchestrator.run_full_pipeline,
        search_filters,
        user["id"]
    )
    return {"message": "Lead discovery started", "status": "processing"}


@app.get("/api/leads/{lead_id}")
async def get_lead(lead_id: str, user: dict = Depends(get_current_user)):
    for lead in orchestrator.pipeline:
        if lead.id == lead_id:
            return lead.dict()
    raise HTTPException(status_code=404, detail="Lead not found")


@app.put("/api/leads/{lead_id}/status")
async def update_lead_status(
    lead_id: str,
    status: LeadStatus,
    user: dict = Depends(get_current_user)
):
    for lead in orchestrator.pipeline:
        if lead.id == lead_id:
            lead.status = status
            return {"message": "Status updated", "lead": lead.dict()}
    raise HTTPException(status_code=404, detail="Lead not found")


@app.post("/api/leads/{lead_id}/research")
async def research_lead(lead_id: str, user: dict = Depends(get_current_user)):
    for lead in orchestrator.pipeline:
        if lead.id == lead_id:
            research = await orchestrator.researcher.research(lead)
            return research.dict()
    raise HTTPException(status_code=404, detail="Lead not found")


@app.post("/api/leads/{lead_id}/personalize")
async def personalize_lead(
    lead_id: str,
    channel: OutreachChannel = OutreachChannel.EMAIL,
    tone: str = "formal",
    user: dict = Depends(get_current_user)
):
    for lead in orchestrator.pipeline:
        if lead.id == lead_id:
            research = await orchestrator.researcher.research(lead)
            lead_dict = lead.dict()
            message = await orchestrator.personalizer.personalize(lead_dict, research, channel, tone)
            return message.dict()
    raise HTTPException(status_code=404, detail="Lead not found")


@app.post("/api/campaigns")
async def create_campaign(
    campaign: CampaignCreate,
    user: dict = Depends(get_current_user)
):
    campaign_id = str(uuid.uuid4())
    return {
        "id": campaign_id,
        "name": campaign.name,
        "description": campaign.description,
        "target_leads": campaign.target_leads,
        "channels": campaign.channels,
        "daily_limits": campaign.daily_limits,
        "status": "draft",
        "created_at": datetime.now().isoformat()
    }


@app.post("/api/campaigns/{campaign_id}/send")
async def send_campaign(
    campaign_id: str,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user)
):
    background_tasks.add_task(orchestrator.run_outreach, campaign_id)
    return {"message": "Campaign sending started", "campaign_id": campaign_id}


@app.post("/api/leads/{lead_id}/followup")
async def trigger_followup(lead_id: str, user: dict = Depends(get_current_user)):
    for lead in orchestrator.pipeline:
        if lead.id == lead_id:
            schedule = FollowUpSchedule(
                id=str(uuid.uuid4()),
                lead_id=lead_id,
                campaign_id="manual"
            )
            result = await orchestrator.followup.process_followups(schedule)
            return result
    raise HTTPException(status_code=404, detail="Lead not found")


@app.post("/api/leads/{lead_id}/qualify")
async def qualify_lead(lead_id: str, user: dict = Depends(get_current_user)):
    for lead in orchestrator.pipeline:
        if lead.id == lead_id:
            qualified = await orchestrator.appointment_setter.qualify_lead(lead.dict())
            return qualified.dict()
    raise HTTPException(status_code=404, detail="Lead not found")


@app.post("/api/leads/{lead_id}/book")
async def book_meeting(
    lead_id: str,
    meeting_data: MeetingCreate,
    user: dict = Depends(get_current_user)
):
    for lead in orchestrator.pipeline:
        if lead.id == lead_id:
            qualified = await orchestrator.appointment_setter.qualify_lead(lead.dict())
            meeting = await orchestrator.appointment_setter.book_meeting(lead.dict(), qualified)
            return meeting.dict()
    raise HTTPException(status_code=404, detail="Lead not found")


@app.get("/api/analytics/pipeline")
async def get_pipeline_analytics(user: dict = Depends(get_current_user)):
    analytics = await orchestrator.sales_manager.get_pipeline_analytics(user["id"])
    return analytics.dict()


@app.get("/api/analytics/performance")
async def get_agent_performance(user: dict = Depends(get_current_user)):
    performance = await orchestrator.sales_manager.get_agent_performance()
    return {"agents": [p.dict() for p in performance]}


@app.get("/api/analytics/funnel")
async def get_conversion_funnel(user: dict = Depends(get_current_user)):
    funnel = await orchestrator.sales_manager.get_conversion_funnel()
    return funnel


@app.get("/api/analytics/forecast")
async def get_revenue_forecast(user: dict = Depends(get_current_user)):
    forecast = await orchestrator.sales_manager.get_revenue_forecast(user["id"])
    return forecast


@app.get("/api/analytics/win-loss")
async def get_win_loss_analysis(user: dict = Depends(get_current_user)):
    analysis = await orchestrator.sales_manager.get_win_loss_analysis()
    return analysis


@app.get("/api/analytics/recommendations")
async def get_recommendations(user: dict = Depends(get_current_user)):
    recommendations = await orchestrator.sales_manager.get_recommendations(user["id"])
    return {"recommendations": recommendations}


@app.get("/api/dashboard")
async def get_dashboard(user: dict = Depends(get_current_user)):
    return await orchestrator.get_dashboard_data(user["id"])


@app.get("/api/meetings")
async def get_meetings(user: dict = Depends(get_current_user)):
    meetings = await orchestrator.appointment_setter.get_upcoming_meetings(user["id"])
    return {"meetings": [m.dict() for m in meetings]}


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0", "timestamp": datetime.now().isoformat()}


# ============================================
# SENTIMENT ANALYSIS ENDPOINTS
# ============================================

@app.post("/api/sentiment/analyze")
async def analyze_sentiment(text: str, user: dict = Depends(get_current_user)):
    from utils.sentiment import SentimentAnalyzer
    analyzer = SentimentAnalyzer()
    return analyzer.analyze(text)


@app.post("/api/sentiment/classify-reply")
async def classify_reply(text: str, user: dict = Depends(get_current_user)):
    from utils.sentiment import SentimentAnalyzer
    analyzer = SentimentAnalyzer()
    return analyzer.classify_reply(text)


# ============================================
# A/B TESTING ENDPOINTS
# ============================================

@app.post("/api/ab-tests")
async def create_ab_test(name: str, lead_id: str, variants: List[Dict], channel: str = "email", user: dict = Depends(get_current_user)):
    from utils.ab_testing import ABTestingEngine
    engine = ABTestingEngine()
    test = engine.create_test(name, lead_id, variants, channel)
    return {"test_id": test.id, "name": test.name, "variants": len(test.variants)}


@app.get("/api/ab-tests")
async def list_ab_tests(user: dict = Depends(get_current_user)):
    from utils.ab_testing import ABTestingEngine
    engine = ABTestingEngine()
    return {"tests": engine.get_all_tests()}


@app.get("/api/ab-tests/{test_id}")
async def get_ab_test(test_id: str, user: dict = Depends(get_current_user)):
    from utils.ab_testing import ABTestingEngine
    engine = ABTestingEngine()
    result = engine.get_results(test_id)
    if not result:
        raise HTTPException(status_code=404, detail="Test not found")
    return result


# ============================================
# SEND-TIME OPTIMIZATION ENDPOINTS
# ============================================

@app.get("/api/send-time/optimal")
async def get_optimal_send_time(channel: str = "email", user: dict = Depends(get_current_user)):
    from utils.send_time_optimizer import SendTimeOptimizer
    optimizer = SendTimeOptimizer()
    return optimizer.get_optimal_send_times(channel)


@app.get("/api/send-time/predict")
async def predict_best_send_time(channel: str = "email", user: dict = Depends(get_current_user)):
    from utils.send_time_optimizer import SendTimeOptimizer
    optimizer = SendTimeOptimizer()
    return optimizer.predict_best_time(channel)


@app.get("/api/send-time/stats")
async def get_send_time_stats(channel: str = "email", user: dict = Depends(get_current_user)):
    from utils.send_time_optimizer import SendTimeOptimizer
    optimizer = SendTimeOptimizer()
    return optimizer.get_stats(channel)


# ============================================
# LOCAL CRM ENDPOINTS
# ============================================

@app.post("/api/crm/contacts")
async def create_crm_contact(first_name: str, last_name: str, email: str, company: str = "", title: str = "", user: dict = Depends(get_current_user)):
    from utils.crm import LocalCRM
    crm = LocalCRM()
    contact = crm.create_contact(first_name=first_name, last_name=last_name, email=email, company=company, title=title)
    return {"id": contact.id, "name": f"{contact.first_name} {contact.last_name}", "email": contact.email}


@app.get("/api/crm/contacts")
async def list_crm_contacts(query: str = "", status: str = None, user: dict = Depends(get_current_user)):
    from utils.crm import LocalCRM
    crm = LocalCRM()
    contacts = crm.search_contacts(query=query, status=status)
    return {"contacts": [{"id": c.id, "name": f"{c.first_name} {c.last_name}", "email": c.email, "company": c.company, "status": c.status} for c in contacts]}


@app.get("/api/crm/contacts/{contact_id}")
async def get_crm_contact(contact_id: str, user: dict = Depends(get_current_user)):
    from utils.crm import LocalCRM
    crm = LocalCRM()
    contact = crm.get_contact(contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return {"id": contact.id, "first_name": contact.first_name, "last_name": contact.last_name, "email": contact.email, "company": contact.company, "title": contact.title, "status": contact.status}


@app.post("/api/crm/contacts/{contact_id}/notes")
async def add_crm_note(contact_id: str, content: str, user: dict = Depends(get_current_user)):
    from utils.crm import LocalCRM
    crm = LocalCRM()
    success = crm.add_note(contact_id, content, author=user["email"])
    if not success:
        raise HTTPException(status_code=404, detail="Contact not found")
    return {"message": "Note added"}


@app.post("/api/crm/contacts/{contact_id}/activities")
async def log_crm_activity(contact_id: str, activity_type: str, subject: str, description: str = "", user: dict = Depends(get_current_user)):
    from utils.crm import LocalCRM
    crm = LocalCRM()
    activity = crm.log_activity(contact_id, activity_type, subject, description)
    if not activity:
        raise HTTPException(status_code=404, detail="Contact not found")
    return {"id": activity.id, "type": activity.type, "subject": activity.subject}


@app.post("/api/crm/deals")
async def create_crm_deal(contact_id: str, title: str, value: float = 0, stage: str = "qualification", user: dict = Depends(get_current_user)):
    from utils.crm import LocalCRM
    crm = LocalCRM()
    deal = crm.create_deal(contact_id, title, value, stage)
    if not deal:
        raise HTTPException(status_code=404, detail="Contact not found")
    return {"id": deal.id, "title": deal.title, "value": deal.value, "stage": deal.stage}


@app.get("/api/crm/pipeline")
async def get_crm_pipeline(stage: str = None, user: dict = Depends(get_current_user)):
    from utils.crm import LocalCRM
    crm = LocalCRM()
    deals = crm.get_pipeline(stage)
    return {"deals": [{"id": d.id, "title": d.title, "value": d.value, "stage": d.stage} for d in deals]}


@app.get("/api/crm/stats")
async def get_crm_stats(user: dict = Depends(get_current_user)):
    from utils.crm import LocalCRM
    crm = LocalCRM()
    return crm.get_pipeline_stats()


@app.post("/api/crm/import")
async def import_leads_to_crm(leads: List[Dict], user: dict = Depends(get_current_user)):
    from utils.crm import LocalCRM
    crm = LocalCRM()
    imported = crm.import_leads(leads)
    return {"imported": imported}


# ============================================
# CONVERSATION MEMORY ENDPOINTS
# ============================================

@app.post("/api/conversations")
async def create_conversation(lead_id: str, lead_name: str = "", company: str = "", user: dict = Depends(get_current_user)):
    from utils.conversation_memory import ConversationMemory
    memory = ConversationMemory()
    conv = memory.get_or_create(lead_id, lead_name, company)
    return {"id": conv.id, "lead_id": conv.lead_id}


@app.post("/api/conversations/{conversation_id}/turns")
async def add_conversation_turn(conversation_id: str, role: str, content: str, channel: str = "email", user: dict = Depends(get_current_user)):
    from utils.conversation_memory import ConversationMemory
    memory = ConversationMemory()
    turn = memory.add_turn(conversation_id, role, content, channel)
    if not turn:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"id": turn.id, "role": turn.role, "content": turn.content}


@app.get("/api/conversations/{conversation_id}/context")
async def get_conversation_context(conversation_id: str, user: dict = Depends(get_current_user)):
    from utils.conversation_memory import ConversationMemory
    memory = ConversationMemory()
    context = memory.get_context_prompt(conversation_id)
    summary = memory.get_lead_summary(conversation_id)
    return {"context": context, "summary": summary}


@app.get("/api/conversations/{conversation_id}/timeline")
async def get_conversation_timeline(conversation_id: str, user: dict = Depends(get_current_user)):
    from utils.conversation_memory import ConversationMemory
    memory = ConversationMemory()
    timeline = memory.get_contact_timeline(conversation_id)
    return {"timeline": timeline}


# ============================================
# INTENT DETECTION ENDPOINTS
# ============================================

@app.post("/api/intent/detect")
async def detect_intent(text: str, user: dict = Depends(get_current_user)):
    from utils.intent_detector import IntentDetector
    detector = IntentDetector()
    return detector.detect(text)


@app.post("/api/intent/batch")
async def batch_detect_intent(texts: List[Dict], user: dict = Depends(get_current_user)):
    from utils.intent_detector import IntentDetector
    detector = IntentDetector()
    return {"results": detector.batch_detect(texts)}


@app.post("/api/intent/job-change")
async def detect_job_change(text: str, user: dict = Depends(get_current_user)):
    from utils.intent_detector import IntentDetector
    detector = IntentDetector()
    return detector.detect_job_change(text)


@app.post("/api/intent/funding")
async def detect_funding(text: str, user: dict = Depends(get_current_user)):
    from utils.intent_detector import IntentDetector
    detector = IntentDetector()
    return detector.detect_funding(text)


# ============================================
# WEBHOOK ENDPOINTS
# ============================================

@app.post("/api/webhooks")
async def create_webhook(url: str, events: List[str], secret: str = None, user: dict = Depends(get_current_user)):
    from utils.webhooks import WebhookManager
    manager = WebhookManager()
    webhook = manager.register_webhook(url, events, secret)
    return {"id": webhook.id, "url": webhook.url, "events": webhook.events}


@app.get("/api/webhooks")
async def list_webhooks(user: dict = Depends(get_current_user)):
    from utils.webhooks import WebhookManager
    manager = WebhookManager()
    return {"webhooks": manager.get_all_webhooks()}


@app.get("/api/webhooks/events")
async def get_available_events(user: dict = Depends(get_current_user)):
    from utils.webhooks import WebhookManager
    return {"events": WebhookManager.AVAILABLE_EVENTS}


@app.delete("/api/webhooks/{webhook_id}")
async def delete_webhook(webhook_id: str, user: dict = Depends(get_current_user)):
    from utils.webhooks import WebhookManager
    manager = WebhookManager()
    success = manager.unregister_webhook(webhook_id)
    if not success:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return {"message": "Webhook deleted"}


@app.get("/api/webhooks/{webhook_id}/stats")
async def get_webhook_stats(webhook_id: str, user: dict = Depends(get_current_user)):
    from utils.webhooks import WebhookManager
    manager = WebhookManager()
    stats = manager.get_webhook_stats(webhook_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return stats
