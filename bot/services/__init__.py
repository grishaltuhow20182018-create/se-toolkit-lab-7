"""API clients for external services."""

import httpx


class LMSAPIClient:
    """Client for LMS Backend API."""

    def __init__(self, base_url: str, api_key: str):
        """Initialize LMS API client.
        
        Args:
            base_url: Base URL of the LMS API.
            api_key: API key for authentication.
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._client = httpx.AsyncClient(
            timeout=30.0,
            headers={"Authorization": f"Bearer {api_key}"},
        )

    async def health_check(self) -> bool:
        """Check if the backend is healthy.
        
        Returns:
            True if backend is reachable and healthy.
        """
        try:
            resp = await self._client.get(f"{self.base_url}/")
            return resp.status_code == 200
        except httpx.HTTPError:
            return False

    async def get_items(self) -> list[dict]:
        """Get all items (labs and tasks).
        
        Returns:
            List of items from the backend.
        """
        try:
            resp = await self._client.get(f"{self.base_url}/items/")
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError:
            return []

    async def get_logs(self, student_id: str) -> list[dict]:
        """Get submission logs for a student.
        
        Args:
            student_id: Student identifier (GitHub username or email).
            
        Returns:
            List of submission logs.
        """
        try:
            resp = await self._client.get(
                f"{self.base_url}/logs/",
                params={"student_id": student_id},
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError:
            return []

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()


class LLMClient:
    """Client for LLM API (Qwen Code or similar)."""

    def __init__(self, api_key: str, base_url: str, model: str):
        """Initialize LLM client.
        
        Args:
            api_key: API key for LLM service.
            base_url: Base URL of the LLM API.
            model: Model name to use.
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._client = httpx.AsyncClient(
            timeout=60.0,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )

    async def chat(self, messages: list[dict]) -> str:
        """Send a chat completion request.
        
        Args:
            messages: List of message dicts with 'role' and 'content'.
            
        Returns:
            AI response text.
        """
        try:
            resp = await self._client.post(
                f"{self.base_url}/chat/completions",
                json={
                    "model": self.model,
                    "messages": messages,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except httpx.HTTPError as e:
            return f"LLM error: {e}"

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()
