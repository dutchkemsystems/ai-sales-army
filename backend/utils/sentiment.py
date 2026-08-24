from typing import Dict, List, Optional
from enum import Enum
import re


class SentimentType(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class SentimentAnalyzer:
    def __init__(self):
        self._classifier = None

    def _get_classifier(self):
        if self._classifier is None:
            try:
                from transformers import pipeline as hf_pipeline
                self._classifier = hf_pipeline(
                    "sentiment-analysis",
                    model="distilbert-base-uncased-finetuned-sst-2-english",
                    top_k=None
                )
            except Exception:
                self._classifier = None
        return self._classifier

    def analyze(self, text: str) -> Dict:
        try:
            classifier = self._get_classifier()
            if classifier is None:
                return self._fallback_analyze(text)
            results = classifier(text[:512])[0]
            scores = {r["label"].lower(): r["score"] for r in results}

            positive = scores.get("positive", 0)
            negative = scores.get("negative", 0)

            if positive > 0.7:
                sentiment = SentimentType.POSITIVE
            elif negative > 0.7:
                sentiment = SentimentType.NEGATIVE
            else:
                sentiment = SentimentType.NEUTRAL

            return {
                "sentiment": sentiment.value,
                "confidence": max(positive, negative),
                "scores": scores,
                "should_escalate": sentiment == SentimentType.NEGATIVE and negative > 0.85,
                "is_interested": sentiment == SentimentType.POSITIVE and positive > 0.75,
            }
        except Exception as e:
            return self._fallback_analyze(text)

    def classify_reply(self, text: str) -> Dict:
        interest_keywords = [
            "interested", "schedule", "demo", "meeting", "call", "pricing",
            "tell me more", "sounds good", "let's talk", "yes", "sure",
            "absolutely", "perfect", "great", "love to", "would like",
        ]
        not_interested_keywords = [
            "not interested", "unsubscribe", "remove me", "stop", "no thank",
            "don't contact", "opt out", "leave me alone", "busy",
        ]
        question_keywords = ["?", "how", "what", "when", "where", "why", "can you", "could you"]

        text_lower = text.lower()
        interest_score = sum(1 for kw in interest_keywords if kw in text_lower)
        not_interested_score = sum(1 for kw in not_interested_keywords if kw in text_lower)
        question_score = sum(1 for kw in question_keywords if kw in text_lower)

        if not_interested_score > 0:
            classification = "not_interested"
            action = "unsubscribe"
        elif interest_score >= 2:
            classification = "interested"
            action = "escalate_to_human"
        elif question_score > 0:
            classification = "question"
            action = "auto_reply"
        else:
            classification = "neutral"
            action = "continue_sequence"

        return {
            "classification": classification,
            "action": action,
            "interest_score": interest_score,
            "not_interested_score": not_interested_score,
            "question_score": question_score,
        }

    def detect_urgency(self, text: str) -> Dict:
        urgent_keywords = [
            "urgent", "asap", "immediately", "emergency", "critical",
            "deadline", "today", "now", "hurry", "time sensitive",
        ]
        text_lower = text.lower()
        urgency_score = sum(1 for kw in urgent_keywords if kw in text_lower)

        return {
            "is_urgent": urgency_score >= 2,
            "urgency_level": "high" if urgency_score >= 3 else "medium" if urgency_score >= 1 else "low",
            "score": urgency_score,
        }

    def _fallback_analyze(self, text: str) -> Dict:
        positive_words = ["great", "good", "excellent", "love", "thanks", "yes", "sure", "interested"]
        negative_words = ["bad", "terrible", "hate", "no", "never", "stop", "unsubscribe"]
        words = text.lower().split()
        pos = sum(1 for w in words if w in positive_words)
        neg = sum(1 for w in words if w in negative_words)

        if pos > neg:
            sentiment = "positive"
        elif neg > pos:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        return {
            "sentiment": sentiment,
            "confidence": 0.6,
            "scores": {"positive": pos / max(len(words), 1), "negative": neg / max(len(words), 1)},
            "should_escalate": neg >= 3,
            "is_interested": pos >= 3,
            "fallback": True,
        }

    def batch_analyze(self, texts: List[str]) -> List[Dict]:
        return [self.analyze(text) for text in texts]
