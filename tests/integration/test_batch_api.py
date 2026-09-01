import pytest


def _valid_payload(index: int = 1) -> dict:
    return {
        "transaction_id": f"TXN-BATCH-{index:04d}",
        "amount_sar": 412.5,
        "channel": "ecom",
        "merchant_category": "ELECTRONICS",
        "customer_id": f"CUST-{index:04d}",
        "timestamp": "2026-07-05T22:14:00Z",
    }


@pytest.mark.integration
def test_batch_predict_success(client_factory):
    client = client_factory(probability=0.93)

    response = client.post(
        "/v1/predict/batch",
        json={
            "transactions": [
                _valid_payload(1),
                _valid_payload(2),
            ]
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["succeeded"] == 2
    assert body["failed"] == 0
    assert len(body["results"]) == 2
    assert body["results"][0]["success"] is True
    assert body["results"][0]["prediction"]["decision"] == "block"


@pytest.mark.integration
def test_batch_partial_failure(client_factory):
    client = client_factory(probability=0.10)

    invalid = _valid_payload(2)
    invalid["amount_sar"] = -1

    response = client.post(
        "/v1/predict/batch",
        json={
            "transactions": [
                _valid_payload(1),
                invalid,
                _valid_payload(3),
            ]
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["succeeded"] == 2
    assert body["failed"] == 1

    failed = body["results"][1]
    assert failed["success"] is False
    assert failed["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.integration
def test_batch_rejects_more_than_256(client_factory):
    client = client_factory()

    response = client.post(
        "/v1/predict/batch",
        json={
            "transactions": [
                _valid_payload(i)
                for i in range(257)
            ]
        },
    )

    assert response.status_code == 422


@pytest.mark.integration
def test_batch_rejects_empty_batch(client_factory):
    client = client_factory()

    response = client.post(
        "/v1/predict/batch",
        json={"transactions": []},
    )

    assert response.status_code == 422