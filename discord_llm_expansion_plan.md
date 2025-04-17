# Discord-LLM-Chatbot Expansion Plan

**Generated:** 2025-04-17 14:06:16

This document outlines a plan to integrate functionality from [`z-waif-experimental`](https://github.com/Drakkadakka/z-waif-experimental-/tree/main) into the [`Discord-LLM-Chatbot`](https://github.com/JerichoJack/Discord-LLM-Chatbot) project.

---

## Overview of New Features

| Feature        | Purpose                                                                 |
|----------------|-------------------------------------------------------------------------|
| Twitch         | Live chat interaction and moderation from Twitch viewers                |
| Vision         | Multimodal support via webcam or uploaded images                        |
| VTube Studio   | Facial animations and emotion mapping for Twitch streaming              |
| Minecraft      | Allow bot to control Minecraft client using mods like Baritone/Wurst    |

---

## Project Structure Changes

- Add a `modules/` directory under `llmchat/`.
- Each integration lives in its own file:

```
llmchat/
└── modules/
    ├── twitch_module.py
    ├── vision_module.py
    ├── vtubestudio_module.py
    └── minecraft_module.py
```

---

## Twitch Integration

### Features:
- Twitch chat reader using `twitchio`
- Chat-to-AI interaction
- Moderation commands (`!ban`, `!timeout`)

### Config Example:
```ini
[Twitch]
enabled = true
oauth_token = your_oauth_token
username = your_bot_username
channel = channel_name
memory_retention_days = 365
```

### Dependencies:
```
twitchio
```

---

## Vision / Multimodal

### Features:
- Supports webcam or image uploads
- Image-to-caption using BLIP or other vision model

### Config Example:
```ini
[Vision]
enabled = true
use_webcam = true
webcam_device_index = 0
max_image_size = 1024
```

### Dependencies:
```
opencv-python
pillow
```

---

## VTube Studio Integration

### Features:
- Use VTube Studio WebSocket API
- Sends emotes and animates based on speech or emotion

### Config Example:
```ini
[VTubeStudio]
enabled = true
host = localhost
port = 8001
api_key = optional_plugin_key
idle_emote_ids = 1,2,3,4,5,6
speaking_emote_id = 7
```

### Dependencies:
```
websockets
```

---

## Minecraft Control

### Features:
- Connects to Minecraft bot via RCON or mod socket
- Accepts slash commands from Discord

### Config Example:
```ini
[Minecraft]
enabled = true
server_address = 127.0.0.1
server_port = 25565
rcon_password = changeme
bot_username = WaifuBot
```

### Dependencies:
```
mcrcon
```

---

## Integration Notes

- Each module conditionally loaded in `DiscordClient`
- Unified logging, config parsing
- Share LLM/voice/message pipeline references
- Extend `config.py` and `requirements.txt`

---

## Implementation Timeline

| Phase | Modules                         | Estimated Effort |
|-------|---------------------------------|------------------|
| 1     | Twitch integration              | 1–2 days         |
| 2     | Vision / BLIP multimodal        | 2–3 days         |
| 3     | VTube Studio hookup             | 2 days           |
| 4     | Minecraft command bridge        | 2–3 days         |
| 5     | Polish, cross-module errors     | 1–2 days         |

---

*End of Plan*
