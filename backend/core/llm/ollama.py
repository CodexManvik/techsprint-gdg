"""
Ollama LLM Client Implementation with Connection Pooling & Streaming
"""
import httpx
import json
from typing import AsyncIterator
from backend.core.llm.base import LLMClient
from backend.config.settings import settings


class OllamaClient(LLMClient):
    """Ollama-specific LLM client with async HTTP and streaming support"""
    
    def __init__(self):
        # Connection pooling for low latency
        self.client = httpx.AsyncClient(
            base_url=settings.OLLAMA_BASE_URL,
            limits=httpx.Limits(
                max_connections=10,
                max_keepalive_connections=5
            ),
            timeout=httpx.Timeout(settings.LLM_TIMEOUT)
        )
        self.model = settings.OLLAMA_MODEL
        
    async def chat(
        self, 
        messages: list[dict[str, str]], 
        stream: bool = False,
        **kwargs
    ) -> str | AsyncIterator[str]:
        """
        Send chat request to Ollama.
        
        Args:
            messages: Conversation history
            stream: Enable token streaming
            **kwargs: temperature, top_p, etc.
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            **kwargs
        }
        
        if stream:
            return self._stream_chat(payload)
        else:
            return await self._complete_chat(payload)
    
    async def _complete_chat(self, payload: dict) -> str:
        """Non-streaming chat completion"""
        try:
            response = await self.client.post("/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()
            return data["message"]["content"]
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Ollama API error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            raise RuntimeError(f"Ollama connection error: {str(e)}")
    
    async def _stream_chat(self, payload: dict) -> AsyncIterator[str]:
        """Streaming chat completion (yields tokens as they arrive)"""
        try:
            async with self.client.stream("POST", "/api/chat", json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            chunk = json.loads(line)
                            if "message" in chunk:
                                yield chunk["message"]["content"]
                        except json.JSONDecodeError:
                            continue
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Ollama streaming error: {e.response.status_code}")
        except httpx.RequestError as e:
            raise RuntimeError(f"Ollama connection error: {str(e)}")
    
    async def health_check(self) -> bool:
        """Verify Ollama server is running"""
        try:
            response = await self.client.get("/api/tags")
            return response.status_code == 200
        except Exception:
            return False
    
    async def close(self):
        """Cleanup HTTP client"""
        await self.client.aclose()
