# fix path
import sys
sys.path.insert(0, 'llmchat')

import asyncio
from llmchat.client import DiscordClient
from llmchat.config import Config

async def main():
    from llmchat.logger import logger  # if needed

    logger.info("Starting main...")

    config = Config()
    client = DiscordClient(config)

    logger.info("Initialized DiscordClient.")

    if client.vtube_client.enabled:
        logger.info("Connecting to VTube Studio...")
        await client.vtube_client.connect()
        await client.vtube_client.send_plugin_info()
        logger.info("VTube Studio initialized.")

    logger.info("Starting Discord bot...")
    await client.start(config.discord_bot_api_key)

    