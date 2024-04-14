import os
from pathlib import Path
import json
import pypdfium2 as pdfium
from langchain_community.vectorstores import Chroma
from langchain_experimental.open_clip import OpenCLIPEmbeddings
from tqdm import tqdm

regions = ["LCK", "LPL", "LEC"]
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

for region in regions:
    print(region)
# Define the directory containing your PDFs and the output directory for images
    region_dir = Path(__file__).parent / region
    img_path = region_dir / "downloaded_images"
    text_path = region_dir / "downloaded_text"



    # Get image URIs
    image_uris = sorted(
        [
            os.path.join(img_path, image_name)
            for image_name in os.listdir(img_path)
            if image_name.endswith(".png")
        ]
    )

    # # Add images
    print("Embedding images for region: ", region)  # noqa: T201
    vectorstore_mmembd.add_images(uris=image_uris)

    # add text from folder
    # print("Embedding text for region: ", region)  # noqa: T201
    # text_uris = sorted(
    #     [
    #         os.path.join(text_path, text_name)
    #         for text_name in os.listdir(text_path)
    #         if text_name.endswith(".txt")
    #     ]
    # )
    # vectorstore_mmembd.add_texts(text_uris)

print("done")