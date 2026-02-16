"""
Abstract LLM Client Interface

All LLM providers must implement this interface for seamless swapping.
"""
from abc import ABC, abstractmethod
from typing import AsyncIterator


class LLMClient(ABC):
    """Base interface for all LLM providers"""
    
    @abstractmethod
    async def chat(
        self, 
        messages: list[dict[str, str]], 
        stream: bool = False,
        **kwargs
    ) -> str | AsyncIterator[str]:
        """
        Send chat messages and get response.
        
        Args:
            messages: List of {"role": "user"|"assistant"|"system", "content": str}
            stream: If True, return async iterator of tokens
            **kwargs: Provider-specific parameters
            
        Returns:
            Complete response string OR async token iterator if stream=True
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if LLM service is reachable"""
        pass
    
    @abstractmethod
    async def close(self):
        """Cleanup resources (close HTTP connections, etc.)"""
        pass
