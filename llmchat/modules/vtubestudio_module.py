import asyncio
import json
from llmchat.logger import logger
import random
import websockets
from llmchat.config import Config
import os

plugin_info = {
    "pluginName": "Ava-Chatbot",
    "pluginDeveloper": "JerichoJack",
    "pluginVersion": "1.0.0",
}

class VTubeStudioClient:
    def __init__(self, config: Config):
        self.config = config
        self.enabled = config.vtubestudio_enabled
        self.idle_emotes = config.vtubestudio_idle_emotes
        self.idle_emote_delay = config.vtubestudio_idle_emote_delay
        self.emotion_map = config.vtubestudio_emotion_map
        self.idle_task = None
        self.connected = False
        self.websocket = None
        self.authenticated = False
        self.auth_token = None

    async def connect(self):
        """Establish WebSocket connection and start authentication flow."""
        try:
            self.websocket = await websockets.connect("ws://127.0.0.1:8001")
            logger.info("Connected to VTube Studio WebSocket.")
            await self.authenticate()
        except Exception as e:
            logger.error(f"Failed to connect to VTube Studio: {e}")

    async def authenticate(self):
        """Authenticate with VTube Studio using cached or requested token."""
        self.auth_token = self.config.vtubestudio_authentication_token
        if self.auth_token:
            logger.info("Loaded authentication token from config.ini.")
            await self.send_authentication_request()
        else:
            await self.request_token()

    async def request_token(self):
        """Request a new token from VTube Studio and wait for user approval."""
        request = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": "authenticationTokenRequest",
            "messageType": "AuthenticationTokenRequest",
            "data": {
                "pluginName": plugin_info["pluginName"],
                "pluginDeveloper": plugin_info["pluginDeveloper"]
            }
        }

        logger.info("Requesting authentication token...")
        await self.websocket.send(json.dumps(request))

        token = None
        approved = False  # Flag to track whether the token is approved

        while not approved:
            response_raw = await self.websocket.recv()
            logger.info(f"Authentication token response: {response_raw}")

            try:
                response = json.loads(response_raw)

                if response.get("messageType") == "AuthenticationTokenResponse":
                    token = response["data"]["authenticationToken"]
                    approved = response["data"].get("authenticationTokenApproved", False)

                    # Only update the token if it was received
                    if token and not self.auth_token:
                        self.auth_token = token
                        self.config.vtubestudio_authentication_token = token
                        logger.info("Received authentication token (not yet approved). Saved to config.ini")

                    if approved:
                        logger.info("Plugin approved by user.")
                        await self.send_authentication_request()  # Token approved, proceed with authentication
                        return

                    logger.info("Waiting for user to approve the plugin in VTube Studio...")

                elif response.get("messageType") == "APIError" and response["data"].get("errorID") == 51:
                    logger.info("Authentication already in progress in VTube Studio. Waiting for approval...")

                else:
                    logger.warning("Unexpected response type while requesting token.")

            except Exception as e:
                logger.error(f"Error parsing token response: {e}")
                return

            # Retry after a reasonable amount of time if no approval feedback yet
            logger.info("Retrying authentication with the received token...")
            await self.send_authentication_request()

            # Sleep for a delay before checking again
            await asyncio.sleep(10)  # 10 seconds before retrying

    async def send_authentication_request(self):
        if not self.auth_token:
            logger.error("No authentication token set. Cannot authenticate.")
            return

        request = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "messageType": "AuthenticationRequest",
            "requestID": "authenticationRequest",
            "data": {
                "pluginName": plugin_info["pluginName"],
                "pluginDeveloper": plugin_info["pluginDeveloper"],
                "authenticationToken": self.auth_token  # ✅ Include token!
            }
        }

        logger.info("Retrying authentication with the received token...")
        await self.websocket.send(json.dumps(request))

        response_raw = await self.websocket.recv()
        logger.info(f"Authentication request response: {response_raw}")

        try:
            response = json.loads(response_raw)
            if response.get("messageType") == "AuthenticationResponse" and response["data"].get("authenticated"):
                logger.info("Successfully authenticated with VTube Studio.")
                self.authenticated = True
            else:
                logger.error("Authentication rejected. Removing invalid token.")
                self.config.vtubestudio_authentication_token = ""
                self.auth_token = None
        except Exception as e:
            logger.error(f"Error parsing authentication response: {e}")

    async def send_plugin_info(self):
        """Send plugin info after successful authentication."""
        if self.authenticated:
            request = {
                "apiName": "VTubeStudioPublicAPI",
                "apiVersion": "1.0",
                "requestID": "pluginInfoRequest",
                "messageType": "PluginInfoRequest",
                "data": plugin_info
            }
            await self.websocket.send(json.dumps(request))
            response = await self.websocket.recv()
            logger.info(f"Plugin info response: {response}")

            if "messageType" in response and response["messageType"] == "APIError":
                logger.error(f"Error sending plugin info: {response['data']['message']}")
            else:
                logger.info("Plugin info successfully sent to VTube Studio.")

            if self.enabled:
                await self.start_idle_loop()
        else:
            logger.error("Cannot send plugin info, not authenticated.")

    async def start_idle_loop(self):
        """Starts the idle emote loop that triggers random idle emotes or emotion-based emotes."""
        if not self.idle_emotes:
            logger.warning("No idle emotes configured. Idle loop will not start.")
            return

        while self.enabled:
            if self.connected and self.authenticated:
                emote = self.get_current_emote()
                await self.send_emote(emote)
            await asyncio.sleep(self.idle_emote_delay)

    def get_current_emote(self):
        """Return the current emote based on message/emotion context or random if no emotion."""
        current_emote = None

        if hasattr(self, 'current_emotion') and self.current_emotion:
            emotion = self.current_emotion
            if emotion in self.emotion_map:
                current_emote = self.emotion_map[emotion]
                logger.info(f"Using emotion emote: {current_emote}")
            else:
                logger.info(f"Emotion {emotion} not mapped. Falling back to idle.")
        
        if not current_emote:
            current_emote = random.choice(self.idle_emotes)
            logger.info(f"Using random idle emote: {current_emote}")

        return current_emote

    async def send_emote(self, emote_id: str):
        """Send a specific emote to VTube Studio."""
        if self.websocket:
            try:
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
