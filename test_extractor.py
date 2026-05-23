from pdf_extractor import extract_images_from_pdf

images = extract_images_from_pdf(
    pdf_path=r"C:\Users\bit\Desktop\statistics.pdf",
    save_dir="extracted_images"
)

for img in images:
    print(f"Page {img['page']} | Image {img['index']} | Size: {img['width']}x{img['height']} | Format: {img['format']}")