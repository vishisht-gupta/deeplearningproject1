import fitz
from PIL import Image
import io
import os

def extract_images_from_pdf(pdf_path: str, save_dir: str = None) -> list:
    doc = fitz.open(pdf_path)
    images = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # render page as image (300 DPI for good quality)
        mat = fitz.Matrix(300/72, 300/72)
        pix = page.get_pixmap(matrix=mat)
        image_bytes = pix.tobytes("png")
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        image_info = {
            "page": page_num + 1,
            "index": 1,
            "format": "png",
            "width": image.width,
            "height": image.height,
            "image": image
        }

        # optionally save to disk
        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
            save_path = os.path.join(save_dir, f"page{page_num+1}.png")
            image.save(save_path)
            image_info["saved_path"] = save_path

        images.append(image_info)

    doc.close()
    print(f"Total pages extracted as images: {len(images)}")
    return images