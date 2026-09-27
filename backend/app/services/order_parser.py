from app.schemas.pack import ExpectedItem


def parse_order_lines(order_lines: str) -> list[ExpectedItem]:
    if not order_lines.strip():
        return []

    items = []

    for entry in order_lines.split(";"):
        sku, quantity = entry.split(":")

        items.append(
            ExpectedItem(
                sku=sku.strip(),
                quantity=int(quantity),
            )
        )

    return items