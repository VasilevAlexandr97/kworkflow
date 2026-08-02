from abc import abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMClientError(Exception):
    pass


class LLMInsufficientBalanceError(LLMClientError):
    pass


@dataclass(frozen=True)
class LLMUsage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost: Decimal


@dataclass(frozen=True)
class LLMCompletion[T]:
    parsed: T
    usage: LLMUsage


class LLMClient(Protocol):
    @abstractmethod
    async def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_format: type[T],
        max_tokens: int | None = None,
    ) -> LLMCompletion[T]:
        raise NotImplementedError

    @abstractmethod
    async def close(self) -> None:
        raise NotImplementedError
