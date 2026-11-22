from __future__ import annotations

import json
from pathlib import Path

from astrbot.api import logger

from .model import LotteryActivity

DATA_VERSION = 2


class LotteryRepository:
    """Store lottery activities in a JSON file."""

    def __init__(self, data_file: Path):
        self.data_file = data_file
        self._activities: dict[str, LotteryActivity] = {}
        if not data_file.exists():
            return

        try:
            payload = json.loads(data_file.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                raise TypeError("Lottery data root must be an object")
            if payload.get("version") != DATA_VERSION:
                logger.info("[LotteryRepository] Reset incompatible lottery data")
                self.save()
                return
            self._activities = {
                group_id: LotteryActivity.from_dict(activity)
                for group_id, activity in payload.get("activities", {}).items()
            }
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            logger.error(f"[LotteryRepository] Failed to load lottery data: {exc}")

    def get(self, group_id: str) -> LotteryActivity | None:
        return self._activities.get(group_id)

    def save(self, activity: LotteryActivity | None = None) -> None:
        if activity:
            self._activities[activity.group_id] = activity
        payload = {
            "version": DATA_VERSION,
            "activities": {
                group_id: stored_activity.to_dict()
                for group_id, stored_activity in self._activities.items()
            },
        }
        try:
            self.data_file.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError as exc:
            logger.error(f"[LotteryRepository] Failed to save lottery data: {exc}")

    def delete(self, group_id: str) -> None:
        del self._activities[group_id]
        self.save()
