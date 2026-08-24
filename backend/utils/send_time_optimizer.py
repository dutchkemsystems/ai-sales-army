import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import json


class SendTimeOptimizer:
    def __init__(self):
        self.send_history: List[Dict] = []
        self.hourly_performance: Dict[str, Dict[int, Dict]] = defaultdict(lambda: {"sent": 0, "opened": 0, "replied": 0})
        self.daily_performance: Dict[str, Dict[int, Dict]] = defaultdict(lambda: {"sent": 0, "opened": 0, "replied": 0})

    def record_send(self, channel: str, send_time: datetime, timezone: str = "UTC"):
        hour = send_time.hour
        day = send_time.weekday()
        self.hourly_performance[channel][hour]["sent"] += 1
        self.daily_performance[channel][day]["sent"] += 1
        self.send_history.append({
            "channel": channel,
            "send_time": send_time.isoformat(),
            "hour": hour,
            "day": day,
            "timezone": timezone,
        })

    def record_open(self, channel: str, open_time: datetime):
        hour = open_time.hour
        day = open_time.weekday()
        self.hourly_performance[channel][hour]["opened"] += 1
        self.daily_performance[channel][day]["opened"] += 1

    def record_reply(self, channel: str, reply_time: datetime):
        hour = reply_time.hour
        day = reply_time.weekday()
        self.hourly_performance[channel][hour]["replied"] += 1
        self.daily_performance[channel][day]["replied"] += 1

    def get_optimal_send_times(self, channel: str, n: int = 3) -> List[Dict]:
        hourly = self.hourly_performance.get(channel, {})
        daily = self.daily_performance.get(channel, {})

        hour_scores = {}
        for hour, data in hourly.items():
            if data["sent"] >= 5:
                open_rate = data["opened"] / data["sent"]
                reply_rate = data["replied"] / data["sent"]
                hour_scores[hour] = open_rate * 0.4 + reply_rate * 0.6
            else:
                hour_scores[hour] = 0.3

        day_scores = {}
        for day, data in daily.items():
            if data["sent"] >= 5:
                open_rate = data["opened"] / data["sent"]
                reply_rate = data["replied"] / data["sent"]
                day_scores[day] = open_rate * 0.4 + reply_rate * 0.6
            else:
                day_scores[day] = 0.3

        if not hour_scores:
            return self._get_defaults(channel, n)

        scored_times = []
        for hour, h_score in hour_scores.items():
            for day, d_score in day_scores.items():
                combined = h_score * 0.6 + d_score * 0.4
                scored_times.append({
                    "hour": int(hour),
                    "day": int(day),
                    "day_name": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][int(day)],
                    "score": round(combined, 4),
                    "confidence": min(1.0, (hourly.get(hour, {}).get("sent", 0) / 10)),
                })

        scored_times.sort(key=lambda x: x["score"], reverse=True)
        return scored_times[:n]

    def _get_defaults(self, channel: str, n: int) -> List[Dict]:
        if channel == "email":
            defaults = [
                {"hour": 9, "day": 1, "day_name": "Tuesday", "score": 0.5, "confidence": 0.0},
                {"hour": 10, "day": 2, "day_name": "Wednesday", "score": 0.48, "confidence": 0.0},
                {"hour": 14, "day": 3, "day_name": "Thursday", "score": 0.45, "confidence": 0.0},
                {"hour": 8, "day": 0, "day_name": "Monday", "score": 0.42, "confidence": 0.0},
                {"hour": 11, "day": 4, "day_name": "Friday", "score": 0.40, "confidence": 0.0},
            ]
        elif channel == "linkedin":
            defaults = [
                {"hour": 8, "day": 1, "day_name": "Tuesday", "score": 0.55, "confidence": 0.0},
                {"hour": 17, "day": 2, "day_name": "Wednesday", "score": 0.50, "confidence": 0.0},
                {"hour": 7, "day": 3, "day_name": "Thursday", "score": 0.48, "confidence": 0.0},
            ]
        else:
            defaults = [
                {"hour": 10, "day": 2, "day_name": "Wednesday", "score": 0.45, "confidence": 0.0},
                {"hour": 14, "day": 3, "day_name": "Thursday", "score": 0.42, "confidence": 0.0},
            ]
        return defaults[:n]

    def get_stats(self, channel: str) -> Dict:
        hourly = self.hourly_performance.get(channel, {})
        daily = self.daily_performance.get(channel, {})
        total_sent = sum(d["sent"] for d in hourly.values())
        total_opened = sum(d["opened"] for d in hourly.values())
        total_replied = sum(d["replied"] for d in hourly.values())
        return {
            "total_sent": total_sent,
            "total_opened": total_opened,
            "total_replied": total_replied,
            "overall_open_rate": round((total_opened / total_sent * 100) if total_sent > 0 else 0, 2),
            "overall_reply_rate": round((total_replied / total_sent * 100) if total_sent > 0 else 0, 2),
            "data_points": total_sent,
        }

    def predict_best_time(self, channel: str, timezone: str = "UTC") -> Dict:
        times = self.get_optimal_send_times(channel, n=1)
        if times and times[0]["confidence"] > 0.3:
            return {
                "recommended_hour": times[0]["hour"],
                "recommended_day": times[0]["day"],
                "day_name": times[0]["day_name"],
                "confidence": times[0]["confidence"],
                "based_on_data": True,
            }
        defaults = self._get_defaults(channel, 1)
        return {
            "recommended_hour": defaults[0]["hour"],
            "recommended_day": defaults[0]["day"],
            "day_name": defaults[0]["day_name"],
            "confidence": 0.0,
            "based_on_data": False,
        }
