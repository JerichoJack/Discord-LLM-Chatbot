# fix path
import sys
sys.path.insert(0, 'llmchat')

from llmchat.config import Config
from llmchat.client import DiscordClient

if __name__ == "__main__":
    config = Config()
    client = DiscordClient(config)
    