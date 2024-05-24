import gdown
import os
from datetime import datetime, timedelta
import pandas as pd
import os
import google.generativeai as genai

def is_file_updated_within_24_hours(file_path):
    if os.path.exists(file_path):
        file_mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
        return datetime.now() - file_mod_time < timedelta(hours=24)
    return False


def download_file(output='league_pro_games.csv'):
    
    # drive link for ref https://drive.google.com/drive/u/1/folders/1gLSw0RLjBbtaNy0dgnGQDAZOHIgCe-HH
    # see https://oracleselixir.com/
    # File link
    file_url = 'https://drive.google.com/uc?id=1IjIEhLc9n8eLKeY-yh_YigKVWbhgGBsN'
    # output = 'league_pro_games.csv'  # Change 'downloaded_file.ext' to your desired output file name

    # Download file
    gdown.download(file_url, output, quiet=False)

local_file = 'league_pro_games.csv'
# TODO check if file was last updated within 24 hours, else download again
if not is_file_updated_within_24_hours(local_file):
    download_file(local_file)
else:
    print("File is already up-to-date, skipping download")
# Load the CSV data into a DataFrame.
df = pd.read_csv("league_pro_games.csv", on_bad_lines='warn')

team1 = "KT Rolster"
team2 = "T1"
# Define the teams to filter.
teams = [team1, team2]
# teams_2 = ["BLG", "TES", "G2", "TL"]

# Filter the DataFrame for the specified teams.
filtered_teams_1 = df[df['teamname'].isin(teams)]
# filtered_teams_2 = df[df['teamname'].isin(teams_2)]

GOOGLE_API_KEY=os.environ.get('GOOGLE_API_KEY')

genai.configure(api_key=GOOGLE_API_KEY)
# given the stats analyze the average performance of each player on KT Rolster, what areas of improvement
# could be done for LCK 2024 SPRING, research the depth of players deft and beryl and their adaptability.
model = genai.GenerativeModel(
    model_name='gemini-1.5-flash-latest',
    system_instruction='Act as a league of legends game analyst and a coach given the following given stats for league games. Identify areas of improvement and the chances of success in following games. Analyze all recent games, the performance of each player, determine if the team has a chance against the upcoming team.',
)

# convert filtered_teams_1 to a str
# prompt

games_csv = filtered_teams_1.to_string(index=False)
base_prompt = f"Given the recent games of {team1} and {team2}, analyze the performance of each player and determine if the {team1} has a chance against the upcoming {team2}. The games are as follows:\n\n{games_csv}\n\n"
response = model.generate_content(base_prompt)

output_file = "response.md"
# save response to markdown file
with open("response.md", "w") as f:
    f.write(response.text)
    # added divider line
    f.write('--------------------')


prompt_2 = f"Determine the likelyhood of first blood for {team1} and {team2}. Act as a sports book, estimate the odds and implied probability. - Answer from an educational perspective, give sample odds knowing they may be wrong."
response = model.generate_content(prompt_2)

with open("response.md", "a") as f:
    f.write(response.text)

    f.write('--------------------')

prompt_3 = f"Determine the likelyhood of who will win between {team1} and {team2}. Act as a sports book, estimate the odds and implied probability. - Answer from an educational perspective, give sample odds knowing they may be wrong."
response = model.generate_content(prompt_3)

with open("response.md", "a") as f:
    f.write(response.text)

    f.write('--------------------')

prompt_4 = f"Estimate the number of matches between {team1} and {team2}. Act as a sports book, estimate the odds and implied probability. - Answer from an educational perspective, give sample odds knowing they may be wrong."
response = model.generate_content(prompt_4)

with open("response.md", "a") as f:
    f.write(response.text)

    f.write('--------------------')