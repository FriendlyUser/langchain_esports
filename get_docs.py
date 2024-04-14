import praw
import requests
import os
import dotenv
import os
import re
import time
import subprocess


# Setup your Reddit credentials and user agent
REDDIT_CLIENT_ID = os.environ.get('REDDIT_CLIENT_ID')
REDDIT_CLIENT_SECRET = os.environ.get('REDDIT_CLIENT_SECRET')
reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent='masterfricker/1.0 (by /u/masterfricker)',
)

subreddit = reddit.subreddit('leagueoflegends')  # replace 'your_subreddit' with your target subreddit
base_query = '2024 Post-Match'  # replace 'your_query' with your search query

def extract_urls_from_markdown(content):
    # Define regex patterns for "Damage Graph" and "Runes"
    damage_graph_pattern = r'\[Damage Graph\]\((https?://i\.imgur\.com/\w+\.\w+)\)'
    runes_pattern = r'\[Runes\]\((https?://i\.imgur\.com/\w+\.\w+)\)'

    # Find all URLs in the content
    damage_graph_urls = re.findall(damage_graph_pattern, content)
    runes_urls = re.findall(runes_pattern, content)

    # for the lpl we have two different charts
    stats_pattern = r'\[Player Stats\]\((https?://i\.imgur\.com/\w+\.\w+)\)'
    breakdown_pattern = r'\[Game Breakdown\]\((https?://i\.imgur\.com/\w+\.\w+)\)'

    stats_pattern_urls = re.findall(stats_pattern, content)
    breakdown_pattern_urls = re.findall(breakdown_pattern, content)

    core_urls = damage_graph_urls + breakdown_pattern_urls
    supporting_urls = runes_urls + stats_pattern_urls
    extracted_urls = {
        "Core": core_urls,
        "Supporting": supporting_urls
    }
    return extracted_urls

def download_image_requests(image_url, save_path):
    try:
        # guessing there is a default header or something
        # to indicate requests should be blocked
        response = requests.get(image_url)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            print(f"Image saved to {save_path}")
        else:
            print(f"Failed to retrieve image. Status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error downloading image: {e}")


def download_image_curl(image_url, save_path):
    # check if save_path has image, if so don't download
    if os.path.exists(save_path):
        print(f"Image already exists at {save_path}")
        return
    try:
        # Use curl to download the image
        subprocess.run(['curl', '-o', save_path, image_url], check=True)
        print(f"Image saved to {save_path}")
    except subprocess.CalledProcessError as e:
        # If curl fails, it will raise a CalledProcessError
        print(f"Failed to retrieve image. Error: {e}")
    except Exception as e:
        # Catch-all for any other exceptions
        print(f"An error occurred: {e}")


regions = ["LCK", "LPL", "LEC"]
scrapped_games = []
for region in regions:
    base_folder = "packages/rag-gemini-multi-modal"
    output_folder = f'{base_folder}/{region}'
    img_folder = f'{output_folder}/downloaded_images'

    text_folder = f'{output_folder}/downloaded_text'
    
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    if not os.path.exists(img_folder):
        os.makedirs(img_folder)

    if not os.path.exists(text_folder):
        os.makedirs(text_folder)

    query = f'{base_query} {region}'
    # Scan the subreddit
    for submission in subreddit.search(query, limit=100):  # adjust the limit as needed
        print(f"Title: {submission.title}, URL: {submission.url}")
        # make sure 2024 is in the name
        if '2024' not in submission.title:
            print("Skipping", submission.title)
            continue

        # if region not in submission.selftext:
        # search for region in submission.selftext
        region_search = re.search(region, submission.selftext)
        if region_search is None:
            print("Skipping", submission.title)
            continue
        # if image path exists print message and skip
        # if os.path.exists(os.path.join(save_folder, submission.url.split('/')[-1])):
        #     print(f"Image already exists: {submission.url.split('/')[-1]}")
        #     continue
        # if hasattr(submission, 'is_gallery') and submission.is_gallery:
        #     for item_id in submission.gallery_data['items']:
        #         image_url = submission.media_metadata[item_id['media_id']]['s']['u']
        #         image_path = os.path.join(save_folder, f"{item_id['media_id']}.jpg")
        #         with open(image_path, 'wb') as f:
        #             f.write(requests.get(image_url).content)
        # elif 'i.redd.it' in submission.url:
        #     image_path = os.path.join(save_folder, submission.url.split('/')[-1])
        #     with open(image_path, 'wb') as f:
        #         f.write(requests.get(submission.url).content)
        # check if text file is present
        # output submission text to file
        if os.path.exists(os.path.join(text_folder, f"{submission.id}.txt")):
            print(f"Text already exists: {submission.id}.txt")
        else:
            with open(os.path.join(text_folder, f"{submission.id}.txt"), "w", errors="ignore") as f:
                f.write(submission.selftext)
        extracted_urls = extract_urls_from_markdown(submission.selftext)

        # Download images
        core_urls = extracted_urls["Core"]
        runes_urls = extracted_urls["Supporting"]
        print(f"Downloading images from URLs: {core_urls}")
        for url in core_urls:
            base_image_name = url.split('/')[-1]
            file_name_adjusted = f"{img_folder}/{submission.id}_{url.split('/')[-1]}"
            download_image_curl(url, file_name_adjusted)

    scrapped_games.append(submission.title)

