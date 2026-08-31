from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from fraud_service.domain.entities import Channel, Decision, Transaction


class PredictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    transaction_id: str = Field(min_length=8, max_length=64)
    amount_sar: float = Field(gt=0, le=1_000_000, strict=True)
    channel: Channel
    merchant_category: str = Field(min_length=2, max_length=64)
    customer_id: str = Field(min_length=4, max_length=64)
    timestamp: datetime

    @field_validator("transaction_id", "customer_id")
    @classmethod
    def reject_surrounding_whitespace(cls, value: str) -> str:
        if value != value.strip():
            raise ValueError("leading or trailing whitespace is not allowed")
        return value

    @field_validator("merchant_category")
    @classmethod
    def validate_merchant_category(cls, value: str) -> str:
        if value != value.strip():
            raise ValueError("leading or trailing whitespace is not allowed")
        if "\x00" in value:
            raise ValueError("null bytes are not allowed")
        return value

    def to_domain(self) -> Transaction:
        return Transaction(**self.model_dump())


class PredictResponse(BaseModel):
    transaction_id: str
    fraud_probability: float = Field(ge=0, le=1)
    decision: Decision
    model_version: str
    trace_id: str


class ErrorDetail(BaseModel):
    code: str
    message: str
    trace_id: str


class ErrorResponse(BaseModel):
    error: ErrorDetail