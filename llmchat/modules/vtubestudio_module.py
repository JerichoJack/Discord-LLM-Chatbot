import asyncio
import json
from llmchat.logger import logger
import random
import websockets
from llmchat.config import Config

class VTubeStudioClient:
    def __init__(self, config: Config):
        self.config = config
        self.enabled = config.vtubestudio_enabled
        self.idle_emotes = config.vtubestudio_idle_emotes
        self.idle_emote_delay = config.vtubestudio_idle_emote_delay
        self.emotion_map = config.vtubestudio_emotion_map
        self.idle_task = None
        self.connected = False

        # Start the idle emote loop if enabled
        if self.enabled:
            self.config.validate_vtubestudio_config()
            self.start_idle_loop()

    async def start_idle_loop(self):
        """Starts the idle emote loop that triggers random idle emotes or emotion-based emotes."""
        if not self.idle_emotes:
            logger.warning("No idle emotes configured. Idle loop will not start.")
            return

        while self.enabled:
            if self.connected:  # Ensure we are connected before attempting to send emotes
                emote = self.get_current_emote()
                await self.send_emote(emote)
            await asyncio.sleep(self.idle_emote_delay)  # Wait before triggering the next idle emote

    def get_current_emote(self):
        """Return the current emote based on message/emotion context or random if no emotion."""
        current_emote = None

        # Check if there is an emotion to map to
        if hasattr(self, 'current_emotion') and self.current_emotion:
            emotion = self.current_emotion
            if emotion in self.emotion_map:
                current_emote = self.emotion_map[emotion]
                logger.info(f"Using emotion emote: {current_emote}")
            else:
                logger.info(f"Emotion {emotion} not mapped. Falling back to idle.")
        
        # Fallback to a random idle emote if no emotion is set or emotion mapping fails
        if not current_emote:
            current_emote = random.choice(self.idle_emotes)
            logger.info(f"Using random idle emote: {current_emote}")

        return current_emote

    async def send_emote(self, emote_id: str):
        """Send a specific emote to VTube Studio."""
        if self.websocket:
            try:
                # Assuming you're using a method to send emotes via WebSocket
                await self.websocket.send(json.dumps({"action": "set_idle_emote", "emote_id": emote_id}))
                logger.info(f"Triggered emote: {emote_id}")
            except Exception as e:
                logger.error(f"Failed to send emote {emote_id}: {e}")
        else:
            logger.warning("WebSocket connection is not established.")
        
    async def stop_idle_loop(self):
        """Stops the idle emote loop."""
        if self.idle_task:
            self.idle_task.cancel()
            self.idle_task = None
            logger.info("Idle loop has been stopped.")
            
    def set_current_emotion(self, emotion_label: str):
        """Set the current emotion to be used in the next idle cycle."""
        self.current_emotion = emotion_label
        logger.info(f"Emotion set to: {emotion_label}")