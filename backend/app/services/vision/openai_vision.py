import base64
import os

from dotenv import load_dotenv
from openai import OpenAI

from app.schemas.pack import VisionResponse
from app.services.vision.prompt import build_vision_prompt

load_dotenv()

client = OpenAI()

MODEL = os.environ["OPENAI_VISION_MODEL"]


def encode_image(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def inspect_package_image(
    image_path: str,
    catalogue_products,
) -> VisionResponse:

    image_base64 = encode_image(image_path)

    prompt = build_vision_prompt(catalogue_products)

    response = client.responses.parse(
        model=MODEL,
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": prompt,
                    },
                    {
                        "type": "input_image",
                        "image_url": (
                            f"data:image/jpeg;base64,{image_base64}"
                        ),
                    },
                ],
            }
        ],
        text_format=VisionResponse,
    )

    if response.output_parsed is None:
        raise RuntimeError(
            "Vision model returned no structured result."
        )

    return response.output_parsed