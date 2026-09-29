import os
import tempfile

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.services.catalog_service import get_catalogue
from app.schemas.pack import OperationalDecision
from app.services.order_parser import parse_order_lines
from app.services.persistence import save_capture, save_result
from app.services.verifier import verify_pack
from app.services.vision.openai_vision import inspect_package_image
from app.services.storage import upload_pack_image


app = FastAPI(
    title="Pack Manager",
    description="AI-powered outbound packing verification",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "pack-manager",
    }


@app.post("/verify")
async def verify_package(
    org_id: str = Form(...),
    order_id: str = Form(...),
    order_lines: str = Form(...),
    image: UploadFile = File(...),
):
    # Read the uploaded image once.
    image_bytes = await image.read()

    # Determine the file extension for the temporary local file.
    file_extension = os.path.splitext(
        image.filename or ""
    )[1] or ".jpg"

    # Upload the original image to storage.
    image_key = upload_pack_image(
        org_id=org_id,
        filename=image.filename or "package.jpg",
        image_bytes=image_bytes,
        content_type=image.content_type or "image/jpeg",
    )

    # Keep a local temporary copy because the vision service
    # currently expects a local file path.
    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=file_extension,
    ) as temp_file:
        temp_file.write(image_bytes)
        image_path = temp_file.name

    # Create the capture record using the storage key.
    capture_id = save_capture(
        org_id=org_id,
        order_id=order_id,
        image_key=image_key,
    )

    try:
        # Parse the expected order items.
        expected_items = parse_order_lines(order_lines)

        # Load the organisation's product catalogue.
        catalogue = get_catalogue(org_id)

        # Inspect the package image using the local temporary file.
        vision_result = inspect_package_image(
            image_path=image_path,
            catalogue_products=catalogue,
        )

        # Compare expected items with observed items.
        verification = verify_pack(
            expected_items=expected_items,
            observed_items=vision_result.items,
        )

        result = verification.model_dump()

        # Persist the verification result.
        save_result(
            org_id=org_id,
            capture_id=capture_id,
            verdict=verification.decision.value,
            result=result,
        )

        return {
            "capture_id": str(capture_id),
            **result,
        }

    except Exception as exc:
        # If anything fails, mark the capture as pending
        # so that it can be reviewed by an operator.
        pending_result = {
            "decision": OperationalDecision.PENDING.value,
            "reason": (
                "Vision verification could not be completed. "
                "Capture requires operator review."
            ),
            "error_type": type(exc).__name__,
        }

        save_result(
            org_id=org_id,
            capture_id=capture_id,
            verdict=OperationalDecision.PENDING.value,
            result=pending_result,
        )

        return {
            "capture_id": str(capture_id),
            **pending_result,
        }

    finally:
        # Remove the temporary local image after processing.
        if os.path.exists(image_path):
            os.remove(image_path)
