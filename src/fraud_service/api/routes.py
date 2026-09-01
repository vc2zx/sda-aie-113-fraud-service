import structlog
from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from fraud_service.api.schemas import PredictRequest, PredictResponse

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


@router.post("/predict", response_model=PredictResponse)
def predict(
    payload: PredictRequest,
    request: Request,
) -> PredictResponse | JSONResponse:
    if not getattr(request.app.state, "ready", False):
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

    transaction = payload.to_domain()
    result = request.app.state.scorer.score(transaction)

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