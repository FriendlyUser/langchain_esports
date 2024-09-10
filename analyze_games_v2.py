import os
import json
from openai import OpenAI

# Define file paths
transcripts_path = "packages/rag-gemini-multi-modal/KT_Rolster/transcripts"
comments_path = "packages/rag-gemini-multi-modal/KT_Rolster/downloaded_comments"
output_path = "packages/KT_Rolster/Analyze"
roster_path = "packages/rag-gemini-multi-modal/KT_Rolster/roster"

# Ensure the output directory exists
os.makedirs(output_path, exist_ok=True)

# List of files to be processed
transcript_files = [
    # os.path.join(transcripts_path, "kt_vs_t1.json"),
    # os.path.join(transcripts_path, "dplus_kia_vs_fearx.json")
]

roster_files = [
    os.path.join(roster_path, "fearx.txt"),
    os.path.join(roster_path, "kt_roster.txt")
]
comment_files = [
    os.path.join(comments_path, "T1 vs KT Rolster  LCK 2024 Summer Playoffs - Round 1 Match 2  Unofficial Live Discussion_comments.txt"),
    os.path.join(comments_path, "Dplus KIA vs. BNK FearX  LCK 2024 Summer Playoffs - Round 1  Post-Match Discussion_comments.txt")
]

# Function to read JSON and text files, convert JSON to text, and format with titles and dividers
def read_files():
    data = ""
    
    # Process JSON files
    # for file_path in transcript_files:
    #     with open(file_path, 'r') as file:
    #         json_data = json.load(file)
    #         # Add title and dividers
    #         data += f"# File: {os.path.basename(file_path)}\n"
    #         data += "-" * 40 + "\n"
    #         data += json.dumps(json_data, indent=2) + "\n\n"  # Convert JSON to nicely formatted text
    #         data += "-" * 40 + "\n\n"

    for file_path in roster_files:
        with open(file_path, 'r', errors='replace') as file:
            # Add title and dividers
            data += f"# File: {os.path.basename(file_path)}\n"
            data += "-" * 40 + "\n"
            data += file.read() + "\n\n"  # Convert JSON to nicely formatted text
            data += "-" * 40 + "\n\n"
    # Process text files
    for file_path in comment_files:
        with open(file_path, 'r', errors='replace') as file:
            # Add title and dividers
            data += f"# File: {os.path.basename(file_path)}\n"
            data += "-" * 40 + "\n"
            data += file.read() + "\n\n"
            data += "-" * 40 + "\n\n"
    
    return data

# Read and combine the data from the files
combined_data = read_files()

# Set up the OpenAI client
token = os.environ["GITHUB_TOKEN"]
endpoint = "https://models.inference.ai.azure.com"
model_name = "gpt-4o"

client = OpenAI(
    base_url=endpoint,
    api_key=token,
)

# Function to interact with OpenAI model
def analyze_data(data, iterations, output_path):
    # save data to file
    output_file = os.path.join(output_path, "KT_FearX_Analysis.md")
    with open(output_file, 'w', errors='ignore') as file:
        file.write(data)

    system_prompt = """Analyze the following data to predict the matchup between KT Rolster and FearX: focus on player performance, team strength and playmaking.
    In a best of 5 focus on the ability of players or the team to make decision that lead to their vicotry."""

    user_prompt = f"""Analyze the following data involving lck playoff games, the 
    team roster and reddit comments to predict the matchup between KT Rolster and FearX. 
    Focus on accuracy and the current team roster: \n\n{data}"""
    for i in range(1, iterations + 1):
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            model=model_name,
            temperature=1.0,
            top_p=1.0
        )
        
        # Get the content from the response
        analysis_result = response.choices[0].message.content
        # utf-8 analysis result
        # Save the analysis result to a markdown file
        output_file = os.path.join(output_path, f"KT_FearX_Analysis_Iteration_{i}.md")
        with open(output_file, 'w', encoding='utf-8', errors='ignore') as file:
            file.write(f"# Analysis Iteration {i}\n\n")
            file.write(analysis_result)

        print(f"Saved analysis iteration {i} to {output_file}")

# Perform analysis with 3 or 4 iterations
analyze_data(combined_data, iterations=3, output_path=output_path)
