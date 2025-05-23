import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
env_path = Path(__file__).resolve().parent.parent.parent / '.env'
print(f"Loading .env file from: {env_path}")
load_dotenv(dotenv_path=env_path)

# Print environment variables for debugging
api_key = os.getenv("SPORTSRADAR_API_KEY")
base_url = os.getenv("NFL_BASE_URL")
openai_api_key = os.getenv("OPENAI_API_KEY")
print(f"API Key loaded: {'*' * 4}{api_key[-4:] if api_key else 'Not found'}")
print(f"Base URL loaded: {base_url}")
print(f"OpenAI API Key loaded: {'*' * 4}{openai_api_key[-4:] if openai_api_key else 'Not found'}")

class Settings:
    API_KEY: str = api_key
    BASE_URL: str = base_url
    OPENAI_API_KEY: str = openai_api_key
    
    # API Info for Swagger UI
    API_TITLE: str = "NFL Data API"
    API_DESCRIPTION: str = "API for fetching NFL data from SportsRadar"
    API_VERSION: str = "0.1.0"

settings = Settings()
