import logging

from openai import AsyncOpenAI
from openai.types.chat.chat_completion_system_message_param import (
    ChatCompletionSystemMessageParam,
)
from openai.types.chat.chat_completion_user_message_param import (
    ChatCompletionUserMessageParam,
)
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class OpenAIClienException(Exception):
    pass


class UsedDocument(BaseModel):
    filename: str


class OpenAIReponse(BaseModel):
    content: str
    used_documents: list[UsedDocument]


class OpenAIClient:
    def __init__(self, api_key: str | None, base_url: str | None) -> None:
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    async def create_chat_completion(
        self,
        model: str,
        messages: list[str],
        system_prompt: str,
        user_system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> OpenAIReponse:
        try:
            system_prompt_message = ChatCompletionSystemMessageParam(
                role="system",
                content=system_prompt,
            )
            user_messages = [
                ChatCompletionUserMessageParam(role="user", content=message)
                for message in messages
            ]
            completion_messages: list[
                ChatCompletionSystemMessageParam | ChatCompletionUserMessageParam
            ] = [system_prompt_message] + user_messages
            if user_system_prompt:
                user_system_prompt_message = ChatCompletionSystemMessageParam(
                    role="system",
                    content=user_system_prompt,
                )
                completion_messages.append(user_system_prompt_message)
            response = await self.client.chat.completions.parse(
                model=model,
                messages=completion_messages,
                temperature=temperature,
                max_completion_tokens=max_tokens,
                response_format=OpenAIReponse,
            )
            parsed_response: OpenAIReponse | None = (
                response.choices[0].message.parsed if response.choices else None
            )
            if parsed_response:
                return parsed_response
            return OpenAIReponse(content="", used_documents=[])
        except Exception as e:
            raise OpenAIClienException(f"Error creating chat completion: {e}")
