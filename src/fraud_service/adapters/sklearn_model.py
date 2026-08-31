from pathlib import Path

import joblib
import pandas as pd

from fraud_service.domain.entities import FraudFeatures


class SklearnModel:
    def __init__(self, model_path: str | Path) -> None:
        bundle = joblib.load(model_path)

        self._pipeline = bundle["pipeline"]
        self._model_version = str(bundle["version"])

    @property
    def model_version(self) -> str:
        return self._model_version

    def predict_probability(self, features: FraudFeatures) -> float:
        frame = pd.DataFrame([features])

        probabilities = self._pipeline.predict_proba(frame)

        return float(probabilities[0, 1])