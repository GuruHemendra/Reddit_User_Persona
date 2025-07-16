 
from reddit_persona.config import RedditConfig, LLMConfig
from reddit_persona.data_collection import DataCollection
import json
import os
from reddit_persona.non_llm_analytics import NonLLMAnalysis

def is_yaml_file_present(file_path):
    """
    Checks if a YAML file exists at the specified path.
    
    Args:
        file_path (str): Path to the file to check.
    
    Returns:
        bool: True if the YAML file exists, False otherwise.
    """
    # Check if the file exists and if it's a .yaml or .yml file
    return os.path.exists(file_path) and (file_path.endswith('.yaml') or file_path.endswith('.yml'))


def is_json_file_present(file_path):
    """
    Checks if a json file exists at the specified path.
    
    Args:
        file_path (str): Path to the file to check.
    
    Returns:
        bool: True if the json file exists, False otherwise.
    """
    # Check if the file exists and if it's a .yaml or .yml file
    return os.path.exists(file_path) and (file_path.endswith('.json'))

def load_json(filepath):
    try:
        if(is_json_file_present(file_path= filepath)):
            with open(filepath,"r") as f:
                reddit_data = json.load(f)
            return reddit_data
        else:
            raise FileNotFoundError(f"No file found at: {filepath}")
    except Exception as e:
        print(f"Error : {e}")


def run():
    user_input = input("User Profile Url..")
    config = RedditConfig(r'utils\defaultconfig.yaml')
    config.display_config()
    datacollection = DataCollection(reddit_client_id=config.get('REDDIT_CLIENT_ID'),reddit_client_secret=config.get('REDDIT_CLIENT_SECRET'),reddit_user_agent=config.get('REDDIT_USER_AGENT'))
    filename = datacollection.generate_reddit_user_json(user_input)
    reddit_data = load_json(filename)
    nonllmanalysis = NonLLMAnalysis(reddit_data=reddit_data)
    analysis = nonllmanalysis.run_analysis()
    new_data = analysis['reddit_data']







