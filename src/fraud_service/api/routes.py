import structlog
from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from fraud_service.api.schemas import (
    BatchItemError,
    BatchItemResult,
    BatchPredictRequest,
    BatchPredictResponse,
    PredictRequest,
    PredictResponse,
)

log = structlog.get_logger()

router = APIRouter(prefix="/v1")


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready", response_model=None)
def ready(request: Request) -> dict[str, str] | JSONResponse:
    if not getattr(request.app.state, "ready", False):
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready"},
        )

    return {"status": "ready"}


def _not_ready_response(request: Request) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "error": {
                "code": "MODEL_NOT_READY",
                "message": "The fraud model is not ready.",
                "trace_id": request.state.trace_id,
            }
        },
    )


def _score_payload(
    payload: PredictRequest,
    request: Request,
) -> PredictResponse:
    result = request.app.state.scorer.score(payload.to_domain())

    log.info(
        "prediction_served",
        decision=result.decision,
        probability_bucket=round(result.probability, 1),
        model_version=result.model_version,
        git_sha=getattr(
            getattr(request.app.state, "settings", None),
            "git_sha",
            "dev",
        ),
    )

    return PredictResponse(
        transaction_id=result.transaction_id,
        fraud_probability=result.probability,
        decision=result.decision,
        model_version=result.model_version,
        trace_id=request.state.trace_id,
    )


@router.post("/predict", response_model=PredictResponse)
def predict(
    payload: PredictRequest,
    request: Request,
) -> PredictResponse | JSONResponse:
    if not getattr(request.app.state, "ready", False):
        return _not_ready_response(request)

    return _score_payload(payload, request)


@router.post("/predict/batch", response_model=BatchPredictResponse)
def predict_batch(
    payload: BatchPredictRequest,
    request: Request,
) -> BatchPredictResponse | JSONResponse:
    if not getattr(request.app.state, "ready", False):
        return _not_ready_response(request)

    results: list[BatchItemResult] = []
    succeeded = 0
    failed = 0

    for index, item in enumerate(payload.transactions):
        try:
            validated = PredictRequest.model_validate(item)
        except ValidationError:
            failed += 1
            results.append(
                BatchItemResult(
                    index=index,
                    success=False,
                    error=BatchItemError(
                        code="VALIDATION_ERROR",
                        message="Transaction failed validation.",
                    ),
                )
            )
            continue

        prediction = _score_payload(validated, request)
        succeeded += 1

        results.append(
            BatchItemResult(
                index=index,
                success=True,
                prediction=prediction,
            )
        )

    log.info(
        "batch_prediction_served",
        batch_size=len(payload.transactions),
        succeeded=succeeded,
        failed=failed,
    )

    return BatchPredictResponse(
        results=results,
        succeeded=succeeded,
        failed=failed,
        trace_id=request.state.trace_id,
    )