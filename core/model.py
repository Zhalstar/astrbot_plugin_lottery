from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any


@dataclass(slots=True)
class Prize:
    level: str
    name: str
    weight: int
    count: int
    remaining: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "level": self.level,
            "name": self.name,
            "weight": self.weight,
            "count": self.count,
            "remaining": self.remaining,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Prize:
        return cls(
            level=data["level"],
            name=data["name"],
            weight=data["weight"],
            count=data["count"],
            remaining=data["remaining"],
        )


@dataclass(slots=True)
class LotteryActivity:
    group_id: str
    prizes: list[Prize]
    no_prize_weight: int
    active: bool = True
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    participants: dict[str, str] = field(default_factory=dict)
    winners: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "group_id": self.group_id,
            "active": self.active,
            "created_at": self.created_at,
            "no_prize_weight": self.no_prize_weight,
            "participants": self.participants,
            "winners": self.winners,
            "prizes": [prize.to_dict() for prize in self.prizes],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LotteryActivity:
        return cls(
            group_id=data["group_id"],
            active=data["active"],
            created_at=data["created_at"],
            no_prize_weight=data["no_prize_weight"],
            participants=data["participants"],
            winners=data["winners"],
            prizes=[Prize.from_dict(prize) for prize in data["prizes"]],
        )


class LotteryError(Enum):
    ACTIVITY_EXISTS = auto()
    ACTIVITY_NOT_FOUND = auto()
    ACTIVITY_INACTIVE = auto()
    ALREADY_PARTICIPATED = auto()
    INVALID_PRIZE_CONFIG = auto()


@dataclass(slots=True)
class DrawResult:
    error: LotteryError | None = None
    prize: Prize | None = None


@dataclass(slots=True)
class PrizeStatus:
    level: str
    name: str
    remaining: int
    total: int


@dataclass(slots=True)
class LotteryStatus:
    active: bool
    participant_count: int
    winner_count: int
    prizes: list[PrizeStatus]
    winners_by_level: dict[str, list[str]]
