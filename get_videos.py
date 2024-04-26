from googleapiclient.discovery import build
import re
import json
import os
import csv
import os
from youtube_transcript_api import YouTubeTranscriptApi

def extract_teams(input_str):
    # Split the string up to the first "|"
    first_part = input_str.split("|")[0].strip()
    
    # Remove the word "vs" or "vs." and trim whitespace
    teams = first_part.replace("vs.", "").replace("vs", "").strip()
    
    # Split by any remaining whitespace to get individual team names
    team_names = teams.split()
    
    # Return the two team names as a tuple
    return tuple(team_names)

# download the transcript, then apply the llm analysis to it, cut into early game
# mid game and late game
# def download_file_from_private_repo(file_url, access_token, destination_path):
#     headers = {'Authorization': f'token {access_token}'}
#     response = requests.get(file_url, headers=headers)

#     if response.status_code == 200:
#         with open(destination_path, 'w') as file:
#             file.write(response.text)
#         print("File downloaded successfully.")
#     else:
#         print(f"Failed to download file: {response.status_code}")

# # Example usage
# ACCESS_TOKEN = 'your_github_access_token_here'
# FILE_URL = 'https://raw.githubusercontent.com/username/repository/branch/path/to/your/file.txt'
# DESTINATION_PATH = 'path/to/save/your/file.txt'

# function that I could use for the deno deploy client side
def find_interview_and_condense(youtube_data):
    # Calculate the 80% index mark to determine if the 'interview' mention is past this point.
    eighty_percent_mark = int(len(youtube_data) * 0.8)
    
    # Iterate over the youtube data to find the first index of 'interview' mention.
    for index, entry in enumerate(youtube_data):
        if 'interview' in entry['text'].lower():
            # If the 'interview' mention is past the 80% mark of the entries, return the condensed array.
            if index >= eighty_percent_mark:
                return youtube_data[index:], index
            break

developerKey = os.environ.get('YOUTUBE_API_KEY')
# Replace 'YOUR_API_KEY' with your actual API key
youtube = build('youtube', 'v3', developerKey=developerKey)

# Step 2: Find the channel ID for LCK Global
channel_response = youtube.search().list(
    q='LCK Global',
    type='channel',
    part='id,snippet',
    maxResults=1
).execute()

channel_id = channel_response['items'][0]['id']['channelId']

pattern = r"^(?!.*Game \d+).*vs.*\|.*Highlight"
# Step 3: Search for highlight videos in the LCK Global channel
videos_response = youtube.search().list(
    part='id,snippet',
    channelId=channel_id,
    q='geng vs hle 2024 highlight 03.06',
    type='video',
    maxResults=1  # You can adjust this number based on your needs
).execute()


csv_file_path = 'videos_info_2.csv'
existing_video_ids = set()

try:
    with open(csv_file_path, 'r', newline='', encoding='utf-8') as csvfile:
        csvreader = csv.DictReader(csvfile)
        for row in csvreader:
            existing_video_ids.add(row['videoID'])
except FileNotFoundError:
    print("CSV file not found, will be created.")

matched_items = []
for video in videos_response['items']:
    video_id = video['id']['videoId']
    video_title = video['snippet']['title']
    
    # Check if the videoID is already in the CSV, skip if it exists
    if video_id not in existing_video_ids:
        if re.match(pattern, video_title):  # Assuming `pattern` is previously defined
            matched_items.append(video)

# make a simple csv that contains, title, extract team t1,t2 from title and then save as pandas dataframe
# for video in matched_items:
#     video_id = video['id']['videoId']
#     # todo dont think I need this here
#     transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
#     transcript = transcript_list.find_generated_transcript(['en'])
#     transcript_data = transcript.fetch()
#     with open(f'data/{video_id}.json', 'w') as f:
#         json.dump(transcript_data, f)

# Open the CSV file in append mode ('a') so we don't overwrite existing data
with open(csv_file_path, 'a', newline='', encoding='utf-8') as csvfile:
    # Define the CSV writer
    csvwriter = csv.writer(csvfile)
    
    # Check if the file is empty to write headers
    if csvfile.tell() == 0:
        csvwriter.writerow(['team1', 'team2', 'videoTitle', 'videoID', 'uploadDate'])
    
    # Loop through each video item
    for video in matched_items:
        video_id = video['id']['videoId']
        video_title = video['snippet']['title']
        upload_date = video['snippet']['publishedAt']  # Assuming this is where upload date is
        
        # Extract team names from the video title (customize this based on your video title structure)
        team_1, team_2 = extract_teams(video_title)
        
        # Write the data to the CSV
        csvwriter.writerow([team_1, team_2, video_title, video_id, upload_date])
    else:
        print("no new matches found")