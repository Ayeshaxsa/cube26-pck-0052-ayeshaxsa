from app.catalog.products import PRODUCT_CATALOG
from app.services.vision.openai_vision import inspect_package_image


image_path = "fixtures/correct_001.jpg"

products = list(PRODUCT_CATALOG.values())

result = inspect_package_image(
    image_path=image_path,
    catalogue_products=products,
)

print("\n=== VISION RESULT ===")
print(result.model_dump_json(indent=2))