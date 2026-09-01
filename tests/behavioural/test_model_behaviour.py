import csv
from dataclasses import replace
from datetime import datetime
from pathlib import Path

import pytest

from fraud_service.domain.entities import Transaction

pytestmark = pytest.mark.behavioural


def _score(model, transaction):
    return model.predict_probability(transaction.to_features())


def test_invariance_to_merchant_casing(real_model, sample_txn):
    lower = _score(real_model, sample_txn)
    upper = _score(
        real_model,
        replace(sample_txn, merchant_category="ELECTRONICS"),
    )

    assert lower == pytest.approx(upper, abs=1e-9)


def test_directional_amount(real_model, sample_txn):
    small = _score(
        real_model,
        replace(sample_txn, amount_sar=50.0),
    )
    large = _score(
        real_model,
        replace(sample_txn, amount_sar=50_000.0),
    )

    assert large >= small - 1e-6


def test_golden_scores(real_model):
    golden_path = Path("data/golden_scores_v3.csv")

    with golden_path.open(encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))[:20]

    assert rows

    for row in rows:
        transaction = Transaction(
            transaction_id=row["transaction_id"],
            amount_sar=float(row["amount_sar"]),
            channel=row["channel"],
            merchant_category=row["mcc"],
            customer_id=row["customer_id"],
            timestamp=datetime.fromisoformat(
                row["timestamp"]
            ),
        )

        actual = _score(real_model, transaction)
        expected = float(row["score"])

        assert actual == pytest.approx(
            expected,
            abs=1e-9,
        ), row["transaction_id"]
