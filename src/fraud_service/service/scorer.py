from fraud_service.domain.entities import FraudScore, Transaction
from fraud_service.domain.policies import DEFAULT_BLOCK_THRESHOLD, decide
from fraud_service.service.interfaces import Model


class FraudScorer:
    def __init__(
        self,
        model: Model,
        block_threshold: float = DEFAULT_BLOCK_THRESHOLD,
    ) -> None:
        self._model = model
        self._block_threshold = block_threshold

    def score(self, transaction: Transaction) -> FraudScore:
        features = transaction.to_features()
        probability = self._model.predict_probability(features)

        return FraudScore(
            transaction_id=transaction.transaction_id,
            probability=probability,
            decision=decide(probability, self._block_threshold),
            model_version=self._model.model_version,
        )