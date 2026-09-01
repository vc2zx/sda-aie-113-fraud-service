import pytest

from fraud_service.service.scorer import FraudScorer
from tests.conftest import ConstantModel


@pytest.mark.unit
def test_scorer_orchestrates_model(sample_txn):
    scorer = FraudScorer(ConstantModel(0.93, version="fixture-v1"))

    result = scorer.score(sample_txn)

    assert result.transaction_id == sample_txn.transaction_id
    assert result.probability == pytest.approx(0.93)
    assert result.decision == "block"
    assert result.model_version == "fixture-v1"
