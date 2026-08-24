import asyncio
import uuid
from typing import Dict, List, Optional
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.lead_finder_agent import LeadFinderAgent
from agents.researcher_agent import ResearcherAgent
from agents.personalizer_agent import PersonalizerAgent
from agents.outreach_agent import OutreachAgent
from agents.followup_agent import FollowUpAgent
from agents.appointment_setter_agent import AppointmentSetterAgent
from agents.sales_manager_agent import SalesManagerAgent
from models import Lead, LeadStatus, OutreachChannel, PersonalizedMessage


class OrchestratorAgent:
    def __init__(self):
        self.lead_finder = LeadFinderAgent()
        self.researcher = ResearcherAgent()
        self.personalizer = PersonalizerAgent()
        self.outreach = OutreachAgent()
        self.followup = FollowUpAgent()
        self.appointment_setter = AppointmentSetterAgent()
        self.sales_manager = SalesManagerAgent()
        self.active_campaigns: Dict = {}
        self.pipeline: List[Lead] = []

    def _update_lead_status(self, lead: Lead, status: LeadStatus):
        lead.status = status
        lead.updated_at = datetime.now()

    async def run_full_pipeline(self, filters: Dict, user_id: str = None) -> Dict:
        results = {
            "leads_discovered": 0, "leads_researched": 0, "messages_personalized": 0,
            "outreach_sent": 0, "followups_scheduled": 0, "followups_processed": 0,
            "meetings_booked": 0, "errors": [], "status": "in_progress",
        }

        try:
            leads = await self.lead_finder.discover(filters)
            results["leads_discovered"] = len(leads)
            self.pipeline.extend(leads)
            for lead in leads:
                self.sales_manager.update_lead(lead)

            research_tasks = [self.researcher.research(lead) for lead in leads]
            research_results = await asyncio.gather(*research_tasks, return_exceptions=True)
            researched_leads = []
            for i, result in enumerate(research_results):
                if not isinstance(result, Exception):
                    self._update_lead_status(leads[i], LeadStatus.RESEARCHED)
                    researched_leads.append(leads[i])
                    results["leads_researched"] += 1

            personalized_messages = []
            for lead in researched_leads:
                for channel in [OutreachChannel.EMAIL, OutreachChannel.LINKEDIN]:
                    try:
                        research = await self.researcher.research(lead)
                        lead_dict = {
                            "id": lead.id, "lead_first_name": lead.lead_first_name,
                            "lead_last_name": lead.lead_last_name, "lead_title": lead.lead_title,
                            "company_name": lead.company_name,
                        }
                        message = await self.personalizer.personalize(lead_dict, research, channel)
                        personalized_messages.append((lead, message))
                        results["messages_personalized"] += 1
                    except Exception as e:
                        results["errors"].append(f"Personalization failed: {e}")

            for lead, message in personalized_messages:
                try:
                    sent = await self.outreach.send_outreach(message, "pipeline")
                    self._update_lead_status(lead, LeadStatus.OUTREACH_SENT)
                    results["outreach_sent"] += 1
                except Exception as e:
                    results["errors"].append(f"Outreach failed: {e}")

            for lead in [l for l, _ in personalized_messages]:
                try:
                    lead_dict = {"id": lead.id, "lead_first_name": lead.lead_first_name,
                                 "lead_last_name": lead.lead_last_name, "company_name": lead.company_name}
                    schedule = await self.followup.schedule_followups(lead_dict, personalized_messages[0][1])
                    results["followups_scheduled"] += 1
                except Exception as e:
                    results["errors"].append(f"Follow-up scheduling failed: {e}")

            analytics = await self.sales_manager.get_pipeline_analytics(user_id)
            results["analytics"] = analytics.dict()
            results["status"] = "completed"

        except Exception as e:
            results["errors"].append(f"Pipeline failed: {e}")
            results["status"] = "failed"

        return results

    async def run_lead_through_pipeline(self, lead: Lead, user_id: str = None) -> Dict:
        result = {"lead_id": lead.id, "stages_completed": [], "errors": []}
        try:
            self._update_lead_status(lead, LeadStatus.RESEARCHED)
            result["stages_completed"].append("research")

            for channel in [OutreachChannel.EMAIL, OutreachChannel.LINKEDIN]:
                try:
                    research = await self.researcher.research(lead)
                    lead_dict = {"id": lead.id, "lead_first_name": lead.lead_first_name,
                                 "lead_last_name": lead.lead_last_name, "lead_title": lead.lead_title,
                                 "company_name": lead.company_name}
                    message = await self.personalizer.personalize(lead_dict, research, channel)
                    await self.outreach.send_outreach(message, "single_lead")
                    result["stages_completed"].append(f"outreach_{channel.value}")
                except Exception as e:
                    result["errors"].append(f"{channel.value} failed: {e}")

            self._update_lead_status(lead, LeadStatus.OUTREACH_SENT)
            self.pipeline.append(lead)
            result["status"] = "completed"
        except Exception as e:
            result["status"] = "failed"
            result["errors"].append(str(e))
        return result

    async def run_outreach(self, campaign_id: str) -> Dict:
        return {"campaign_id": campaign_id, "status": "completed", "outreach_sent": 0}

    async def process_pending_followups(self) -> Dict:
        return {"processed": 0, "meetings_booked": 0, "errors": []}

    async def get_dashboard_data(self, user_id: str = None) -> Dict:
        try:
            analytics = await self.sales_manager.get_pipeline_analytics(user_id)
            performance = await self.sales_manager.get_agent_performance()
            recommendations = await self.sales_manager.get_recommendations(user_id)
            return {
                "analytics": analytics.dict(),
                "performance": [p.dict() for p in performance],
                "recommendations": recommendations,
                "pipeline_summary": {"total_leads": len(self.pipeline)},
            }
        except Exception as e:
            return {"error": str(e), "analytics": {}, "performance": [], "recommendations": []}
