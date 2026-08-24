import uuid
import asyncio
from typing import Dict, List, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, field
import json
import hashlib
import hmac


@dataclass
class Webhook:
    id: str
    url: str
    events: List[str]
    secret: Optional[str] = None
    active: bool = True
    fail_count: int = 0
    last_triggered: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class WebhookDelivery:
    id: str
    webhook_id: str
    event: str
    payload: Dict
    status: str = "pending"
    response_code: Optional[int] = None
    response_body: Optional[str] = None
    attempts: int = 0
    max_attempts: int = 3
    created_at: datetime = field(default_factory=datetime.now)
    delivered_at: Optional[datetime] = None


class WebhookManager:
    def __init__(self):
        self.webhooks: Dict[str, Webhook] = {}
        self.deliveries: List[WebhookDelivery] = []
        self.event_handlers: Dict[str, List[Callable]] = {}
        self._delivery_queue: List[WebhookDelivery] = []

    def register_webhook(self, url: str, events: List[str], secret: str = None) -> Webhook:
        webhook_id = str(uuid.uuid4())
        webhook = Webhook(
            id=webhook_id,
            url=url,
            events=events,
            secret=secret,
        )
        self.webhooks[webhook_id] = webhook
        return webhook

    def unregister_webhook(self, webhook_id: str) -> bool:
        if webhook_id in self.webhooks:
            del self.webhooks[webhook_id]
            return True
        return False

    def update_webhook(self, webhook_id: str, **kwargs) -> Optional[Webhook]:
        webhook = self.webhooks.get(webhook_id)
        if not webhook:
            return None
        for key, value in kwargs.items():
            if hasattr(webhook, key):
                setattr(webhook, key, value)
        return webhook

    def trigger_event(self, event: str, payload: Dict) -> List[WebhookDelivery]:
        matching_webhooks = [
            w for w in self.webhooks.values()
            if w.active and (event in w.events or "*" in w.events)
        ]
        deliveries = []
        for webhook in matching_webhooks:
            delivery = WebhookDelivery(
                id=str(uuid.uuid4()),
                webhook_id=webhook.id,
                event=event,
                payload=payload,
            )
            self.deliveries.append(delivery)
            self._delivery_queue.append(delivery)
            deliveries.append(delivery)

        self._process_internal_handlers(event, payload)
        return deliveries

    async def process_queue(self):
        import httpx
        pending = [d for d in self._delivery_queue if d.status == "pending" and d.attempts < d.max_attempts]
        for delivery in pending:
            webhook = self.webhooks.get(delivery.webhook_id)
            if not webhook or not webhook.active:
                delivery.status = "skipped"
                continue
            delivery.attempts += 1
            try:
                headers = {"Content-Type": "application/json", "X-Webhook-Event": delivery.event, "X-Webhook-ID": delivery.id}
                if webhook.secret:
                    body = json.dumps(delivery.payload, default=str)
                    signature = hmac.new(webhook.secret.encode(), body.encode(), hashlib.sha256).hexdigest()
                    headers["X-Webhook-Signature"] = f"sha256={signature}"
                async with httpx.AsyncClient(timeout=10) as client:
                    response = await client.post(webhook.url, json=delivery.payload, headers=headers)
                    delivery.response_code = response.status_code
                    delivery.response_body = response.text[:500]
                    delivery.status = "delivered" if 200 <= response.status_code < 300 else "failed"
                    delivery.delivered_at = datetime.now()
                    webhook.last_triggered = datetime.now()
                    webhook.fail_count = 0 if delivery.status == "delivered" else webhook.fail_count + 1
            except Exception as e:
                delivery.status = "failed"
                delivery.response_body = str(e)[:500]
                webhook.fail_count += 1
            if webhook.fail_count >= 5:
                webhook.active = False

    def register_handler(self, event: str, handler: Callable):
        if event not in self.event_handlers:
            self.event_handlers[event] = []
        self.event_handlers[event].append(handler)

    def _process_internal_handlers(self, event: str, payload: Dict):
        handlers = self.event_handlers.get(event, []) + self.event_handlers.get("*", [])
        for handler in handlers:
            try:
                handler(payload)
            except Exception:
                pass

    def get_delivery_status(self, delivery_id: str) -> Optional[WebhookDelivery]:
        for d in self.deliveries:
            if d.id == delivery_id:
                return d
        return None

    def get_webhook_stats(self, webhook_id: str) -> Dict:
        webhook = self.webhooks.get(webhook_id)
        if not webhook:
            return {}
        deliveries = [d for d in self.deliveries if d.webhook_id == webhook_id]
        successful = sum(1 for d in deliveries if d.status == "delivered")
        failed = sum(1 for d in deliveries if d.status == "failed")
        return {
            "webhook_id": webhook.id,
            "url": webhook.url,
            "events": webhook.events,
            "active": webhook.active,
            "total_deliveries": len(deliveries),
            "successful": successful,
            "failed": failed,
            "success_rate": round((successful / len(deliveries) * 100) if deliveries else 0, 2),
            "last_triggered": webhook.last_triggered.isoformat() if webhook.last_triggered else None,
        }

    def get_all_webhooks(self) -> List[Dict]:
        return [
            {
                "id": w.id,
                "url": w.url,
                "events": w.events,
                "active": w.active,
                "fail_count": w.fail_count,
                "last_triggered": w.last_triggered.isoformat() if w.last_triggered else None,
                "created_at": w.created_at.isoformat(),
            }
            for w in self.webhooks.values()
        ]

    AVAILABLE_EVENTS = [
        "lead.discovered",
        "lead.researched",
        "lead.personalized",
        "outreach.sent",
        "outreach.opened",
        "outreach.replied",
        "outreach.bounced",
        "followup.sent",
        "meeting.booked",
        "meeting.confirmed",
        "meeting.cancelled",
        "deal.created",
        "deal.won",
        "deal.lost",
        "campaign.completed",
    ]
