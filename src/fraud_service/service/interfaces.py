from typing import Protocol

from fraud_service.domain.entities import FraudFeatures


class Model(Protocol):
    @property
    def model_version(self) -> str:
        ...

    def predict_probability(self, features: FraudFeatures) -> float:
        ...