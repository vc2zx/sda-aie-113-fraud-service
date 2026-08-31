from pathlib import Path

import pandas as pd

from fraud_service.adapters.sklearn_model import SklearnModel
from fraud_service.domain.entities import Transaction
from fraud_service.service.scorer import FraudScorer

DATA_PATH = Path("data/transactions_sample.csv")
MODEL_PATH = Path("models/fraud_xgb_v3.joblib")
OUTPUT_PATH = Path("scored.csv")


def main() -> None:
    model = SklearnModel(MODEL_PATH)
    scorer = FraudScorer(model)

    data = pd.read_csv(DATA_PATH)

    results: list[dict[str, object]] = []

    for row in data.itertuples(index=False):
        transaction = Transaction(
            transaction_id=row.transaction_id,
            amount_sar=float(row.amount_sar),
            channel=row.channel,
            merchant_category=row.merchant_category,
            customer_id=row.customer_id,
            timestamp=pd.to_datetime(row.timestamp).to_pydatetime(),
        )

        score = scorer.score(transaction)

        results.append(
            {
                "transaction_id": score.transaction_id,
                "score": score.probability,
                "decision": score.decision,
                "model_version": score.model_version,
            }
        )

    scored = pd.DataFrame(results)
    scored.to_csv(OUTPUT_PATH, index=False)

    print(f"Model version: {model.model_version}")
    print(f"Scored transactions: {len(scored)}")
    print(scored["decision"].value_counts().to_string())
    print(f"Output written to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()