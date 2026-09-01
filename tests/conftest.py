from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from fraud_service.api.app import create_app
from fraud_service.domain.entities import FraudFeatures, Transaction
from fraud_service.service.scorer import FraudScorer


class ConstantModel:
    def __init__(self, probability: float, version: str = "test-1") -> None:
        self._probability = probability
        self._version = version

    @property
    def model_version(self) -> str:
        return self._version

    def predict_probability(self, features: FraudFeatures) -> float:
        return self._probability


@pytest.fixture
def sample_txn() -> Transaction:
    return Transaction(
        transaction_id="TXN-TEST-0001",
        amount_sar=250.0,
        channel="ecom",
        merchant_category="electronics",
        customer_id="CUST-77",
        timestamp=datetime(2026, 7, 5, 3, 30, tzinfo=UTC),
    )


@pytest.fixture
def client_factory():
    def _make(
        probability: float = 0.10,
        threshold: float = 0.85,
    ) -> TestClient:
        app = create_app()
        app.state.ready = True
        app.state.scorer = FraudScorer(
            model=ConstantModel(probability),
            block_threshold=threshold,
        )
        return TestClient(app, raise_server_exceptions=False)

    return _make


@pytest.fixture(scope="session")
def real_model():
    from pathlib import Path

    from fraud_service.adapters.sklearn_model import SklearnModel

    return SklearnModel(Path("models/fraud_xgb_v3.joblib"))
