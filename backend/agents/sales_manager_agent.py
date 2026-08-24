from typing import List, Dict, Optional
from datetime import datetime, date, timedelta
import logging
from uuid import uuid4

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import PipelineAnalytics, AgentPerformance, Lead, LeadStatus

logger = logging.getLogger(__name__)

AGENT_NAMES = [
    "Lead Finder",
    "Researcher",
    "Personalizer",
    "Outreach",
    "Follow-Up",
    "Appointment Setter",
    "Sales Manager",
]


class SalesManagerAgent:
    def __init__(self):
        self.leads: List[Lead] = []
        self.agent_metrics: Dict[str, Dict] = {}
        for name in AGENT_NAMES:
            self.agent_metrics[name] = {
                "leads_processed": 0,
                "success_count": 0,
                "fail_count": 0,
                "avg_time_per_lead": 0.0,
                "success_rate": 0.0,
                "last_run": None,
            }

    async def get_pipeline_analytics(self, user_id: str = None) -> PipelineAnalytics:
        leads = self.leads
        total = len(leads)
        stage_counts = self._get_stage_counts(leads)
        won = stage_counts.get(LeadStatus.CLOSED_WON, 0)
        conversion_rate = (won / total * 100) if total > 0 else 0.0
        avg_time = self._calculate_avg_time_to_book(leads)

        return PipelineAnalytics(
            id=str(uuid4()),
            date=date.today(),
            total_leads=total,
            researched=stage_counts.get(LeadStatus.RESEARCHED, 0),
            personalized=stage_counts.get(LeadStatus.PERSONALIZED, 0),
            outreach_sent=stage_counts.get(LeadStatus.OUTREACH_SENT, 0),
            replied=stage_counts.get(LeadStatus.FOLLOWING_UP, 0),
            interested=stage_counts.get(LeadStatus.INTERESTED, 0),
            meetings_booked=stage_counts.get(LeadStatus.MEETING_BOOKED, 0),
            meetings_completed=stage_counts.get(LeadStatus.CLOSED_WON, 0),
            closed_won=won,
            conversion_rate=conversion_rate,
            avg_time_to_book=avg_time,
            revenue_forecast=won * 5000,
        )

    async def get_agent_performance(self) -> List[AgentPerformance]:
        performances = []
        for agent_name, metrics in self.agent_metrics.items():
            performances.append(AgentPerformance(
                agent_name=agent_name,
                leads_processed=metrics["leads_processed"],
                success_count=metrics["success_count"],
                fail_count=metrics["fail_count"],
                avg_time_per_lead=metrics["avg_time_per_lead"],
                success_rate=metrics["success_rate"],
                last_run=metrics["last_run"],
            ))
        return performances

    async def get_conversion_funnel(self) -> Dict:
        stage_counts = self._get_stage_counts(self.leads)
        return {status.value: count for status, count in stage_counts.items()}

    async def get_revenue_forecast(self, user_id: str = None) -> Dict:
        leads = self.leads
        by_stage: Dict[str, float] = {}
        total_forecast = 0.0
        stage_values = {
            LeadStatus.DISCOVERED: 1000,
            LeadStatus.RESEARCHED: 2000,
            LeadStatus.PERSONALIZED: 3000,
            LeadStatus.OUTREACH_SENT: 4000,
            LeadStatus.INTERESTED: 8000,
            LeadStatus.MEETING_BOOKED: 15000,
            LeadStatus.CLOSED_WON: 50000,
        }
        for lead in leads:
            value = stage_values.get(lead.status, 0)
            by_stage[lead.status.value] = by_stage.get(lead.status.value, 0) + value
            total_forecast += value

        return {
            "total_forecast": round(total_forecast, 2),
            "by_stage": {k: round(v, 2) for k, v in by_stage.items()},
            "confidence_level": "medium",
        }

    async def get_win_loss_analysis(self) -> Dict:
        won = sum(1 for l in self.leads if l.status == LeadStatus.CLOSED_WON)
        lost = sum(1 for l in self.leads if l.status == LeadStatus.LOST)
        total = won + lost
        return {
            "won_count": won,
            "lost_count": lost,
            "win_rate": round((won / total * 100) if total > 0 else 0, 2),
            "common_loss_reasons": ["Budget constraints", "Timing not right", "Competitor chosen"],
        }

    async def get_recommendations(self, user_id: str = None) -> List[Dict]:
        leads = self.leads
        recommendations = []

        discovered = [l for l in leads if l.status == LeadStatus.DISCOVERED]
        if discovered:
            recommendations.append({
                "action": "research_leads",
                "title": f"{len(discovered)} leads need research",
                "reason": "Move discovered leads to researched status",
                "priority": "high",
            })

        researched = [l for l in leads if l.status == LeadStatus.RESEARCHED]
        if researched:
            recommendations.append({
                "action": "personalize_outreach",
                "title": f"{len(researched)} leads ready for personalization",
                "reason": "Create personalized messages for researched leads",
                "priority": "high",
            })

        if not recommendations:
            recommendations.append({
                "action": "discover_leads",
                "title": "Start by discovering leads",
                "reason": "Your pipeline is empty",
                "priority": "medium",
            })

        return recommendations

    def _calculate_avg_time_to_book(self, leads: List[Lead]) -> float:
        booked = [l for l in leads if l.status in (LeadStatus.MEETING_BOOKED, LeadStatus.CLOSED_WON)]
        if not booked:
            return 0.0
        total_days = sum((l.updated_at - l.created_at).total_seconds() / 86400 for l in booked)
        return round(total_days / len(booked), 2)

    def _get_stage_counts(self, leads: List[Lead]) -> Dict:
        counts = {status: 0 for status in LeadStatus}
        for lead in leads:
            if lead.status in counts:
                counts[lead.status] += 1
        return counts

    def update_lead(self, lead: Lead) -> None:
        for i, existing in enumerate(self.leads):
            if existing.id == lead.id:
                self.leads[i] = lead
                return
        self.leads.append(lead)

    def get_leads_by_status(self, status: LeadStatus) -> List[Lead]:
        return [l for l in self.leads if l.status == status]
