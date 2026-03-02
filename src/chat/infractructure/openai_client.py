from openai import AsyncOpenAI
from openai.types.chat.chat_completion_user_message_param import (
    ChatCompletionUserMessageParam,
)


class OpenAIClienException(Exception):
    pass


class OpenAIClient:
    def __init__(self, api_key: str, base_url: str) -> None:
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    async def create_chat_completion(
        self,
        model: str,
        messages: list[str],
        temperature: float = 0.7,
    ) -> str:
        try:
            prepared_messages = await self._prepare_messages(messages)
            response = await self.client.chat.completions.create(
                model=model,
                messages=prepared_messages,
                temperature=temperature,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            raise OpenAIClienException(f"Error creating chat completion: {e}")

    async def _prepare_messages(
        self, messages: list[str]
    ) -> list[ChatCompletionUserMessageParam]:
        return [
            ChatCompletionUserMessageParam(content=message, role="user")
            for message in messages
        ]
