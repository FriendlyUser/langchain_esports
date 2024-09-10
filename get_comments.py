import praw
import requests
import os
import re
import subprocess
import datetime

# Setup your Reddit credentials and user agent
REDDIT_CLIENT_ID = os.environ.get('REDDIT_CLIENT_ID')
REDDIT_CLIENT_SECRET = os.environ.get('REDDIT_CLIENT_SECRET')
reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent='masterfricker/1.0 (by /u/masterfricker)',
)

subreddit = reddit.subreddit('leagueoflegends')
query = 'LCK 2024 Summer Playoffs'

# Set the threshold for post age (2 months ago)
two_months_ago = datetime.datetime.now() - datetime.timedelta(days=60)

# Define the base folder for storing data
base_folder = "packages/rag-gemini-multi-modal/KT_Rolster"
img_folder = f'{base_folder}/downloaded_images'
text_folder = f'{base_folder}/downloaded_text'
comments_folder = f'{base_folder}/downloaded_comments'

# Create necessary directories
for folder in [img_folder, text_folder, comments_folder]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# Set the threshold for post age (1 month ago)
one_month_ago = datetime.datetime.now() - datetime.timedelta(days=30)

def extract_urls_from_markdown(content):
    # Define regex patterns for various image links
    patterns = {
        "Damage Graph": r'\[Damage Graph\]\((https?://i\.imgur\.com/\w+\.\w+)\)',
        "Runes": r'\[Runes\]\((https?://i\.imgur\.com/\w+\.\w+)\)',
        "Player Stats": r'\[Player Stats\]\((https?://i\.imgur\.com/\w+\.\w+)\)',
        "Game Breakdown": r'\[Game Breakdown\]\((https?://i\.imgur\.com/\w+\.\w+)\)',
    }

    # Extract URLs using regex
    extracted_urls = {key: re.findall(pattern, content) for key, pattern in patterns.items()}
    core_urls = extracted_urls["Damage Graph"] + extracted_urls["Game Breakdown"]
    supporting_urls = extracted_urls["Runes"] + extracted_urls["Player Stats"]

    return {"Core": core_urls, "Supporting": supporting_urls}

def download_image_curl(image_url, save_path):
    # Check if image already exists
    if os.path.exists(save_path):
        print(f"Image already exists at {save_path}")
        return
    try:
        # Use curl to download the image
        subprocess.run(['curl', '-o', save_path, image_url], check=True)
        print(f"Image saved to {save_path}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to retrieve image. Error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

def clean_submission(text):
    # remove characters like / to save to a file
    return text.replace("/", "").replace("\n", " ").replace("?", "").replace("|", "")

# add function to validate submission, if not valid skip
# Scan the subreddit with the specified query
for submission in subreddit.search(query, limit=10):  # Adjust the limit as needed
    # Check if the post is at least a month old
    # submission_date = datetime.datetime.fromtimestamp(submission.created_utc)
    submission_date = datetime.datetime.fromtimestamp(submission.created_utc)
    if submission_date < two_months_ago:
        # print(f"Skipping older submission: {submission.title} ({submission_date})")
        continue

    print(f"Title: {submission.title}, URL: {submission.url}")

    # Save submission text if not already saved
    text_file_path = os.path.join(text_folder, f"{clean_submission(submission.title)}.txt")
    if not os.path.exists(text_file_path):
        with open(text_file_path, "w", errors="ignore") as f:
            f.write(submission.selftext)
    else:
        print(f"Text already exists: {submission.title}.txt")

    # Extract and download images
    extracted_urls = extract_urls_from_markdown(submission.selftext)
    for url in extracted_urls["Core"]:
        image_save_path = os.path.join(img_folder, f"{submission.id}_{url.split('/')[-1]}")
        download_image_curl(url, image_save_path)

    # Extract and save comments
    comments_file_path = os.path.join(comments_folder, f"{clean_submission(submission.title)}_comments.txt")
    if not os.path.exists(comments_file_path):
        with open(comments_file_path, "w", errors="ignore") as f:
            submission.comments.replace_more(limit=10)  # Expand all MoreComments objects
            comments = submission.comments.list()
            top_comments = sorted(comments, key=lambda c: c.score, reverse=True)[:100]
            for comment in top_comments:
                if isinstance(comment, praw.models.Comment):
                    f.write(f"{comment.body}\n")
        print(f"Comments saved for submission: {submission.title}")
    else:
        print(f"Comments already exist: {submission.id}_comments.txt")