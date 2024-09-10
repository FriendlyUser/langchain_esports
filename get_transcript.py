import re
import json
import os
import csv
import os
from youtube_transcript_api import YouTubeTranscriptApi

video_ids = ["vCGUJtj_52k", "eu5aD_kWHmA"]
for video_id in video_ids:
    # todo dont think I need this here
    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
    transcript = transcript_list.find_generated_transcript(['en'])
    transcript_data = transcript.fetch()
    with open(f'packages/rag-gemini-multi-modal/KT_Rolster/transcripts/{video_id}.txt', 'w') as f:
        # extract just the text from the transcript
        f.write(''.join([item['text'] for item in transcript_data]))