import base64
import io
from PIL import Image
from groq import Groq

client = Groq(api_key="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")

async def generate_answer(prompt: str) -> str:
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        max_tokens=1000
    )
    return response.choices[0].message.content


async def explain_image(image: Image.Image, extra_prompt: str = "") -> str:
    # convert PIL image to base64
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    image_bytes = buffer.getvalue()
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    prompt = extra_prompt if extra_prompt else "Describe this image in detail. List all objects, text, charts, or diagrams you can see."

    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_b64}"
                        }
                    }
                ]
            }
        ],
        temperature=0.2,
        max_tokens=1000
    )
    return response.choices[0].message.content