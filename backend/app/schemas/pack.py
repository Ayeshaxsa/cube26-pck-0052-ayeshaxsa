from enum import Enum

from pydantic import BaseModel, Field


class ObservationStatus(str, Enum):
    OBSERVED = "observed"
    UNCERTAIN = "uncertain"


class CheckStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    UNCERTAIN = "uncertain"


class OperationalDecision(str, Enum):
    SEAL = "seal"
    STOP_AND_FIX = "stop_and_fix"
    PENDING = "pending"


class ItemObservation(BaseModel):
    sku: str
    quantity: int = Field(ge=0)
    status: ObservationStatus
    evidence: str


class ExpectedItem(BaseModel):
    sku: str
    quantity: int = Field(ge=0)


class ItemCheck(BaseModel):
    sku: str
    expected_quantity: int
    observed_quantity: int
    status: CheckStatus
    reason: str

class VerificationStatus(str, Enum):
    VERIFIED = "verified"
    UNCERTAIN = "uncertain"
    PENDING = "pending"

class PackVerificationResult(BaseModel):
    expected_items: list[ExpectedItem]
    observed_items: list[ItemObservation]
    checks: list[ItemCheck]
    verification_status: VerificationStatus
    decision: OperationalDecision
    reason: str

class VisionResponse(BaseModel):
    items: list[ItemObservation]
    image_quality: ObservationStatus

class VerificationRequest(BaseModel):
    order_lines: str
    image_path: str