from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import google_search
from google.adk.agents import SequentialAgent, LlmAgent
from google.adk.tools.agent_tool import AgentTool
import os
import json
import pandas as pd
from datetime import datetime, timedelta
from google.genai import types
import gdown

APP_NAME="google_search_agent"
USER_ID="user1234"
SESSION_ID="1234"

MODEL_NAME='gemini-2.5-flash'
# --- Tool Functions ---

def is_file_updated_within_24_hours(file_path: str) -> bool:
    """
    Checks if a file exists and was modified within the last 24 hours.

    Args:
        file_path (str): The path to the file.

    Returns:
        bool: True if the file exists and is up-to-date, otherwise False.
    """
    if os.path.exists(file_path):
        file_mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
        return datetime.now() - file_mod_time < timedelta(hours=24)
    return False

def download_league_data(output_path: str = 'league_pro_games.csv') -> str:
    """
    Downloads the League of Legends pro games dataset.

    Args:
        output_path (str): The path to save the downloaded file.

    Returns:
        str: A message indicating the result of the download.
    """
    if is_file_updated_within_24_hours(output_path):
        return f"File '{output_path}' is already up-to-date."

    # Google Drive file ID for the dataset
    file_id = '1IjIEhLc9n8eLKeY-yh_YigKVWbhgGBsN'
    file_url = f'https://drive.google.com/uc?id={file_id}'

    print(f"Downloading data to '{output_path}'...")
    gdown.download(file_url, output_path, quiet=False)
    return f"File '{output_path}' downloaded successfully."


def filter_data_from_agents(selected_cols_json: str, selected_teams_json: str) -> pd.DataFrame:
    """
    Filters the league dataset based on JSON outputs from agents.

    Args:
        selected_cols_json (str): JSON string from dataframe_fields_agent with a "columns" key.
        selected_teams_json (str): JSON string from get_teams_agent with a "teams" key.

    Returns:
        pd.DataFrame: A filtered DataFrame containing the specified teams and columns.
    """
    file_path = 'league_pro_games.csv'

    # --- 1. Parse Agent Outputs ---
    try:
        columns_to_keep = json.loads(selected_cols_json)["columns"]
        teams_to_filter = json.loads(selected_teams_json)["teams"]
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error parsing JSON from agent output: {e}")
        return pd.DataFrame() # Return an empty DataFrame on error

    # --- 2. Load and Filter Data ---
    download_league_data(file_path)
    try:
        df = pd.read_csv(file_path, on_bad_lines='warn')

        # Filter for the selected teams first
        team_filtered_df = df[df['teamname'].isin(teams_to_filter)]

        # Select the desired columns from the team-filtered data
        final_df = team_filtered_df[columns_to_keep]

        # filter only for position = team
        # final_df = final_df[final_df['position'] == 'team']
        # 12 allows us to ask ai to look at particular games
        final_df = final_df.tail(60)
        return final_df.to_string()

    except FileNotFoundError:
        print(f"Error: Data file '{file_path}' not found.")
        return pd.DataFrame()
    except KeyError as e:
        print(f"Error: A specified column was not found in the dataset: {e}")
        return pd.DataFrame()

local_file = 'league_pro_games.csv'
if not is_file_updated_within_24_hours(local_file):
    download_league_data(local_file)
else:
    print("File is already up-to-date, skipping download")


dataframe_fields_agent = LlmAgent(
    model=MODEL_NAME,
    name="get_fields",
    instruction="""
    Act like a professional esport analyst that fully understands league of legends.
    
    Your goal is to analyze the request and determine what fields and data should be returned for analysis.

    The available columns are:


    gameid,datacompleteness,url,league,year,split,playoffs,date,game,patch,participantid,side,position,playername,playerid,teamname,teamid,champion,ban1,ban2,ban3,ban4,ban5,pick1,pick2,pick3,pick4,pick5,gamelength,result,kills,deaths,assists,teamkills,teamdeaths,doublekills,triplekills,quadrakills,pentakills,firstblood,firstbloodkill,firstbloodassist,firstbloodvictim,team kpm,ckpm,firstdragon,dragons,opp_dragons,elementaldrakes,opp_elementaldrakes,infernals,mountains,clouds,oceans,chemtechs,hextechs,dragons (type unknown),elders,opp_elders,firstherald,heralds,opp_heralds,void_grubs,opp_void_grubs,firstbaron,barons,opp_barons,atakhans,opp_atakhans,firsttower,towers,opp_towers,firstmidtower,firsttothreetowers,turretplates,opp_turretplates,inhibitors,opp_inhibitors,damagetochampions,dpm,damageshare,damagetakenperminute,damagemitigatedperminute,wardsplaced,wpm,wardskilled,wcpm,controlwardsbought,visionscore,vspm,totalgold,earnedgold,earned gpm,earnedgoldshare,goldspent,gspd,gpr,total cs,minionkills,monsterkills,monsterkillsownjungle,monsterkillsenemyjungle,cspm,goldat10,xpat10,csat10,opp_goldat10,opp_xpat10,opp_csat10,golddiffat10,xpdiffat10,csdiffat10,killsat10,assistsat10,deathsat10,opp_killsat10,opp_assistsat10,opp_deathsat10,goldat15,xpat15,csat15,opp_goldat15,opp_xpat15,opp_csat15,golddiffat15,xpdiffat15,csdiffat15,killsat15,assistsat15,deathsat15,opp_killsat15,opp_assistsat15,opp_deathsat15,goldat20,xpat20,csat20,opp_goldat20,opp_xpat20,opp_csat20,golddiffat20,xpdiffat20,csdiffat20,killsat20,assistsat20,deathsat20,opp_killsat20,opp_assistsat20,opp_deathsat20,goldat25,xpat25,csat25,opp_goldat25,opp_xpat25,opp_csat25,golddiffat25,xpdiffat25,csdiffat25,killsat25,assistsat25,deathsat25,opp_killsat25,opp_assistsat25,opp_deathsat25
    

    Return the result in a json object where we have 

    {
        "columns": [url, league, year, ..., side]
    },

    only return the json object

""",
    description="Return the fields in the csv that should be processed",
    output_key="selected_cols"
)


# leagues_to_include = ['LTA N', 'LEC', 'LCK', 'LPL', 'LCP']
#  filtered_df = df[df['league'].isin(leagues_to_include)]
# teams

league_teams = ['Weibo Gaming', 'Oh My God', 'LNG Esports', 'ThunderTalk Gaming',
       'Royal Never Give Up', 'FunPlus Phoenix', 'OKSavingsBank BRION',
       'DRX', 'Ultra Prime', 'DN Freecs', 'Nongshim RedForce',
       'BNK FEARX', 'KT Rolster', 'LGD Gaming', "Anyone's Legend",
       'Dplus KIA', 'T1', 'Gen.G', 'Hanwha Life Esports', 'EDward Gaming',
       'Bilibili Gaming', 'CTBC Flying Oyster', 'MGN Vikings Esports',
       'Fukuoka SoftBank HAWKS gaming', 'GAM Esports', 'Top Esports',
       'Team WE', 'Team Secret Whales', 'DetonatioN FocusMe', 'TALON',
       'Chiefs Esports Club', 'Team Heretics', 'Rogue', 'Team Vitality',
       'Team BDS', 'GiantX', 'SK Gaming', 'Movistar KOI', 'Fnatic',
       'Karmine Corp', 'G2 Esports', 'Invictus Gaming',
       'Ninjas in Pyjamas', 'JD Gaming', 'Shopify Rebellion', 'FlyQuest',
       'LYON', 'Cloud9', 'Disguised', '100 Thieves', 'Dignitas',
       'Team Liquid']

get_teams_agent = LlmAgent(
    name="teams_agent",
    model=MODEL_NAME,
    description=(
        "You are a helpful agent for esports for competitive league of legends with fearless draft."
    ),
    instruction=(
        f"""
        Your goal is to analyze the request and what league of legend teams are of interest. Return the response in json format,
        Make sure that the list is in the league teams below

        {",".join(league_teams)}

        and the format is 

        {{
            "teams": []
        }}

        only return the formatted json.
        """
    ),
    output_key="selected_teams"
)


get_filtered_rows_agent = LlmAgent(
    name="teams_agent",
    model=MODEL_NAME,
    description=(
        "You are a helpful agent for that will filter for the correct entries for esports information for league of legends."
    ),
    instruction=
        """
        Your goal is to take both outputs from the previous agents, the {selected_cols} and {selected_teams}, pass those
        strings and returned the filtered data
        """,
    output_key="selected_rows",
    tools=[filter_data_from_agents],
)

report_generation_agent = LlmAgent(
    name="report_agent",
    model=MODEL_NAME,
    description=(
        "You are a helpful agent that will take in the information processed so far and output an useful report."
    ),

    instruction=(
        """
            Given the following information about the teams of interest look  and determine player performance, team performance, draft gap if any. Optimize for fearless draft in league of legends.
        """
    ),
    output_key="report",
)


root_agent = SequentialAgent(
    name="EsportsAgent",
    sub_agents=[dataframe_fields_agent, get_teams_agent, get_filtered_rows_agent, report_generation_agent],
    description="Processes competitive league CSV data to provide detailed insights into esports team and player performance."
    # The agents will run in the order provided: Writer -> Reviewer -> Refactorer
)


# Note: In Colab, you can directly use 'await' at the top level.
# If running this code as a standalone Python script, you'll need to use asyncio.run() or manage the event loop.
# await call_agent_async("what's the latest ai news?")