import uuid

from sqlalchemy import text

from app.db.database import SessionLocal


def save_capture(
    org_id: str,
    order_id: str,
    image_key: str,
):
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

        capture_id = uuid.uuid4()

        db.execute(
            text(
                """
                insert into public.pack_captures
                (id, org_id, order_id, image_key, status)
                values
                (:id, :org_id, :order_id, :image_key, 'captured')
                """
            ),
            {
                "id": capture_id,
                "org_id": org_id,
                "order_id": order_id,
                "image_key": image_key,
            },
        )

        db.commit()

        return capture_id

    finally:
        db.close()


def save_result(
    org_id: str,
    capture_id,
    verdict: str,
    result: dict,
):
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

        db.execute(
            text(
                """
                insert into public.verification_results
                (id, org_id, capture_id, verdict, result)
                values
                (:id, :org_id, :capture_id, :verdict, CAST(:result AS jsonb)
)
                """
            ),
            {
                "id": uuid.uuid4(),
                "org_id": org_id,
                "capture_id": capture_id,
                "verdict": verdict,
                "result": __import__("json").dumps(result),
            },
        )

        db.commit()

    finally:
        db.close()