from app.schemas.pack import (
    CheckStatus,
    ExpectedItem,
    ItemObservation,
    ObservationStatus,
    OperationalDecision,
)
from app.services.verifier import verify_pack
# used for testing the verification logic without relying on the vision model
def test_correct_order():
    expected = [
        ExpectedItem(sku="TSHIRT-BLK", quantity=1),
        ExpectedItem(sku="CAP-BLU", quantity=1),
        ExpectedItem(sku="SOCK-RED", quantity=1),
    ]

    observed = [
        ItemObservation(
            sku="TSHIRT-BLK",
            quantity=1,
            status=ObservationStatus.OBSERVED,
            evidence="Black t-shirt visible.",
        ),
        ItemObservation(
            sku="CAP-BLU",
            quantity=1,
            status=ObservationStatus.OBSERVED,
            evidence="Blue cap visible.",
        ),
        ItemObservation(
            sku="SOCK-RED",
            quantity=1,
            status=ObservationStatus.OBSERVED,
            evidence="Red socks visible.",
        ),
    ]

    result = verify_pack(expected, observed)

    assert result.decision == OperationalDecision.SEAL


def test_missing_item():
    expected = [
        ExpectedItem(sku="TSHIRT-BLK", quantity=1),
        ExpectedItem(sku="CAP-BLU", quantity=1),
    ]

    observed = [
        ItemObservation(
            sku="TSHIRT-BLK",
            quantity=1,
            status=ObservationStatus.OBSERVED,
            evidence="Black t-shirt visible.",
        ),
    ]

    result = verify_pack(expected, observed)

    assert result.decision == OperationalDecision.STOP_AND_FIX

    cap_check = next(
        check for check in result.checks
        if check.sku == "CAP-BLU"
    )

    assert cap_check.status == CheckStatus.FAIL
    assert cap_check.observed_quantity == 0


def test_extra_item():
    expected = [
        ExpectedItem(sku="TSHIRT-BLK", quantity=1),
    ]

    observed = [
        ItemObservation(
            sku="TSHIRT-BLK",
            quantity=1,
            status=ObservationStatus.OBSERVED,
            evidence="Black t-shirt visible.",
        ),
        ItemObservation(
            sku="CAP-BLU",
            quantity=1,
            status=ObservationStatus.OBSERVED,
            evidence="Blue cap visible.",
        ),
    ]

    result = verify_pack(expected, observed)

    assert result.decision == OperationalDecision.STOP_AND_FIX

    cap_check = next(
        check for check in result.checks
        if check.sku == "CAP-BLU"
    )

    assert cap_check.status == CheckStatus.FAIL
    assert cap_check.expected_quantity == 0


def test_wrong_quantity():
    expected = [
        ExpectedItem(sku="TSHIRT-BLK", quantity=2),
    ]

    observed = [
        ItemObservation(
            sku="TSHIRT-BLK",
            quantity=1,
            status=ObservationStatus.OBSERVED,
            evidence="One black t-shirt visible.",
        ),
    ]

    result = verify_pack(expected, observed)

    assert result.decision == OperationalDecision.STOP_AND_FIX

    shirt_check = next(
        check for check in result.checks
        if check.sku == "TSHIRT-BLK"
    )

    assert shirt_check.status == CheckStatus.FAIL
    assert shirt_check.expected_quantity == 2
    assert shirt_check.observed_quantity == 1


def test_uncertain_item():
    expected = [
        ExpectedItem(sku="CAP-BLU", quantity=1),
    ]

    observed = [
        ItemObservation(
            sku="CAP-BLU",
            quantity=1,
            status=ObservationStatus.UNCERTAIN,
            evidence="A cap is visible but its color cannot be determined.",
        ),
    ]

    result = verify_pack(expected, observed)

    assert result.decision == OperationalDecision.STOP_AND_FIX

    cap_check = next(
        check for check in result.checks
        if check.sku == "CAP-BLU"
    )

    assert cap_check.status == CheckStatus.UNCERTAIN