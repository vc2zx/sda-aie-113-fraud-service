from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from secrets import token_hex
from time import perf_counter

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from fraud_service.adapters.sklearn_model import SklearnModel
from fraud_service.api.routes import router
from fraud_service.domain.entities import Transaction
from fraud_service.service.scorer import FraudScorer

MODEL_PATH = Path("models/fraud_xgb_v3.joblib")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.ready = False

    model = SklearnModel(MODEL_PATH)
    scorer = FraudScorer(model)

    warmup_transaction = Transaction(
        transaction_id="WARMUP-0001",
        amount_sar=100.0,
        channel="ecom",
        merchant_category="ELECTRONICS",
        customer_id="WARMUP-CUSTOMER",
        timestamp=datetime.fromisoformat("2026-07-05T22:14:00+00:00"),
    )

    scorer.score(warmup_transaction)

    app.state.scorer = scorer
    app.state.ready = True

    yield

    app.state.ready = False


def create_app() -> FastAPI:
    app = FastAPI(
        title="Fraud Scoring Service",
        version="0.1.0",
        lifespan=lifespan,
    )

    @app.middleware("http")
    async def tracing_middleware(
        request: Request,
        call_next,
    ) -> Response:
        trace_id = token_hex(8)
        request.state.trace_id = trace_id

        started = perf_counter()
        response = await call_next(request)
        elapsed_ms = (perf_counter() - started) * 1000

        response.headers["X-Trace-ID"] = trace_id
        response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.3f}"

        return response

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        _exc: RequestValidationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed.",
                    "trace_id": request.state.trace_id,
                }
            },
        )
    @app.exception_handler(Exception)
    async def global_exception_handler(
        request: Request,
        _exc: Exception,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred.",
                    "trace_id": request.state.trace_id,
                }
            },
        )

    app.include_router(router)

    return app


app = create_app()