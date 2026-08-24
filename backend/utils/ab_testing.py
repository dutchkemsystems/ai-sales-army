import uuid
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import math
import random


@dataclass
class Variant:
    id: str
    name: str
    subject: Optional[str]
    body: str
    channel: str
    sent: int = 0
    opened: int = 0
    clicked: int = 0
    replied: int = 0
    bounced: int = 0


@dataclass
class ABTest:
    id: str
    name: str
    lead_id: str
    variants: List[Variant]
    status: str = "running"
    winner_id: Optional[str] = None
    confidence_level: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


class ABTestingEngine:
    def __init__(self):
        self.tests: Dict[str, ABTest] = {}
        self.min_sample_size = 30
        self.confidence_threshold = 0.95

    def create_test(
        self,
        name: str,
        lead_id: str,
        variants: List[Dict],
        channel: str = "email",
    ) -> ABTest:
        test_id = str(uuid.uuid4())
        variant_objects = []
        for i, v in enumerate(variants):
            variant_objects.append(Variant(
                id=str(uuid.uuid4()),
                name=v.get("name", f"Variant {chr(65 + i)}"),
                subject=v.get("subject"),
                body=v.get("body", ""),
                channel=channel,
            ))

        test = ABTest(
            id=test_id,
            name=name,
            lead_id=lead_id,
            variants=variant_objects,
        )
        self.tests[test_id] = test
        return test

    def select_variant(self, test_id: str) -> Optional[Variant]:
        test = self.tests.get(test_id)
        if not test or not test.variants:
            return None
        total_sent = sum(v.sent for v in test.variants)
        if total_sent < 10:
            return test.variants[total_sent % len(test.variants)]
        return self._thompson_sampling(test)

    def record_event(self, test_id: str, variant_id: str, event: str):
        test = self.tests.get(test_id)
        if not test:
            return
        for variant in test.variants:
            if variant.id == variant_id:
                if event == "sent":
                    variant.sent += 1
                elif event == "opened":
                    variant.opened += 1
                elif event == "clicked":
                    variant.clicked += 1
                elif event == "replied":
                    variant.replied += 1
                elif event == "bounced":
                    variant.bounced += 1
                break
        self._check_winner(test)

    def _thompson_sampling(self, test: ABTest) -> Variant:
        samples = []
        for variant in test.variants:
            if variant.sent == 0:
                samples.append((variant, random.betavariate(1, 1)))
                continue
            alpha = variant.replied + 1
            beta = variant.sent - variant.replied + 1
            samples.append((variant, random.betavariate(alpha, beta)))
        samples.sort(key=lambda x: x[1], reverse=True)
        return samples[0][0]

    def _check_winner(self, test: ABTest):
        if test.status != "running":
            return
        eligible = [v for v in test.variants if v.sent >= self.min_sample_size]
        if len(eligible) < 2:
            return

        best = max(eligible, key=lambda v: v.replied / max(v.sent, 1))
        others = [v for v in eligible if v.id != best.id]
        if not others:
            return

        best_rate = best.replied / max(best.sent, 1)
        for other in others:
            other_rate = other.replied / max(other.sent, 1)
            z_score = self._calculate_z_score(best_rate, best.sent, other_rate, other.sent)
            confidence = self._z_to_confidence(z_score)
            if confidence >= self.confidence_threshold:
                test.status = "completed"
                test.winner_id = best.id
                test.confidence_level = confidence
                test.completed_at = datetime.now()
                break

    def _calculate_z_score(self, p1: float, n1: int, p2: float, n2: int) -> float:
        if n1 == 0 or n2 == 0:
            return 0
        p_pool = (p1 * n1 + p2 * n2) / (n1 + n2)
        if p_pool == 0 or p_pool == 1:
            return 0
        se = math.sqrt(p_pool * (1 - p_pool) * (1/n1 + 1/n2))
        if se == 0:
            return 0
        return (p1 - p2) / se

    def _z_to_confidence(self, z: float) -> float:
        z = abs(z)
        if z < 1.645:
            return 0.90
        elif z < 1.96:
            return 0.95
        elif z < 2.576:
            return 0.99
        return 0.999

    def get_results(self, test_id: str) -> Optional[Dict]:
        test = self.tests.get(test_id)
        if not test:
            return None

        variant_results = []
        for v in test.variants:
            open_rate = (v.opened / v.sent * 100) if v.sent > 0 else 0
            reply_rate = (v.replied / v.sent * 100) if v.sent > 0 else 0
            click_rate = (v.clicked / v.sent * 100) if v.sent > 0 else 0
            variant_results.append({
                "id": v.id,
                "name": v.name,
                "subject": v.subject,
                "body_preview": v.body[:100] + "..." if len(v.body) > 100 else v.body,
                "sent": v.sent,
                "opened": v.opened,
                "clicked": v.clicked,
                "replied": v.replied,
                "bounced": v.bounced,
                "open_rate": round(open_rate, 2),
                "reply_rate": round(reply_rate, 2),
                "click_rate": round(click_rate, 2),
            })

        return {
            "test_id": test.id,
            "name": test.name,
            "status": test.status,
            "winner_id": test.winner_id,
            "confidence_level": test.confidence_level,
            "variants": variant_results,
            "created_at": test.created_at.isoformat(),
            "completed_at": test.completed_at.isoformat() if test.completed_at else None,
        }

    def get_all_tests(self) -> List[Dict]:
        return [self.get_results(t.id) for t in self.tests.values()]
