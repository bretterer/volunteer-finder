import os
from typing import Optional
from dotenv import load_dotenv
from pathlib import Path
import logging

# Get the root directory
ROOT_DIR = Path(__file__).parent
ENV_PATH = ROOT_DIR / '.env'

# Load environment variables
load_dotenv(dotenv_path=ENV_PATH)

# Setup logger
logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Custom exception for configuration errors"""
    pass


class Config:
    """Configuration class for the resume matcher system"""

    # OpenAI Settings
    OPENAI_API_KEY: Optional[str] = os.getenv('OPENAI_API_KEY')
    MODEL_NAME: str = os.getenv('MODEL_NAME', 'gpt-4o-mini')
    MAX_COMPLETION_TOKENS: int = int(os.getenv('MAX_COMPLETION_TOKENS', 2100))
    TEMPERATURE: float = 1.0

    # Scoring Settings
    TOP_N_JOBS_FOR_CANDIDATE: int = 5
    TOP_N_CANDIDATES_FOR_JOB: int = 10

    # Processing Settings
    CHUNK_SIZE: int = 2000
    CHUNK_OVERLAP: int = 200

    # Valid model names (expand as needed)
    VALID_MODELS = {
        'gpt-4o-mini',
        'gpt-4o',
        'gpt-4-turbo',
        'gpt-4',
        'gpt-3.5-turbo'
    }

    @classmethod
    def validate(cls) -> None:
        """
        Validate that all required settings are present and valid.

        Raises:
            ConfigurationError: If any configuration is missing or invalid
        """
        # Validate API Key
        if not cls.OPENAI_API_KEY:
            raise ConfigurationError(
                "OPENAI_API_KEY not found in .env file. "
                "Please create a .env file with your OpenAI API key."
            )

        if not cls.OPENAI_API_KEY.startswith('sk-'):
            raise ConfigurationError(
                "OPENAI_API_KEY appears to be invalid. "
                "OpenAI API keys should start with 'sk-'"
            )

        # Validate Model Name
        if cls.MODEL_NAME not in cls.VALID_MODELS:
            logger.warning(
                f"Model '{cls.MODEL_NAME}' is not in the list of known models. "
                f"Valid models: {', '.join(cls.VALID_MODELS)}"
            )

        # Validate Token Limits
        if cls.MAX_COMPLETION_TOKENS <= 0:
            raise ConfigurationError(
                f"MAX_COMPLETION_TOKENS must be positive, got {cls.MAX_COMPLETION_TOKENS}"
            )

        if cls.MAX_COMPLETION_TOKENS > 16000:
            logger.warning(
                f"MAX_COMPLETION_TOKENS is very high ({cls.MAX_COMPLETION_TOKENS}). "
                "This may result in high API costs."
            )

        # Validate Temperature
        if not 0.0 <= cls.TEMPERATURE <= 2.0:
            raise ConfigurationError(
                f"TEMPERATURE must be between 0.0 and 2.0, got {cls.TEMPERATURE}"
            )

        # Validate Scoring Settings
        if cls.TOP_N_JOBS_FOR_CANDIDATE <= 0:
            raise ConfigurationError(
                f"TOP_N_JOBS_FOR_CANDIDATE must be positive, got {cls.TOP_N_JOBS_FOR_CANDIDATE}"
            )

        if cls.TOP_N_CANDIDATES_FOR_JOB <= 0:
            raise ConfigurationError(
                f"TOP_N_CANDIDATES_FOR_JOB must be positive, got {cls.TOP_N_CANDIDATES_FOR_JOB}"
            )

        # Validate Processing Settings
        if cls.CHUNK_SIZE <= 0:
            raise ConfigurationError(
                f"CHUNK_SIZE must be positive, got {cls.CHUNK_SIZE}"
            )

        if cls.CHUNK_OVERLAP < 0:
            raise ConfigurationError(
                f"CHUNK_OVERLAP must be non-negative, got {cls.CHUNK_OVERLAP}"
            )

        if cls.CHUNK_OVERLAP >= cls.CHUNK_SIZE:
            raise ConfigurationError(
                f"CHUNK_OVERLAP ({cls.CHUNK_OVERLAP}) must be less than "
                f"CHUNK_SIZE ({cls.CHUNK_SIZE})"
            )

        logger.info("Configuration validated successfully")
        logger.debug(f"Model: {cls.MODEL_NAME}, Max tokens: {cls.MAX_COMPLETION_TOKENS}")

    @classmethod
    def get_openai_client(cls):
        """
        Get configured OpenAI client.

        Returns:
            OpenAI: Configured OpenAI client instance

        Raises:
            ConfigurationError: If configuration is invalid
        """
        cls.validate()

        try:
            from openai import OpenAI
            return OpenAI(api_key=cls.OPENAI_API_KEY)
        except ImportError as e:
            raise ConfigurationError(
                "OpenAI package not installed. Install it with: pip install openai"
            ) from e
        except Exception as e:
            raise ConfigurationError(
                f"Failed to initialize OpenAI client: {str(e)}"
            ) from e

    @classmethod
    def display_config(cls) -> str:
        """
        Get a formatted string of the current configuration (for debugging).
        DOES NOT display sensitive information like API keys.

        Returns:
            str: Formatted configuration string
        """
        return f"""
Configuration:
==============
OpenAI Settings:
  - API Key: {'✓ Set' if cls.OPENAI_API_KEY else '✗ Not set'}
  - Model: {cls.MODEL_NAME}
  - Max Completion Tokens: {cls.MAX_COMPLETION_TOKENS}
  - Temperature: {cls.TEMPERATURE}

Scoring Settings:
  - Top N Jobs for Candidate: {cls.TOP_N_JOBS_FOR_CANDIDATE}
  - Top N Candidates for Job: {cls.TOP_N_CANDIDATES_FOR_JOB}

Processing Settings:
  - Chunk Size: {cls.CHUNK_SIZE}
  - Chunk Overlap: {cls.CHUNK_OVERLAP}
"""