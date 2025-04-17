from . import LLMSource
from llmchat.config import Config
from llmchat.persistence import PersistentData
from llmchat.logger import logger
import discord
import requests
import functools
import time

class OllamaLLM(LLMSource):
    def __init__(self, client: discord.Client, config: Config, db: PersistentData):
        """
        Initializes the OllamaLLM class using config settings.
        """
        super(OllamaLLM, self).__init__(client, config, db)
        self.base_url = config.ollama_base_url
        self.model = config.ollama_model
        self.temperature = config.llm_temperature
        self.max_tokens = config.llm_max_tokens

        logger.info(f"Ollama initialized with model: {self.model}")

    async def list_models(self) -> list[discord.SelectOption]:
        """
        Fetch available models from Ollama and return as selectable Discord options.
        """
        url = f"{self.base_url}/api/tags"
        try:
            response = requests.get(url)
            response.raise_for_status()
            models = response.json().get("models", [])
            return [discord.SelectOption(label=model["name"], value=model["name"]) for model in models]
        except requests.RequestException as e:
            logger.error(f"Error fetching Ollama models: {e}")
            return []

    def set_model(self, model_id: str) -> None:
        """
        Sets the active Ollama model.
        """
        self.model = model_id
        logger.info(f"Switched Ollama model to: {self.model}")

    async def get_context(self, invoker: discord.User = None) -> str:
        """
        Builds the conversation context for the LLM by retrieving recent messages.
        """
        context = self.get_initial(invoker).strip() + "\n"

        for author_id, content, _ in self.db.get_recent_messages(self.config.llm_context_messages_count):
            if author_id == -1:
                continue
            elif author_id == self.client.user.id:
                context += f"{self.config.bot_name}: {content}"
            else:
                name = (await self.client.fetch_user(author_id)).mention
                identity = self.db.get_identity(author_id)
                if identity:
                    name = identity[0]

                context += f"{name} {content}"
            context += "\n"
        # Commented out for RAG Testing
        #if self.config.bot_reminder:
        #    context += f"Reminder: {self._insert_wildcards(self.config.bot_reminder, self.db.get_identity(invoker.id))}\n"

        return context

    def _generate(self, context: str) -> str:
        """
        Sends a request to the Ollama LLM and retrieves the response.
        """
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": context, 
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": False
        }

        try:
            start_time = time.time()
            response = requests.post(url, json=payload)
            response.raise_for_status()
            result = response.json().get("response", "")
            logger.debug(f"Generation took {time.time() - start_time}s")

            if not result:
                raise Exception("Ollama generated an empty response!")
            return result
        except requests.RequestException as e:
            logger.error(f"Error communicating with Ollama: {e}")
            return "Error communicating with the AI."

    async def generate_response(self, invoker: discord.User = None) -> str:
        """
        Generates a response using Ollama LLM.
        """
        context = await self.get_context(invoker)
        logger.debug(f"Generated context: {context}")

        blocking = functools.partial(self._generate, context)
        return await self.client.loop.run_in_executor(None, blocking)

    @property
    def current_model_name(self) -> str:
        """
        Returns the current model name.
        """
        return self.model if self.model else "*Not loaded!*"
