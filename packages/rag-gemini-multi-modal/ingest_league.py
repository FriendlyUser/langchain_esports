import os
from pathlib import Path
import json
import re
# import pypdfium2 as pdfium
from langchain_community.vectorstores import Chroma
from langchain_experimental.open_clip import OpenCLIPEmbeddings
from tqdm import tqdm

# DROP LPL from analysis, scorecards are too messy for my ingestion.
# regions = ["LCK", "LPL", "LEC"]
regions = ["LPL"]

region_teams = {
    "LPL": [
        "TES",
        "BLG"
    ]
}
vectorstore = Path(__file__).parent / "chroma_db_multi_modal"
re_vectorstore_path = vectorstore.relative_to(Path.cwd())


# Load embedding function

embedding = None

vectorstore_mmembd = None
# Create chroma


for region in regions:
    print(region)
    # Define the directory containing your PDFs and the output directory for images
    region_dir = Path(__file__).parent / region
    img_path = region_dir / "downloaded_images"
    text_path = region_dir / "downloaded_text"


    # add text from folder
    print("Embedding text for region: ", region)  # noqa: T201
    text_uris = sorted(
        [
            os.path.join(text_path, text_name)
            for text_name in os.listdir(text_path)
            if text_name.endswith(".txt")
        ]
    )

    good_text_files = []
    teams_in_region = region_teams[region]
    # Filter and process only those text files that mention any of the teams in teams_in_region
    for text_uri in text_uris:
        with open(text_uri, 'r', encoding='utf-8') as file:
            content = file.read()
            # Check if any team name from the list is in the text content
            if any(team in content for team in teams_in_region):
                # This is where you would handle the text content that matches the condition
                print(f"Processing text file {text_uri} as it mentions one of the teams.")
                # Add your specific text processing logic here
                good_text_files.append(text_uri)

    filtered_texts = []
    
    # Define lines to exclude
    exclude_markers = [
        "[Official page]",
        "Leaguepedia",
        # "###MATCH 1:", "###MATCH 2:", "###MATCH 3:", "###MATCH 4:", "###MATCH 5:",
        "https://i.imgur.com",
        "This thread was created by the Post-Match Team"
    ]

    # Loop through each file path
    for uri in good_text_files:
        with open(uri, 'r', encoding='utf-8') as file:
            filtered_lines = []
            for line in file:
                # Check if line contains any exclusion marker
                if not any(marker in line for marker in exclude_markers):
                    # Remove Markdown characters
                    clean_line = line.replace("#", "").replace("[", "").replace("]", "").strip()
                    if clean_line:  # Ensure line is not empty after cleaning
                        filtered_lines.append(clean_line)

            # Combine the filtered lines into a single string
            filtered_text = "\n".join(filtered_lines)
            filtered_texts.append(filtered_text)

    # print(filtered_texts)
    # 

    # Get image URIs
    image_uris = sorted(
        [
            os.path.join(img_path, image_name)
            for image_name in os.listdir(img_path)
            if image_name.endswith(".png")
        ]
    )
    valid_image_uris = []
    # iterate through each text file like 19f9tlv.txt,
    # extract prefix from 19f9tlv.txt, 19f9tlv
    # use extract matching images from image_uris like
    # 19f9tlv_gQrymZB.png, 19f9tlv_QrymZB.png
    # Add images
    for text_uri in good_text_files:
 
        # Extract prefix from filename (e.g., '19f9tlv' from '19f9tlv.txt')
        # get basename from text_uri 
        text_basename = os.path.basename(text_uri)
        prefix = text_basename.split(".")[0]

        # Append matching image URIs to valid_image_uris list
        for uri in image_uris:
            # split uri by _
            image_base_name = os.path.basename(uri)
            image_prefix = image_base_name.split("_")[0]
            if image_prefix == prefix:
                valid_image_uris.append(uri)

    print("Embedding images for region: ", region)  # noqa: T201
    # print(valid_image_uris)
    if embedding is None:
        embedding = OpenCLIPEmbeddings(model_name="ViT-H-14", checkpoint="laion2b_s32b_b79k")

    if vectorstore_mmembd is None:
        vectorstore_mmembd = Chroma(
            collection_name="multi-modal-rag",
            persist_directory=str(Path(__file__).parent / "chroma_db_multi_modal"),
            embedding_function=embedding,
            # modalities=["text", "image"]  # Specify modalities if your version of Chroma supports this
        )
    vectorstore_mmembd.add_texts(filtered_texts)
    vectorstore_mmembd.add_images(uris=valid_image_uris)


print("done")