"""
App configuration, using environment variables
"""
from os import environ

from dotenv import load_dotenv

load_dotenv()

config = {
    # Check if debug is enabled
    "DEBUG": environ.get("DEBUG") if environ.get("DEBUG") else False,
    # Port to run the web server on
    "PORT": environ.get("PORT") if environ.get("PORT") else 8000,
    # Application settings
    "APP_NAME": environ.get("LOGS_NAMPESPACE") if environ.get("LOGS_NAMPESPACE") else "My App"
}
