import gdown

# drive link for ref https://drive.google.com/drive/u/1/folders/1gLSw0RLjBbtaNy0dgnGQDAZOHIgCe-HH
# see https://oracleselixir.com/
# File link
file_url = 'https://drive.google.com/uc?id=1IjIEhLc9n8eLKeY-yh_YigKVWbhgGBsN'
output = 'league_pro_games.csv'  # Change 'downloaded_file.ext' to your desired output file name

# Download file
gdown.download(file_url, output, quiet=False)