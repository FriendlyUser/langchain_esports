import praw
import requests
import os

# Setup your Reddit credentials and user agent
# It's highly recommended to use environment variables for credentials
REDDIT_CLIENT_ID = os.environ.get('REDDIT_CLIENT_ID')
REDDIT_CLIENT_SECRET = os.environ.get('REDDIT_CLIENT_SECRET')

# Ensure credentials are set
if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
    raise ValueError("REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET environment variables must be set.")

reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent='masterfricker/1.0 (by /u/masterfricker)',
)

# New Reddit Search Tool
All right, let's refine the search_reddit_posts function to not save images to disk, and instead return an array of the top comments and submission details directly. This will make the output immediately consumable by an LLM without disk I/O for images.

Here's the updated search_reddit_posts function and the necessary adjustments:

Python

import praw
import requests
import os
import re
import subprocess
import datetime
import json
import uuid # Import uuid for unique filenames if needed

# Setup your Reddit credentials and user agent
# It's highly recommended to use environment variables for credentials
REDDIT_CLIENT_ID = os.environ.get('REDDIT_CLIENT_ID')
REDDIT_CLIENT_SECRET = os.environ.get('REDDIT_CLIENT_SECRET')

# Ensure credentials are set
if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
    raise ValueError("REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET environment variables must be set.")

reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent='masterfricker/1.0 (by /u/masterfricker)',
)

# New Reddit Search Tool - MODIFIED
def search_reddit_posts(query: str, subreddit_name: str = 'all', limit: int = 10, time_filter: str = 'month') -> str:
    """
    Searches Reddit for posts matching a query and returns relevant submission details and top comments.
    Images are NOT downloaded.

    Args:
        query (str): The search query.
        subreddit_name (str): The subreddit to search in (e.g., 'leagueoflegends', 'all').
        limit (int): The maximum number of submissions to retrieve.
        time_filter (str): Filter submissions by time (e.g., 'hour', 'day', 'week', 'month', 'year', 'all').

    Returns:
        str: A JSON string containing a list of dictionaries, where each dictionary
             represents a submission with its title, URL, selftext, and a list of top comments.
             Returns an empty list as JSON if no data was found or an error message.
    """
    try:
        sub = reddit.subreddit(subreddit_name)
        
        results_data = []

        for submission in sub.search(query, limit=limit, time_filter=time_filter):
            submission_date = datetime.datetime.fromtimestamp(submission.created_utc)

            print(f"Processing: Title: {submission.title}")

            # Prepare comments
            comments_list = []
            submission.comments.replace_more(limit=10)  # Expand MoreComments objects
            comments = submission.comments.list()
            top_comments = sorted(comments, key=lambda c: c.score, reverse=True)[:100] # Get top 100 comments
            for comment in top_comments:
                if isinstance(comment, praw.models.Comment):
                    comments_list.append(comment.body)
            
            # Prepare submission data
            submission_data = {
                "title": submission.title,
                "url": submission.url,
                "selftext": submission.selftext,
                "created_utc": submission_date.isoformat(), # ISO format for easy parsing
                "score": submission.score,
                "num_comments": submission.num_comments,
                "top_comments": comments_list
            }
            results_data.append(submission_data)
        
        if results_data:
            return json.dumps(results_data, indent=2) # Return as pretty JSON string
        else:
            return json.dumps({"message": f"No posts found for query '{query}' in r/{subreddit_name} within the last {time_filter}."})

    except Exception as e:
        return json.dumps({"error": f"An error occurred during Reddit search: {e}"})
