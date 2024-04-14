import os
from pathlib import Path
import json
import pypdfium2 as pdfium
from langchain_community.vectorstores import Chroma
from langchain_experimental.open_clip import OpenCLIPEmbeddings
from tqdm import tqdm


def get_images_from_pdf(pdf_path, img_dump_path):
    """
    Extract images from each page of a PDF document and save as JPEG files.

    :param pdf_path: A string representing the path to the PDF file.
    :param img_dump_path: A string representing the path to dummp images.
    """
    pdf = pdfium.PdfDocument(pdf_path)
    n_pages = len(pdf)
    image_paths = []
    for page_number in range(n_pages):
        page = pdf.get_page(page_number)
        bitmap = page.render(scale=1, rotation=0, crop=(0, 0, 0, 0))
        pil_image = bitmap.to_pil()
        pil_image.save(f"{img_dump_path}/img_{page_number + 1}.jpg", format="JPEG")
        image_paths.append(f"{img_dump_path}/img_{page_number + 1}.jpg")

    return image_paths
    

def process_pdfs_in_directory(pdf_dir, output_dir):
    """
    Process all PDF files in the specified directory and extract images.
    
    :param pdf_dir: The directory containing PDF files.
    :param output_dir: The directory where extracted images will be saved.
    """
    pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]
    images_paths = []
    for pdf_file in tqdm(pdf_files, desc="Processing PDFs"):
        pdf_path = os.path.join(pdf_dir, pdf_file)
        new_images_paths = get_images_from_pdf(pdf_path, output_dir)
        images_paths.extend(new_images_paths)

    return images_paths

# Define the directory containing your PDFs and the output directory for images
pdf_dir = Path(__file__).parent / "docs"
img_dump_path = Path(__file__).parent / "docs/extracted_images"

# Ensure the output directory exists
os.makedirs(img_dump_path, exist_ok=True)

# Process all PDF files in the specified directory
pil_images = process_pdfs_in_directory(pdf_dir, img_dump_path)

# print("done")  # noqa: T201
vectorstore = Path(__file__).parent / "chroma_db_multi_modal"
re_vectorstore_path = vectorstore.relative_to(Path.cwd())

# Load embedding function
print("Loading embedding function")  # noqa: T201
embedding = OpenCLIPEmbeddings(model_name="ViT-H-14", checkpoint="laion2b_s32b_b79k")

# Create chroma
vectorstore_mmembd = Chroma(
    collection_name="multi-modal-rag",
    persist_directory=str(Path(__file__).parent / "chroma_db_multi_modal"),
    embedding_function=embedding,
    # modalities=["text", "image"]  # Specify modalities if your version of Chroma supports this

)

# Get image URIs
image_uris = sorted(
    [
        os.path.join(img_dump_path, image_name)
        for image_name in os.listdir(img_dump_path)
        if image_name.endswith(".jpg")
    ]
)

# # Add images
print("Embedding images")  # noqa: T201
vectorstore_mmembd.add_images(uris=image_uris)

