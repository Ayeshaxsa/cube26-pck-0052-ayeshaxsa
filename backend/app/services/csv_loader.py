import csv

from app.services.order_parser import parse_order_lines


def load_orders_from_csv(csv_path: str):
    orders = []

    with open(csv_path, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            orders.append(
                {
                    "record_id": row["record_id"],
                    "unit_id": row["unit_id"],
                    "org_id": row["org_id"],
                    "order_id": row["order_id"],
                    "channel": row["channel"],
                    "expected_items": parse_order_lines(
                        row["order_lines"]
                    ),
                }
            )

    return orders