from openai import AsyncOpenAI
from openai.types.chat.chat_completion_system_message_param import (
    ChatCompletionSystemMessageParam,
)
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
        system_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> str:
        try:
            system_prompt_message = ChatCompletionSystemMessageParam(
                role="system",
                content=system_prompt,
            )
            user_messages = [
                ChatCompletionUserMessageParam(
                    role="user",
                    content=message,
                )
                for message in messages
            ]
            completion_messages: list[
                ChatCompletionSystemMessageParam | ChatCompletionUserMessageParam
            ] = [system_prompt_message] + user_messages
            response = await self.client.chat.completions.create(
                model=model,
                messages=completion_messages,
                temperature=temperature,
                max_completion_tokens=max_tokens,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            raise OpenAIClienException(f"Error creating chat completion: {e}")
