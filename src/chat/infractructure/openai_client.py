from openai import AsyncOpenAI
from openai.types.chat.chat_completion_user_message_param import (
    ChatCompletionUserMessageParam,
)

SYSTEM_PROMPT = """
    Jesteś LuciAI – zaawansowanym asystentem AI zintegrowanym z platformą Lucidexis.
    Twoim zadaniem jest wspierać użytkowników w zarządzaniu bazą wiedzy, dokumentami,
    wyszukiwaniu semantycznym oraz automatyzacji procesów związanych z wiedzą organizacyjną.
    Działasz jak inteligentny kurator treści – pomagasz organizować,
    wzbogacać i optymalizować wiedzę przechowywaną w systemie.
    Możesz używać struktury markdown do formatowania odpowiedzi, w tym nagłówków, list, pogrubienia i kursywy.
"""


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
        max_tokens: int = 500,
    ) -> str:
        try:
            prepared_messages = await self._prepare_messages(messages)
            response = await self.client.chat.completions.create(
                model=model,
                messages=prepared_messages,
                temperature=temperature,
                max_completion_tokens=max_tokens,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            raise OpenAIClienException(f"Error creating chat completion: {e}")

    async def _prepare_messages(
        self, messages: list[str]
    ) -> list[ChatCompletionUserMessageParam]:
        return [
            ChatCompletionUserMessageParam(
                role="system",
                content=SYSTEM_PROMPT,
            )
        ] + [
            ChatCompletionUserMessageParam(
                role="user",
                content=message,
            )
            for message in messages
        ]
