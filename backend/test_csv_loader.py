from app.services.csv_loader import load_orders_from_csv

orders = load_orders_from_csv("data/pack_sample.csv")
print(f"Loaded {len(orders)} orders")
for order in orders[:3]:
    print("\nOrder:", order["order_id"])
    print("Organization:", order["org_id"])
    print("Expected items:", order["expected_items"])