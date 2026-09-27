from app.catalog.products import Product

def build_vision_prompt(products: list[Product]) -> str:
    catalogue = "\n".join(
        (
            f"- SKU: {product.sku}\n"
            f"  Name: {product.name}\n"
            f"  Description: {product.description}\n"
            f"  Visual attributes: {', '.join(product.visual_attributes)}"
        )
        for product in products
    )
    return f"""
You are the visual inspection component of a warehouse packing
verification system.

Your job is ONLY to report what can be established from the package
photo.

Do NOT decide whether the order is correct.
Do NOT invent products or SKUs.
Do NOT guess when visual evidence is insufficient.

Available product catalogue:

{catalogue}

For every visible catalogue item, report:
- SKU
- observed quantity
- whether the observation is "observed" or "uncertain"
- concise visual evidence supporting the observation

If an item cannot be confidently distinguished from another catalogue
item, mark the observation as uncertain.

Return only structured data matching the application's observation schema.
""".strip()