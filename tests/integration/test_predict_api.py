from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from fraud_service.api.app import create_app

MALFORMED = sorted(Path("payloads/malformed").glob("*.json"))


def _payload(sample_txn):
    return {
        "transaction_id": sample_txn.transaction_id,
        "amount_sar": sample_txn.amount_sar,
        "channel": sample_txn.channel,
        "merchant_category": sample_txn.merchant_category,
        "customer_id": sample_txn.customer_id,
        "timestamp": sample_txn.timestamp.isoformat(),
    }


@pytest.mark.integration
def test_predict_contract(client_factory, sample_txn):
    client = client_factory(probability=0.93)

    response = client.post("/v1/predict", json=_payload(sample_txn))

    assert response.status_code == 200
    body = response.json()
    assert body["decision"] == "block"
    assert body["fraud_probability"] == pytest.approx(0.93)
    assert body["model_version"] == "test-1"
    assert body["trace_id"]
    assert response.headers["X-Trace-ID"]


@pytest.mark.integration
@pytest.mark.parametrize("payload_file", MALFORMED, ids=lambda p: p.stem)
def test_malformed_corpus_rejected(client_factory, payload_file):
    client = client_factory()

    response = client.post(
        "/v1/predict",
        content=payload_file.read_bytes(),
        headers={"content-type": "application/json"},
    )

    assert 400 <= response.status_code < 500, payload_file.name


@pytest.mark.integration
def test_health(client_factory):
    client = client_factory()

    response = client.get("/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.integration
def test_ready_when_ready(client_factory):
    client = client_factory()

    response = client.get("/v1/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


@pytest.mark.integration
def test_ready_503_before_startup():
    client = TestClient(create_app(), raise_server_exceptions=False)

    response = client.get("/v1/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "not_ready"}


@pytest.mark.integration
def test_predict_503_when_model_not_ready(sample_txn):
    app = create_app()
    app.state.ready = False
    client = TestClient(app, raise_server_exceptions=False)

    response = client.post("/v1/predict", json=_payload(sample_txn))

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "MODEL_NOT_READY"


@pytest.mark.integration
def test_validation_error_envelope(client_factory):
    client = client_factory()

    response = client.post(
        "/v1/predict",
        json={"transaction_id": "bad"},
    )

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["error"]["trace_id"]


@pytest.mark.integration
def test_unexpected_error_does_not_leak_stack(client_factory, sample_txn):
    class ExplodingScorer:
        def score(self, transaction):
            raise RuntimeError("SECRET INTERNAL STACK DETAIL")

    client = client_factory()
    client.app.state.scorer = ExplodingScorer()

    response = client.post("/v1/predict", json=_payload(sample_txn))

    assert response.status_code == 500
    body = response.json()
    assert body["error"]["code"] == "INTERNAL_SERVER_ERROR"
    assert "SECRET INTERNAL STACK DETAIL" not in response.text


@pytest.mark.integration
def test_real_startup_lifecycle():
    app = create_app()

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/v1/ready")
        assert response.status_code == 200
        assert app.state.ready is True

    assert app.state.ready is False
