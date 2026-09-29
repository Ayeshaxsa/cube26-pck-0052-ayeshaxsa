from sqlalchemy import text

from app.db.database import SessionLocal
from app.catalog.products import Product


def get_catalogue(org_id: str) -> list[Product]:
    db = SessionLocal()

    try:
        db.execute(
            text(
                """
                select set_config(
                    'app.current_org_id',
                    :org_id,
                    true
                )
                """
            ),
            {"org_id": org_id},
        )

        rows = db.execute(
            text(
                """
                select
                    sku,
                    name,
                    description,
                    visual_attributes
                from public.products
                where org_id = :org_id
                order by sku
                """
            ),
            {"org_id": org_id},
        ).mappings().all()

        return [
            Product(
                sku=row["sku"],
                name=row["name"],
                description=row["description"] or "",
                visual_attributes=row["visual_attributes"] or [],
            )
            for row in rows
        ]

    finally:
        db.close()