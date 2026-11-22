from __future__ import annotations

import random

from astrbot.api import logger

from .config import PluginConfig
from .data import LotteryRepository
from .model import (
    DrawResult,
    LotteryActivity,
    LotteryError,
    LotteryStatus,
    Prize,
    PrizeStatus,
)


class LotteryService:
    """Coordinate lottery business operations."""

    def __init__(self, config: PluginConfig):
        self._config = config
        self._repository = LotteryRepository(config.lottery_data_file)

    def start_activity(self, group_id: str) -> LotteryError | None:
        activity = self._repository.get(group_id)
        if activity and activity.active:
            return LotteryError.ACTIVITY_EXISTS

        prizes: list[Prize] = []
        levels: set[str] = set()
        try:
            no_prize_weight = int(self._config.no_prize_weight)
            for entry in self._config.prize_entries:
                level = str(entry["level"]).strip()
                name = str(entry["name"]).strip()
                weight = int(entry["weight"])
                count = int(entry["count"])
                if not level or not name or level in levels or weight < 0 or count <= 0:
                    return LotteryError.INVALID_PRIZE_CONFIG
                levels.add(level)
                prizes.append(
                    Prize(
                        level=level,
                        name=name,
                        weight=weight,
                        count=count,
                        remaining=count,
                    )
                )
        except (KeyError, TypeError, ValueError):
            return LotteryError.INVALID_PRIZE_CONFIG

        if (
            not prizes
            or no_prize_weight < 0
            or (no_prize_weight == 0 and not any(prize.weight > 0 for prize in prizes))
        ):
            return LotteryError.INVALID_PRIZE_CONFIG

        self._repository.save(
            LotteryActivity(
                group_id=group_id,
                prizes=prizes,
                no_prize_weight=no_prize_weight,
            )
        )
        logger.info(f"[Lottery] Started activity in group {group_id}")
        return None

    def draw(self, group_id: str, user_id: str, nickname: str) -> DrawResult:
        activity = self._repository.get(group_id)
        if not activity:
            return DrawResult(error=LotteryError.ACTIVITY_NOT_FOUND)
        if not activity.active:
            return DrawResult(error=LotteryError.ACTIVITY_INACTIVE)
        if user_id in activity.participants:
            return DrawResult(error=LotteryError.ALREADY_PARTICIPATED)

        activity.participants[user_id] = nickname
        candidates: list[Prize | None] = [
            prize
            for prize in activity.prizes
            if prize.remaining > 0 and prize.weight > 0
        ]
        weights = [prize.weight for prize in candidates if prize is not None]
        if activity.no_prize_weight > 0:
            candidates.append(None)
            weights.append(activity.no_prize_weight)

        won_prize = (
            random.choices(candidates, weights=weights, k=1)[0] if candidates else None
        )
        if won_prize:
            won_prize.remaining -= 1
            activity.winners[user_id] = won_prize.level

        self._repository.save(activity)
        return DrawResult(prize=won_prize)

    def stop_activity(self, group_id: str) -> LotteryError | None:
        activity = self._repository.get(group_id)
        if not activity:
            return LotteryError.ACTIVITY_NOT_FOUND
        if not activity.active:
            return LotteryError.ACTIVITY_INACTIVE
        activity.active = False
        self._repository.save(activity)
        return None

    def delete_activity(self, group_id: str) -> LotteryError | None:
        if not self._repository.get(group_id):
            return LotteryError.ACTIVITY_NOT_FOUND
        self._repository.delete(group_id)
        return None

    def get_status(self, group_id: str) -> LotteryStatus | None:
        activity = self._repository.get(group_id)
        if not activity:
            return None

        winners_by_level: dict[str, list[str]] = {}
        for user_id, level in activity.winners.items():
            winners_by_level.setdefault(level, []).append(
                activity.participants.get(user_id, user_id)
            )
        return LotteryStatus(
            active=activity.active,
            participant_count=len(activity.participants),
            winner_count=len(activity.winners),
            prizes=[
                PrizeStatus(
                    level=prize.level,
                    name=prize.name,
                    remaining=prize.remaining,
                    total=prize.count,
                )
                for prize in activity.prizes
                if prize.weight > 0
            ],
            winners_by_level=winners_by_level,
        )
