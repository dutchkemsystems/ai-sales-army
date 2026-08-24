import uuid
from typing import Dict, List, Optional
from datetime import datetime
import re


class IntentDetector:
    def __init__(self):
        self.intent_keywords = {
            "buying_intent": {
                "keywords": [
                    "pricing", "cost", "how much", "quote", "proposal",
                    "demo", "trial", "pilot", "implementation", "onboard",
                    "contract", "agreement", "purchase", "buy", "order",
                    "integrate", "deploy", "start", "begin", "launch",
                ],
                "weight": 1.0,
            },
            "research_intent": {
                "keywords": [
                    "features", "capabilities", "compare", "alternative",
                    "review", "case study", "testimonial", "benchmark",
                    "documentation", "specs", "technical", "api",
                ],
                "weight": 0.7,
            },
            "urgency_signal": {
                "keywords": [
                    "urgent", "asap", "immediately", "deadline", "before",
                    "need now", "time sensitive", "critical", "emergency",
                    "this week", "this month", "end of quarter",
                ],
                "weight": 0.9,
            },
            "budget_signal": {
                "keywords": [
                    "budget", "funded", "approved", "allocated", "invest",
                    "roi", "return", "savings", "cost reduction", "afford",
                ],
                "weight": 0.8,
            },
            "decision_maker": {
                "keywords": [
                    "decide", "approval", "authorize", "sign off",
                    "final say", "my team", "my department", "my company",
                    "we are looking", "we want", "we need",
                ],
                "weight": 0.85,
            },
            "competitor_mention": {
                "keywords": [
                    "alternative to", "compared to", "switch from",
                    "moving from", "currently using", "replace",
                    "better than", "vs", "versus",
                ],
                "weight": 0.75,
            },
        }

    def detect(self, text: str) -> Dict:
        text_lower = text.lower()
        detected_intents = {}
        total_score = 0

        for intent_name, config in self.intent_keywords.items():
            matches = [kw for kw in config["keywords"] if kw in text_lower]
            if matches:
                score = len(matches) / len(config["keywords"]) * config["weight"]
                detected_intents[intent_name] = {
                    "score": round(score, 3),
                    "matches": matches,
                    "confidence": min(1.0, score * 2),
                }
                total_score += score

        if not detected_intents:
            primary_intent = "neutral"
            confidence = 0.0
        else:
            primary_intent = max(detected_intents.items(), key=lambda x: x[1]["score"])[0]
            confidence = detected_intents[primary_intent]["confidence"]

        return {
            "primary_intent": primary_intent,
            "confidence": round(confidence, 3),
            "all_intents": detected_intents,
            "total_score": round(total_score, 3),
            "recommended_action": self._recommend_action(primary_intent, confidence),
            "should_escalate": primary_intent in ("buying_intent", "urgency_signal") and confidence > 0.6,
        }

    def _recommend_action(self, intent: str, confidence: float) -> str:
        if intent == "buying_intent" and confidence > 0.5:
            return "schedule_meeting"
        elif intent == "urgency_signal" and confidence > 0.5:
            return "priority_outreach"
        elif intent == "decision_maker" and confidence > 0.5:
            return "fast_track"
        elif intent == "competitor_mention" and confidence > 0.5:
            return "competitive_positioning"
        elif intent == "research_intent" and confidence > 0.3:
            return "send_case_studies"
        elif intent == "budget_signal" and confidence > 0.3:
            return "send_proposal"
        return "continue_nurture"

    def detect_job_change(self, text: str) -> Dict:
        job_change_signals = [
            "just started", "new role", "joined", "promoted",
            "moved to", "transitioning", "new position", "appointed",
        ]
        text_lower = text.lower()
        matches = [s for s in job_change_signals if s in text_lower]
        return {
            "is_job_change": len(matches) > 0,
            "signals": matches,
            "recommendation": "reach_out_congratulate" if matches else None,
        }

    def detect_funding(self, text: str) -> Dict:
        funding_patterns = [
            r"raised?\s+\$[\d.]+\s*(million|billion|M|B)",
            r"series\s+[a-e]",
            r"ipo|going public",
            r"valuation\s+of\s+\$[\d.]+",
            r"funding\s+round",
        ]
        text_lower = text.lower()
        matches = []
        for pattern in funding_patterns:
            if re.search(pattern, text_lower):
                matches.append(pattern)
        return {
            "has_funding_signal": len(matches) > 0,
            "signals": matches,
            "recommendation": "high_priority_outreach" if matches else None,
        }

    def detect_technology_change(self, text: str) -> Dict:
        tech_signals = [
            "migrating", "switching", "new platform", "tech stack",
            "digital transformation", "modernize", "upgrade", "adopt",
        ]
        text_lower = text.lower()
        matches = [s for s in tech_signals if s in text_lower]
        return {
            "has_tech_change": len(matches) > 0,
            "signals": matches,
            "recommendation": "technical_outreach" if matches else None,
        }

    def batch_detect(self, texts: List[Dict]) -> List[Dict]:
        results = []
        for item in texts:
            text = item.get("text", "")
            lead_id = item.get("lead_id")
            detection = self.detect(text)
            detection["lead_id"] = lead_id
            results.append(detection)
        return results
