# Raqib | رقيب — Fraud Scoring Service

A production-oriented fraud scoring service developed as the golden-thread project for **SDA-AIE-113 — Software Engineering Practices for AI Systems**, delivered through [SDAIA Academy](https://sdaia.gov.sa/en/Sectors/academy/Pages/default.aspx).

Raqib transforms a pre-trained fraud-detection model from a notebook-oriented workflow into a production-style AI service with clean architecture, strict API contracts, containerisation, automated testing, CI/CD, typed configuration, structured logging, health and readiness checks, and immutable container releases.

---

## Project Overview

The starting point of the project was a pre-trained fraud model and notebook-based scoring workflow.

The engineering objective was not to retrain or redesign the model, but to build the production system around it.

The final service includes:

- Clean Architecture separation.
- FastAPI serving layer.
- Strict request validation.
- Health and readiness endpoints.
- Model loading and startup warm-up.
- Multi-stage Docker image.
- Non-root container execution.
- Docker Compose orchestration with Redis.
- Unit, integration, and behavioural testing.
- Golden-score regression testing.
- Branch coverage enforcement.
- GitHub Actions CI/CD.
- Immutable GHCR image tags.
- Typed environment-based configuration.
- Structured JSON logging.
- Trace IDs for request correlation.
- Privacy-aware logging and sensitive-field masking.
- Batch Prediction extension with partial-failure semantics.

---

## Architecture

```text
src/fraud_service/
├── adapters/
│   └── sklearn_model.py
├── api/
│   ├── app.py
│   ├── routes.py
│   └── schemas.py
├── domain/
│   ├── entities.py
│   └── policies.py
├── service/
│   ├── interfaces.py
│   └── scorer.py
├── batch.py
├── config.py
└── logging_setup.py
```

The design follows dependency inversion:

```text
API
 ↓
Service
 ↓
Domain

Adapters → Service interface
```

The core domain and scoring service do not depend directly on FastAPI, pandas, joblib, or scikit-learn.

The concrete ML implementation is isolated behind the model adapter.

---

## Model Artefacts

The supplied production model bundle is:

```text
models/fraud_xgb_v3.joblib
```

Model version:

```text
v3.2.0
```

The bundle contains:

```python
{
    "pipeline": ...,
    "version": "v3.2.0"
}
```

The supplied transaction dataset contains 5,000 synthetic transactions:

```text
data/transactions_sample.csv
```

The golden regression scores are stored in:

```text
data/golden_scores_v3.csv
```

These scores are used as a behavioural tripwire to detect unintended model or feature-engineering changes.

---

# Quick Start

## Requirements

For the recommended containerised setup:

- Docker Desktop
- Docker Compose

For local development:

- Python 3.12+
- Git

---

## Clone

```bash
git clone https://github.com/vc2zx/sda-aie-113-fraud-service.git
cd sda-aie-113-fraud-service
```

---

## Run with Docker Compose

```bash
docker compose up -d --build
```

On systems using the legacy Compose command:

```bash
docker-compose up -d --build
```

Check container status:

```bash
docker compose ps
```

Both services should become healthy:

```text
api      healthy
redis    healthy
```

The API is available at:

```text
http://127.0.0.1:8000
```

Swagger/OpenAPI documentation:

```text
http://127.0.0.1:8000/docs
```

Stop the stack:

```bash
docker compose down
```

---

# API

## Health

```http
GET /v1/health
```

Response:

```json
{
  "status": "ok"
}
```

This endpoint verifies that the application process is alive.

---

## Readiness

```http
GET /v1/ready
```

Successful response:

```json
{
  "status": "ready"
}
```

The service reports ready only after the model has been loaded successfully and the startup warm-up prediction has completed.

Before readiness:

```http
HTTP 503 Service Unavailable
```

```json
{
  "status": "not_ready"
}
```

---

## Single Prediction

```http
POST /v1/predict
```

Example request:

```json
{
  "transaction_id": "TXN-2026-00042",
  "amount_sar": 412.5,
  "channel": "ecom",
  "merchant_category": "ELECTRONICS",
  "customer_id": "CUST-0042",
  "timestamp": "2026-07-05T22:14:00Z"
}
```

Example response:

```json
{
  "transaction_id": "TXN-2026-00042",
  "fraud_probability": 0.5570662261643815,
  "decision": "allow",
  "model_version": "v3.2.0",
  "trace_id": "<trace-id>"
}
```

The decision policy produces one of:

```text
allow
review
block
```

The default block threshold is:

```text
0.85
```

---

# API Validation

The serving contract rejects malformed inputs before they reach the model.

Validation includes:

- Unknown fields are forbidden.
- Transaction IDs have explicit length and character constraints.
- Customer IDs have explicit length and character constraints.
- Amounts must be strict numeric values.
- Amounts must be greater than zero.
- Amounts have an upper bound.
- Channels are restricted to supported values.
- Merchant categories are validated.
- Timestamps must use an RFC 3339-style datetime string.
- Leading and trailing whitespace is rejected where applicable.
- Malformed payloads return a controlled `4xx` response.

Example validation error:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed.",
    "trace_id": "<trace-id>"
  }
}
```

The repository contains a malformed request corpus with more than 50 invalid payload cases used by integration tests.

---

# Batch Prediction Extension

As the Capstone extension, Raqib implements:

```http
POST /v1/predict/batch
```

A batch accepts:

```text
1–256 transactions
```

Example:

```json
{
  "transactions": [
    {
      "transaction_id": "TXN-BATCH-0001",
      "amount_sar": 412.5,
      "channel": "ecom",
      "merchant_category": "ELECTRONICS",
      "customer_id": "CUST-0001",
      "timestamp": "2026-07-05T22:14:00Z"
    },
    {
      "transaction_id": "TXN-BATCH-0002",
      "amount_sar": 150.0,
      "channel": "pos",
      "merchant_category": "RESTAURANT",
      "customer_id": "CUST-0002",
      "timestamp": "2026-07-05T12:00:00Z"
    }
  ]
}
```

The endpoint implements **partial-failure semantics**.

If one transaction is invalid, valid transactions in the same batch are still scored.

Conceptual response:

```json
{
  "results": [
    {
      "index": 0,
      "success": true,
      "prediction": {
        "transaction_id": "TXN-BATCH-0001",
        "fraud_probability": 0.55,
        "decision": "allow",
        "model_version": "v3.2.0",
        "trace_id": "<trace-id>"
      },
      "error": null
    },
    {
      "index": 1,
      "success": false,
      "prediction": null,
      "error": {
        "code": "VALIDATION_ERROR",
        "message": "Transaction failed validation."
      }
    }
  ],
  "succeeded": 1,
  "failed": 1,
  "trace_id": "<trace-id>"
}
```

This prevents one malformed transaction from invalidating an otherwise usable batch.

---

# Local Development

Create a Python 3.12 virtual environment.

Windows:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the package and development dependencies:

```bash
python -m pip install -e ".[dev]"
```

Run the API:

```bash
uvicorn fraud_service.api.app:app --host 127.0.0.1 --port 8000
```

Run the original batch entry point:

```bash
python -m fraud_service.batch
```

Expected batch execution:

```text
Model version: v3.2.0
Scored transactions: 5000
```

---

# Configuration

Configuration is managed through `pydantic-settings`.

All application settings use the:

```text
FRAUD_
```

environment variable prefix.

| Environment Variable | Default | Description |
|---|---|---|
| `FRAUD_MODEL_PATH` | `models/fraud_xgb_v3.joblib` | Model bundle location |
| `FRAUD_BLOCK_THRESHOLD` | `0.85` | Block decision threshold |
| `FRAUD_LOG_LEVEL` | `INFO` | Application logging level |
| `FRAUD_GIT_SHA` | `dev` | Source revision identifier |
| `FRAUD_REGISTRY_TOKEN` | unset | Optional secret value |

An example configuration is provided in:

```text
configs/settings.example.env
```

The configuration layer validates values at startup.

For example, an invalid model path causes startup to fail immediately rather than waiting until the first prediction request.

---

# Model Lifecycle

The model is loaded through the FastAPI lifespan.

Startup sequence:

```text
Application starts
       ↓
Read configuration
       ↓
Load model artefact
       ↓
Create FraudScorer
       ↓
Execute warm-up prediction
       ↓
Mark application ready
```

This ensures:

- Model-loading failures are detected early.
- The first user request does not pay the complete model warm-up cost.
- `/v1/ready` represents actual serving readiness.

---

# Logging and Observability

Raqib emits structured JSON logs to stdout.

Each request receives a generated:

```text
trace_id
```

The same trace ID is returned through:

```text
X-Trace-ID
```

The response also includes:

```text
X-Process-Time-Ms
```

Operational logging includes fields such as:

- trace ID
- HTTP method
- request path
- response status
- latency
- model version
- Git SHA
- decision
- probability bucket

Example event types:

```text
model_loaded
prediction_served
batch_prediction_served
http_request
```

---

## Privacy-Safe Logging

Raw transaction information is intentionally excluded from prediction logs.

The service does not intentionally log:

- `customer_id`
- raw transaction features
- full transaction payloads
- transaction amount as a prediction log field
- secrets

Potentially sensitive logging keys are defensively replaced with:

```text
***MASKED***
```

Example:

```json
{
  "token": "***MASKED***",
  "event": "mask_test",
  "level": "info"
}
```

---

# Testing Strategy

The project uses three testing levels.

```text
tests/
├── unit/
├── integration/
└── behavioural/
```

## Unit Tests

Unit tests cover deterministic application logic such as:

- Feature extraction.
- Merchant-category normalisation.
- Fraud decision boundaries.
- Invalid probabilities.
- Invalid thresholds.
- Scoring orchestration with deterministic test doubles.

---

## Integration Tests

Integration tests exercise the FastAPI application boundary.

They cover:

- Successful prediction.
- Health endpoint.
- Readiness behaviour.
- Model-not-ready behaviour.
- Structured validation errors.
- Global exception handling.
- Malformed request corpus.
- Application startup lifecycle.
- Batch prediction.
- Batch partial failures.
- Maximum batch size.

---

## Behavioural Tests

Behavioural tests execute against the real model.

They include:

- Merchant-category casing invariance.
- Directional amount behaviour.
- Golden-score regression checks.

These tests protect against silent ML behaviour changes that ordinary unit tests may not detect.

---

## Run Tests

Run the complete suite:

```bash
python -m pytest -q
```

Current validated suite:

```text
75+ tests
```

The exact count may increase as Capstone extension tests are added.

---

## Coverage

Run branch coverage:

```bash
python -m pytest \
  --cov=fraud_service.domain \
  --cov=fraud_service.service \
  --cov=fraud_service.api \
  --cov-branch \
  --cov-fail-under=80 \
  -q
```

The CI quality gate requires at least:

```text
80% branch coverage
```

During Lab 4 validation, the core domain, service, and API layers reached:

```text
100% coverage
```

before the later Capstone extension was added.

---

# Containerisation

The production Docker image uses a multi-stage build.

Key properties:

- Python 3.12.
- Slim runtime image.
- Separate builder stage.
- Dependency wheel caching.
- Source changes do not invalidate the dependency-build layer.
- Non-root runtime user.
- Built-in readiness healthcheck.
- Model artefact copied into the runtime image.

Runtime user:

```text
app
```

This was verified using:

```bash
docker compose exec api whoami
```

---

# Docker Compose

The Compose stack contains:

```text
API
Redis
```

Redis includes its own healthcheck.

The API is configured to start only after Redis reports healthy.

The current fraud-scoring path does **not** use Redis as a prediction cache. Redis is retained as the supporting service used to demonstrate multi-service orchestration and health-based dependency gating.

---

# Benchmarks

Measured engineering benchmarks are documented in:

```text
BENCHMARKS.md
```

## API Load Test

Bare-metal load test:

| Metric | Result |
|---|---:|
| Requests | 1000 |
| Successful responses | 1000 |
| Concurrency | 20 |
| Requests/sec | 137.1847 |
| Average latency | 145.4 ms |
| p50 | 138.8 ms |
| p90 | 175.8 ms |
| p95 | 193.1 ms |
| p99 | 324.2 ms |
| Fastest | 97.1 ms |
| Slowest | 368.7 ms |

---

## Docker Image

| Image | Disk Usage | Content Size |
|---|---:|---:|
| Naive | 2.17 GB | 539 MB |
| Multi-stage | 923 MB | 257 MB |

Content-size reduction:

```text
≈ 52.3%
```

---

## Build Performance

| Build | Time |
|---|---:|
| Naive initial build | ~9 min |
| Multi-stage initial build | 189.43 s |
| Fully cached rebuild | 2.12 s |
| Warm rebuild after source change | 32.44 s |

---

## Container Prediction Latency

Five sequential requests:

```text
12.758 ms
17.841 ms
12.809 ms
11.181 ms
12.783 ms
```

Average:

```text
13.47 ms
```

The sequential container test and the concurrent `hey` benchmark represent different workloads and are not directly comparable.

---

## Time to Ready

Measured from Compose startup until the API container reported healthy:

```text
13.21 s
```

---

# CI/CD

GitHub Actions automatically runs quality gates for changes to the project.

Current pipeline includes:

```text
lint
test
image-smoke
publish
```

The test job enforces branch coverage.

The image-smoke job:

1. Builds the Docker image.
2. Starts the container.
3. Waits for `/v1/ready`.
4. Executes a real prediction request.

The publish job runs only for pushes to:

```text
main
```

---

## Immutable Container Releases

Container images are published to GitHub Container Registry:

```text
ghcr.io/vc2zx/sda-aie-113-fraud-service
```

Images use the Git commit SHA as their tag:

```text
ghcr.io/vc2zx/sda-aie-113-fraud-service:<git-sha>
```

The project intentionally does not use:

```text
latest
```

for release identification.

This provides direct traceability between:

```text
source commit
      ↓
CI run
      ↓
container image
```

Container registries also identify published images by immutable OCI digest:

```text
ghcr.io/vc2zx/sda-aie-113-fraud-service@sha256:<digest>
```

---

# Secret Hygiene

Secrets are not intended to be stored directly in source code.

Runtime secrets are supplied through environment-based configuration.

The repository includes:

```text
INCIDENT.md
```

which documents the response process for accidental credential exposure.

The response order is:

```text
Revoke / rotate
       ↓
Investigate
       ↓
Remove
       ↓
Clean history if required
       ↓
Prevent recurrence
```

Sensitive logging fields are also defensively masked.

---

# Error Handling

Validation failures return controlled `4xx` responses.

Unexpected internal exceptions return a generic response:

```json
{
  "error": {
    "code": "INTERNAL_SERVER_ERROR",
    "message": "An unexpected error occurred.",
    "trace_id": "<trace-id>"
  }
}
```

Internal stack traces and exception details are not exposed through the HTTP response.

---

# Engineering Decisions

Engineering trade-offs and architectural decisions are documented separately in:

```text
DECISIONS.md
```

The major decisions cover:

1. Isolating the ML framework behind an adapter.
2. Enforcing strict serving contracts at the HTTP boundary.
3. Loading and warming the model during startup.
4. Using a multi-stage non-root container.
5. Treating behavioural tests and immutable releases as production contracts.

---

# Supporting Documentation

| File | Purpose |
|---|---|
| `README.md` | Main setup and operational runbook |
| `BENCHMARKS.md` | Measured performance and container results |
| `DECISIONS.md` | Engineering decisions and trade-offs |
| `INCIDENT.md` | Secret-exposure response procedure |
| `configs/settings.example.env` | Configuration example |
| `LAB1.md` – `LAB6.md` | Original course lab instructions |
| `LAB1-SETUP.md` – `LAB6-SETUP.md` | Lab environment/setup instructions |

---

# Development History

The project was intentionally developed incrementally so the Git history demonstrates the productionisation process.

Major milestones include:

```text
Notebook
   ↓
Clean Architecture
   ↓
FastAPI service
   ↓
Docker + Compose
   ↓
Three-level testing
   ↓
CI/CD
   ↓
Typed configuration + structured logging
   ↓
Capstone extension
```

Representative commits include:

```text
refactor: extract clean architecture layers from notebook
feat(api): prediction endpoint with validation, health, tracing
feat(container): add multi-stage image and compose stack
test: three-level suite with behavioural tripwires
ci: add quality gates and immutable image publishing
feat(ops): add typed config structured logging and secret hygiene
feat(api): add batch prediction with partial failures
```

---

# Capstone Requirements Mapping

| Area | Implementation |
|---|---|
| Architecture | Domain, service, adapter, and API separation |
| API | FastAPI, strict validation, predictable error envelopes |
| Model lifecycle | Startup loading, warm-up, readiness |
| Container | Multi-stage build, slim runtime, non-root user |
| Orchestration | Docker Compose with Redis health gating |
| Unit testing | Policies, features, scorer |
| Integration testing | API contracts and malformed corpus |
| Behavioural testing | Real-model invariance, directional, and golden tests |
| Coverage | ≥80% branch coverage gate |
| CI/CD | GitHub Actions |
| Release | GHCR image tagged with commit SHA |
| Configuration | `pydantic-settings` with `FRAUD_*` variables |
| Logging | Structured JSON logs and trace IDs |
| Privacy | No raw transaction logging and sensitive-field masking |
| Incident response | `INCIDENT.md` |
| Extension | Batch Prediction ≤256 with partial failures |
| Performance evidence | `BENCHMARKS.md` |
| Engineering decisions | `DECISIONS.md` |

---

# Capstone Demo Flow

A concise demonstration can be performed in approximately five minutes.

### 1. Start the stack

```bash
docker compose up -d
```

### 2. Verify readiness

```bash
curl http://127.0.0.1:8000/v1/ready
```

### 3. Submit a valid prediction

```bash
curl \
  -X POST \
  -H "Content-Type: application/json" \
  --data-binary @payloads/sample.json \
  http://127.0.0.1:8000/v1/predict
```

### 4. Demonstrate malformed-input rejection

Submit one payload from:

```text
payloads/malformed/
```

and show the controlled `4xx` response.

### 5. Run behavioural tests

```bash
python -m pytest -m behavioural -q
```

### 6. Show CI/CD

Open GitHub Actions and demonstrate the automated:

```text
lint → test → image-smoke → publish
```

pipeline.

### 7. Explain one engineering trade-off

Use one decision from:

```text
DECISIONS.md
```

---

# Course and Attribution

This project was developed as the golden-thread engineering project for:

**SDA-AIE-113 — Software Engineering Practices for AI Systems**

Program provider:

### https://github.com/SDAIAAcademy

The project demonstrates the software-engineering practices required to move an AI model from an experimental notebook workflow toward a production-oriented service.

The original classroom repository, model artefacts, datasets, lab instructions, and course structure were provided for educational use as part of the SDA-AIE-113 program.

---

## Repository

```text
https://github.com/vc2zx/sda-aie-113-fraud-service
```
