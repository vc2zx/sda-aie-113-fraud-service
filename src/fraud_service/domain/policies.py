from fraud_service.domain.entities import Decision

DEFAULT_BLOCK_THRESHOLD = 0.85
REVIEW_MARGIN = 0.15


def decide(
    probability: float,
    block_threshold: float = DEFAULT_BLOCK_THRESHOLD,
) -> Decision:
    if not 0.0 <= probability <= 1.0:
        raise ValueError("probability must be between 0 and 1")

    if not 0.0 <= block_threshold <= 1.0:
        raise ValueError("block_threshold must be between 0 and 1")

    if probability >= block_threshold:
        return "block"

    if probability >= block_threshold - REVIEW_MARGIN:
        return "review"

    return "allow"