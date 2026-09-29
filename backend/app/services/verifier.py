from app.schemas.pack import (
    CheckStatus,
    ExpectedItem,
    ItemCheck,
    ItemObservation,
    OperationalDecision,
    PackVerificationResult,
    VerificationStatus,
)

def verify_pack(
    expected_items: list[ExpectedItem],
    observed_items: list[ItemObservation],
) -> PackVerificationResult:
    expected_by_sku = {
        item.sku: item.quantity
        for item in expected_items
    }

    observed_by_sku = {
        item.sku: item.quantity
        for item in observed_items
    }

    checks: list[ItemCheck] = []

    all_skus = set(expected_by_sku) | set(observed_by_sku)
    # union of expected and observed SKUs to ensure we check all items

    for sku in sorted(all_skus):
        expected_quantity = expected_by_sku.get(sku, 0)
        observed_quantity = observed_by_sku.get(sku, 0)

        observed_item = next(
            (
                item
                for item in observed_items
                if item.sku == sku
            ),
            None,
        )

        if observed_item and observed_item.status.value == "uncertain":
            status = CheckStatus.UNCERTAIN
            reason = "The item could not be verified with sufficient visual evidence."

        elif expected_quantity == observed_quantity:
            status = CheckStatus.PASS
            reason = "Expected and observed quantities match."

        else:
            status = CheckStatus.FAIL

            if expected_quantity == 0:
                reason = "Unexpected extra item detected."

            elif observed_quantity == 0:
                reason = "Expected item is missing."

            else:
                reason = (
                    f"Quantity mismatch: expected {expected_quantity}, "
                    f"observed {observed_quantity}."
                )

        checks.append(
            ItemCheck(
                sku=sku,
                expected_quantity=expected_quantity,
                observed_quantity=observed_quantity,
                status=status,
                reason=reason,
            )
        )

    has_uncertain = any(
        check.status == CheckStatus.UNCERTAIN
        for check in checks
    )

    has_failure = any(
        check.status == CheckStatus.FAIL
        for check in checks
    )

    if has_uncertain:
        verification_status = VerificationStatus.UNCERTAIN
        decision = OperationalDecision.STOP_AND_FIX
        reason = "Verification is uncertain and requires human review."

    elif has_failure:
        verification_status = VerificationStatus.VERIFIED
        decision = OperationalDecision.STOP_AND_FIX
        reason = "One or more packing checks failed."

    else:
        verification_status = VerificationStatus.VERIFIED
        decision = OperationalDecision.SEAL
        reason = "All expected items and quantities were verified."

    return PackVerificationResult(
        expected_items=expected_items,
        observed_items=observed_items,
        checks=checks,
        verification_status=verification_status,
        decision=decision,
        reason=reason,
    )