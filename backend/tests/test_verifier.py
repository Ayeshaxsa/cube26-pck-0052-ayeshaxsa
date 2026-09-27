from app.schemas.pack import (
    ExpectedItem,
    ItemObservation,
    ObservationStatus,
    OperationalDecision,
    CheckStatus,
)
from app.services.verifier import verify_pack

def test_missing_and_extra_items():
    expected = [
        ExpectedItem(sku="TSHIRT-BLK", quantity=3),
        ExpectedItem(sku="CAP-BLU", quantity=1),
    ]
    observed = [
        ItemObservation(
            sku="TSHIRT-BLK",
            quantity=2,
            status=ObservationStatus.OBSERVED,
            evidence="Two black t-shirts are visible.",
        ),
        ItemObservation(
            sku="CAP-BLU",
            quantity=1,
            status=ObservationStatus.OBSERVED,
            evidence="One blue cap is visible.",
        ),
        ItemObservation(
            sku="SOCK-RED",
            quantity=1,
            status=ObservationStatus.OBSERVED,
            evidence="One red sock is visible.",
        ),
    ]

    result = verify_pack(expected, observed)
    assert result.decision == OperationalDecision.STOP_AND_FIX

    tshirt_check = next(
        check for check in result.checks
        if check.sku == "TSHIRT-BLK"
    )

    assert tshirt_check.expected_quantity == 3
    assert tshirt_check.observed_quantity == 2
    assert tshirt_check.status == CheckStatus.FAIL

    cap_check = next(
        check for check in result.checks
        if check.sku == "CAP-BLU"
    )

    assert cap_check.status == CheckStatus.PASS

    sock_check = next(
        check for check in result.checks
        if check.sku == "SOCK-RED"
    )

    assert sock_check.status == CheckStatus.FAIL
    assert "extra" in sock_check.reason.lower()

def test_uncertain_observation_requires_review():
    expected = [
        ExpectedItem(sku="CAP-BLU", quantity=1),
    ]

    observed = [
        ItemObservation(
            sku="CAP-BLU",
            quantity=1,
            status=ObservationStatus.UNCERTAIN,
            evidence="A cap is visible, but the color cannot be determined.",
        ),
    ]

    result = verify_pack(expected, observed)

    assert result.decision == OperationalDecision.STOP_AND_FIX

    cap_check = next(
        check for check in result.checks
        if check.sku == "CAP-BLU"
    )

    assert cap_check.status == CheckStatus.UNCERTAIN