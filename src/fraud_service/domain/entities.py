from dataclasses import dataclass
from datetime import datetime
from math import log1p
from typing import Literal, TypedDict

Channel = Literal["ecom", "pos", "atm"]
Decision = Literal["allow", "review", "block"]


class FraudFeatures(TypedDict):
    amount_log: float
    channel: str
    mcc: str
    hour_of_day: int
    is_night: int


@dataclass(frozen=True, slots=True)
class Transaction:
    transaction_id: str
    amount_sar: float
    merchant_category: str
    customer_id: str
    timestamp: datetime
    channel: Channel

    def to_features(self) -> FraudFeatures:
        hour = self.timestamp.hour

        return {
            "amount_log": log1p(self.amount_sar),
            "channel": self.channel,
            "mcc": self.merchant_category.strip().upper().replace(" ", "_"),
            "hour_of_day": hour,
            "is_night": int(hour < 6),
        }


@dataclass(frozen=True, slots=True)
class FraudScore:
    transaction_id: str
    probability: float
    decision: Decision
    model_version: str