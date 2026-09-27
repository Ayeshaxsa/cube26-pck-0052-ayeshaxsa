from app.catalog.products import PRODUCT_CATALOG
from app.schemas.pack import ExpectedItem
from app.services.order_parser import parse_order_lines
from app.services.verifier import verify_pack
from app.services.vision.openai_vision import inspect_package_image


# 1. The customer's order
order = parse_order_lines(
    "TSHIRT-BLK:1;CAP-BLU:1;SOCK-RED:1"
)

# 2. Inspect the actual package photo
vision_result = inspect_package_image(
    image_path="fixtures/correct_001.jpg",
    catalogue_products=list(PRODUCT_CATALOG.values()),
)

# 3. Verify observed items against the order
verification = verify_pack(
    expected_items=order,
    observed_items=vision_result.items,
)

# 4. Print the final operational result
print("\n=== FINAL PACK VERIFICATION ===")

print("\nExpected:")
for item in verification.expected_items:
    print(f"  {item.sku}: {item.quantity}")

print("\nObserved:")
for item in verification.observed_items:
    print(f"  {item.sku}: {item.quantity} ({item.status.value})")

print("\nChecks:")
for check in verification.checks:
    print(
        f"  {check.sku}: "
        f"expected={check.expected_quantity}, "
        f"observed={check.observed_quantity}, "
        f"status={check.status.value}"
    )

print("\nDecision:")
print(f"  {verification.decision.value}")

print("\nReason:")
print(f"  {verification.reason}")