import os
import uuid

from supabase import create_client


supabase = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_SERVICE_ROLE_KEY"],
)


BUCKET = "pack-images"


def upload_pack_image(
    org_id: str,
    filename: str,
    image_bytes: bytes,
    content_type: str,
) -> str:

    extension = os.path.splitext(filename)[1] or ".jpg"

    image_key = (
        f"{org_id}/"
        f"{uuid.uuid4()}"
        f"{extension}"
    )

    supabase.storage.from_(BUCKET).upload(
        path=image_key,
        file=image_bytes,
        file_options={
            "content-type": content_type,
            "upsert": "false",
        },
    )

    return image_key