import os
from dotenv import load_dotenv
from pathlib import Path

# Get the root directory
ROOT_DIR = Path(__file__).parent
ENV_PATH = ROOT_DIR / '.env'

# Load environment variables
load_dotenv(dotenv_path=ENV_PATH)


class Config:
    """Configuration class for the resume matcher system"""

    # OpenAI Settings
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    MODEL_NAME = os.getenv('MODEL_NAME', 'gpt-4o-mini')
    MAX_COMPLETION_TOKENS = int(os.getenv('MAX_COMPLETION_TOKENS', 2100))
    TEMPERATURE = 1.0

    # Scoring Settings
    TOP_N_JOBS_FOR_CANDIDATE = 5
    TOP_N_CANDIDATES_FOR_JOB = 10

    # Processing Settings
    CHUNK_SIZE = 2000
    CHUNK_OVERLAP = 200

    @classmethod
    def validate(cls):
        """Validate that all required settings are present"""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not found in .env file")
        print("✅ Configuration validated successfully!")
        print(f"🤖 Model: {cls.MODEL_NAME}")
        print(f"🎯 Max completion tokens: {cls.MAX_COMPLETION_TOKENS}")

    @classmethod
    def get_openai_client(cls):
        """Get configured OpenAI client"""
        from openai import OpenAI
        return OpenAI(api_key=cls.OPENAI_API_KEY)