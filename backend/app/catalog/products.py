from pydantic import BaseModel

class Product(BaseModel):
    sku: str
    name: str
    description: str
    visual_attributes: list[str]

PRODUCT_CATALOG = {
    "TSHIRT-BLK": Product(
        sku="TSHIRT-BLK",
        name="Black T-Shirt",
        description="Black short-sleeve t-shirt",
        visual_attributes=[
            "black",
            "short sleeve",
            "t-shirt",
        ],
    ),
    "CAP-BLU": Product(
        sku="CAP-BLU",
        name="Blue Cap",
        description="Blue baseball cap",
        visual_attributes=[
            "blue",
            "baseball cap",
        ],
    ),
    "SOCK-RED": Product(
        sku="SOCK-RED",
        name="Red Socks",
        description="Red pair of socks",
        visual_attributes=[
            "red",
            "socks",
        ],
    ),
}