import uuid
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class ConversationTurn:
    id: str
    role: str
    content: str
    channel: str
    timestamp: datetime
    metadata: Dict = field(default_factory=dict)


@dataclass
class Conversation:
    id: str
    lead_id: str
    lead_name: str
    company: str
    turns: List[ConversationTurn] = field(default_factory=list)
    sentiment_history: List[str] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)
    objections: List[str] = field(default_factory=list)
    interests: List[str] = field(default_factory=list)
    status: str = "active"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


class ConversationMemory:
    def __init__(self):
        self.conversations: Dict[str, Conversation] = {}

    def get_or_create(self, lead_id: str, lead_name: str = "", company: str = "") -> Conversation:
        for conv in self.conversations.values():
            if conv.lead_id == lead_id and conv.status == "active":
                return conv
        conv_id = str(uuid.uuid4())
        conv = Conversation(
            id=conv_id,
            lead_id=lead_id,
            lead_name=lead_name,
            company=company,
        )
        self.conversations[conv_id] = conv
        return conv

    def add_turn(self, conversation_id: str, role: str, content: str, channel: str, metadata: Dict = None) -> Optional[ConversationTurn]:
        conv = self.conversations.get(conversation_id)
        if not conv:
            return None
        turn = ConversationTurn(
            id=str(uuid.uuid4()),
            role=role,
            content=content,
            channel=channel,
            timestamp=datetime.now(),
            metadata=metadata or {},
        )
        conv.turns.append(turn)
        conv.updated_at = datetime.now()
        self._extract_topics(conv, content)
        return turn

    def add_sentiment(self, conversation_id: str, sentiment: str):
        conv = self.conversations.get(conversation_id)
        if conv:
            conv.sentiment_history.append(sentiment)

    def add_objection(self, conversation_id: str, objection: str):
        conv = self.conversations.get(conversation_id)
        if conv and objection not in conv.objections:
            conv.objections.append(objection)

    def add_interest(self, conversation_id: str, interest: str):
        conv = self.conversations.get(conversation_id)
        if conv and interest not in conv.interests:
            conv.interests.append(interest)

    def get_context_prompt(self, conversation_id: str, max_turns: int = 10) -> str:
        conv = self.conversations.get(conversation_id)
        if not conv:
            return ""

        recent_turns = conv.turns[-max_turns:] if conv.turns else []
        context_parts = [f"Lead: {conv.lead_name} at {conv.company}"]

        if conv.objections:
            context_parts.append(f"Previous objections: {', '.join(conv.objections[-3:])}")
        if conv.interests:
            context_parts.append(f"Expressed interests: {', '.join(conv.interests[-3:])}")
        if conv.sentiment_history:
            recent_sentiment = conv.sentiment_history[-3:]
            context_parts.append(f"Recent sentiment trend: {' -> '.join(recent_sentiment)}")

        if recent_turns:
            context_parts.append("\nConversation history:")
            for turn in recent_turns:
                prefix = "Lead" if turn.role == "lead" else "You"
                context_parts.append(f"  {prefix}: {turn.content[:200]}")

        return "\n".join(context_parts)

    def get_lead_summary(self, conversation_id: str) -> Dict:
        conv = self.conversations.get(conversation_id)
        if not conv:
            return {}

        positive_count = sum(1 for s in conv.sentiment_history if s == "positive")
        negative_count = sum(1 for s in conv.sentiment_history if s == "negative")
        total = len(conv.sentiment_history) or 1

        return {
            "lead_name": conv.lead_name,
            "company": conv.company,
            "total_interactions": len(conv.turns),
            "channels_used": list(set(t.channel for t in conv.turns)),
            "sentiment_score": round((positive_count - negative_count) / total, 2),
            "objections": conv.objections,
            "interests": conv.interests,
            "last_interaction": conv.updated_at.isoformat(),
            "status": conv.status,
        }

    def _extract_topics(self, conv: Conversation, content: str):
        topic_keywords = {
            "pricing": ["price", "cost", "budget", "expensive", "affordable", "discount"],
            "demo": ["demo", "demonstration", "show", "walkthrough", "trial"],
            "integration": ["integrate", "integration", "api", "connect", "plugin"],
            "support": ["support", "help", "issue", "problem", "bug"],
            "timeline": ["timeline", "deadline", "when", "how long", "schedule"],
            "competition": ["competitor", "alternative", "compared", "versus", "vs"],
        }
        content_lower = content.lower()
        for topic, keywords in topic_keywords.items():
            if any(kw in content_lower for kw in keywords):
                if topic not in conv.topics:
                    conv.topics.append(topic)

    def close_conversation(self, conversation_id: str):
        conv = self.conversations.get(conversation_id)
        if conv:
            conv.status = "closed"

    def get_all_conversations(self, lead_id: str = None) -> List[Conversation]:
        convs = list(self.conversations.values())
        if lead_id:
            convs = [c for c in convs if c.lead_id == lead_id]
        return sorted(convs, key=lambda c: c.updated_at, reverse=True)
