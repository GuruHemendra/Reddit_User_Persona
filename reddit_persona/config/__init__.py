import yaml
import os

class RedditConfig:
    """Class to manage predefined API configuration values."""

    # Define the fixed configuration fields (keys) here
    CONFIG_FIELDS = [
        "REDDIT_CLIENT_ID",
        "REDDIT_CLIENT_SECRET",
        "REDDIT_USER_AGENT",
    ]

    def __init__(self, yaml_path=None, **kwargs):
        """
        Initializes the configuration, either from a YAML file or provided arguments.
        
        Args:
            yaml_path (str, optional): Path to the YAML configuration file.
            kwargs (dict): Additional configuration fields as key-value pairs.
        """
        # Initialize the configuration as an empty dictionary
        self.config = {field: None for field in self.CONFIG_FIELDS}

        # If a YAML path is provided, load the configurations from there
        if yaml_path:
            self.load_from_yaml(yaml_path)

        # If any keyword arguments are provided, populate them into the config dictionary
        self.config.update(kwargs)

        # If any configuration values are missing, prompt the user for input
        self.load_from_input()

    def load_from_yaml(self, yaml_path):
        """Loads configuration from a YAML file."""
        try:
            with open(yaml_path, 'r') as file:
                config_data = yaml.safe_load(file)
                # Only update the fixed fields, leaving others intact

                for field in self.CONFIG_FIELDS:
                    if  field in config_data:
                        self.config[field] = config_data[field]
        except FileNotFoundError:
            print(f"Error: The file at {yaml_path} was not found.")
        except yaml.YAMLError as e:
            print(f"Error parsing YAML file: {e}")

    def load_from_input(self):
        """
        Prompts the user for input, checking for existing values and allowing 
        the user to modify them.
        """
        for field_name in self.CONFIG_FIELDS:
            # If the field is not already set, prompt the user for input
            if self.config[field_name] is None :
                self.config[field_name] = self.ask_user_input(field_name)

    def ask_user_input(self, field_name):
        """
        Prompts the user to input a value for the specified configuration field.
        
        Args:
            field_name (str): The name of the configuration field.
        
        Returns:
            str: The user input value.
        """
        current_value = self.config.get(field_name)

        # If the field already has a value, ask if the user wants to keep it
        if current_value:
            response = input(
                f"'{field_name}' already exists as '{current_value}'. "
                "Would you like to use it? (y/n): ").strip().lower()
            if response == 'y':
                return current_value

        # If the user does not want to keep the existing value, ask for new input
        return input(f"Please enter the value for {field_name}: ").strip()

    def display_config(self):
        """Returns the current configuration as a dictionary."""
        print("Displaying Config...")
        for k in self.config.keys():
            print(f"{k} : {self.config[k]}")
        return self.config

    def get(self, field_name):
        """
        Retrieves the value for the specified configuration field.
        
        Args:
            field_name (str): The name of the configuration field to retrieve.
        
        Returns:
            str: The value of the specified configuration field, or None if it does not exist.
        """
        # Check if the field is in the predefined config fields
        if field_name in self.CONFIG_FIELDS:
            return self.config.get(field_name)
        else:
            print(f"Error: '{field_name}' is not a valid configuration field.")
            return None
        

import yaml
import os

class LLMConfig:
    """Class to manage Hugging Face LLM configuration including token and model ID."""

    CONFIG_FIELDS = [
        "HF_TOKEN",
        "MODEL_ID"
    ]

    def __init__(self, hf_token=None, model_id=None, yaml_path=None):
        """
        Initialize config either from direct input, a YAML file, or environment variables.

        Args:
            hf_token (str, optional): Hugging Face access token.
            model_id (str, optional): Model ID to use (e.g., 'mistralai/Mistral-7B-Instruct-v0.1').
            yaml_path (str, optional): Path to YAML file with config fields.
        """
        self.config = {field: None for field in self.CONFIG_FIELDS}

        # Priority 1: Direct arguments
        if hf_token:
            self.config["HF_TOKEN"] = hf_token
        if model_id:
            self.config["MODEL_ID"] = model_id

        # Priority 2: YAML file
        if yaml_path:
            self.load_from_yaml(yaml_path)

        # Priority 3: Environment variables
        for field in self.CONFIG_FIELDS:
            if self.config[field] is None:
                self.config[field] = os.getenv(field)

        # Priority 4: Prompt user
        self.load_from_input()

    def load_from_yaml(self, yaml_path):
        """Load configuration from a YAML file."""
        try:
            with open(yaml_path, 'r') as file:
                config_data = yaml.safe_load(file)
                for field in self.CONFIG_FIELDS:
                    if field in config_data:
                        self.config[field] = config_data[field]
        except FileNotFoundError:
            print(f"❌ Error: The file at {yaml_path} was not found.")
        except yaml.YAMLError as e:
            print(f"❌ Error parsing YAML file: {e}")

    def load_from_input(self):
        """Prompt user for any missing fields."""
        for field in self.CONFIG_FIELDS:
            if not self.config.get(field):
                self.config[field] = self.ask_user_input(field)

    def ask_user_input(self, field_name):
        """Ask user to enter the value for a missing field."""
        return input(f"Please enter the value for {field_name}: ").strip()

    def display_config(self):
        """Display and return current configuration."""
        print("🔧 LLM Configuration:")
        for k, v in self.config.items():
            print(f" - {k}: {v}")
        return self.config

    def get(self, field_name):
        """Safely retrieve a configuration field."""
        if field_name in self.CONFIG_FIELDS:
            return self.config.get(field_name)
        else:
            print(f"⚠️ Error: '{field_name}' is not a valid configuration field.")
            return None
