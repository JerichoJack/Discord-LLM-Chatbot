import asyncio
import json
import logging
import random
import websockets

class VTubeStudioClient:
    def __init__(self, config):
        self.enabled = config.getboolean("VTubeStudio", "enabled", fallback=False)
        if not self.enabled:
            return

        self.host = config.get("VTubeStudio", "host", fallback="127.0.0.1")
        self.port = config.getint("VTubeStudio", "port", fallback=8001)
        self.uri = f"ws://{self.host}:{self.port}"

        self.reconnect_interval = config.getint("VTubeStudio", "reconnect_interval", fallback=5)
        self.idle_emotes = config.get("VTubeStudio", "idle_emotes", fallback="").split(",")
        self.thinking_emote = config.get("VTubeStudio", "thinking_emote", fallback=None)
        self.speaking_emote = config.get("VTubeStudio", "speaking_emote", fallback=None)
        self.random_idle_interval = config.getint("VTubeStudio", "random_idle_interval", fallback=30)
        self.emotion_map = self.parse_emotion_map(config.get("VTubeStudio", "emotion_map", fallback=""))

        self.websocket = None
        self.connected = False
        self.loop = asyncio.get_event_loop()
        self.task = None

    def parse_emotion_map(self, raw_map):
        result = {}
        for pair in raw_map.split(","):
            if ":" in pair:
                emotion, emote = pair.split(":")
                result[emotion.strip()] = emote.strip()
        return result

    async def connect(self):
        while True:
            try:
                logging.info("[VTS] Attempting to connect...")
                async with websockets.connect(self.uri) as ws:
                    self.websocket = ws
                    self.connected = True
                    logging.info("[VTS] Connected to VTube Studio.")
                    await self.idle_cycle()
            except Exception as e:
                logging.warning(f"[VTS] Connection error: {e}. Reconnecting in {self.reconnect_interval}s.")
                self.connected = False
                await asyncio.sleep(self.reconnect_interval)

    async def send_emote(self, emote_id):
        if not self.connected or not self.websocket:
            return
        payload = {
            "apiName": "VTubeStudioPublicAPI",
            "messageType": "TriggerHotkey",
            "data": {"hotkeyID": emote_id}
        }
        try:
            await self.websocket.send(json.dumps(payload))
            logging.info(f"[VTS] Sent emote: {emote_id}")
        except Exception as e:
            logging.warning(f"[VTS] Failed to send emote: {e}")

    async def idle_cycle(self):
        while self.connected:
            emote = random.choice(self.idle_emotes)
            await self.send_emote(emote)
            await asyncio.sleep(self.random_idle_interval)

    async def play_thinking(self):
        if self.thinking_emote:
            await self.send_emote(self.thinking_emote)

    async def play_speaking(self):
        if self.speaking_emote:
            await self.send_emote(self.speaking_emote)

    async def play_emotion(self, emotion: str):
        if not self.enabled:
            return
        emote_id = self.emotion_mapping.get(emotion.lower())
        if emote_id:
            await self.send_emote(emote_id)
        else:
            logging.warning(f"No emote mapping for emotion: {emotion}")

    async def idle_emote_loop(self):
        while True:
            if not self.enabled:
                break
            if not self.idle_mode:
                await asyncio.sleep(1)
                continue

            emote = random.choice(self.idle_emotes)
            await self.send_emote(emote)
            await asyncio.sleep(random.randint(10, 30))  # Adjust as needed

    def start(self):
        if self.enabled:
            self.task = self.loop.create_task(self.connect())

    def stop(self):
        if self.task:
            self.task.cancel()
