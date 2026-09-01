import pytest

from fraud_service.domain.policies import decide


@pytest.mark.unit
@pytest.mark.parametrize(
    ("probability", "expected"),
    [
        (0.0, "allow"),
        (0.699999, "allow"),
        (0.70, "review"),
        (0.849999, "review"),
        (0.85, "block"),
        (1.0, "block"),
    ],
)
def test_decision_bands(probability, expected):
    assert decide(probability, block_threshold=0.85) == expected


@pytest.mark.unit
@pytest.mark.parametrize("probability", [-0.01, 1.01])
def test_invalid_probability_rejected(probability):
    with pytest.raises(ValueError):
        decide(probability)


@pytest.mark.unit
@pytest.mark.parametrize("threshold", [-0.01, 1.01])
def test_invalid_threshold_rejected(threshold):
    with pytest.raises(ValueError):
        decide(0.5, block_threshold=threshold)
