import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
engine = create_engine(os.environ["DATABASE_URL"])
with engine.connect() as db:
    db.execute(
        text("""
            select set_config(
                'app.current_org_id',
                'org_demo_alpha',
                false
            )
        """)
    )
    rows = db.execute(
        text("""
            select org_id, sku, name
            from public.products
            order by sku
        """)
    ).fetchall()
    print("ALPHA VIEW:")
    for row in rows:
        print(row)