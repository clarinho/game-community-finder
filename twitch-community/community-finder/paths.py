import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)

# Match your actual filenames in the project root
FILTERS_PATH = os.path.join(PROJECT_DIR, "filters.json")
CONFIG_PATH = os.path.join(PROJECT_DIR, "config.json")
DISCORD_CACHE_PATH = os.path.join(PROJECT_DIR, "discord_cache.json")

