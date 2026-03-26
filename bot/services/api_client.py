"""API clients for external services."""

import httpx
from typing import Any


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

    async def health_check(self) -> dict:
        """Check if the backend is healthy.
        
        Returns:
            Dict with 'healthy' bool and 'message' str.
        """
        try:
            resp = await self._client.get(f"{self.base_url}/")
            if resp.status_code == 200:
                # Also check if we can fetch items
                items_resp = await self._client.get(f"{self.base_url}/items/")
                items_resp.raise_for_status()
                items = items_resp.json()
                return {
                    "healthy": True,
                    "message": f"Backend is healthy. {len(items)} items available.",
                }
            else:
                return {
                    "healthy": False,
                    "message": f"Backend returned HTTP {resp.status_code}",
                }
        except httpx.ConnectError as e:
            return {
                "healthy": False,
                "message": f"Connection refused ({self.base_url}). Check that the services are running.",
            }
        except httpx.HTTPStatusError as e:
            return {
                "healthy": False,
                "message": f"HTTP {e.response.status_code} {e.response.reason_phrase}. The backend service may be down.",
            }
        except httpx.HTTPError as e:
            return {
                "healthy": False,
                "message": f"Backend error: {str(e)}",
            }

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

    async def get_labs(self) -> list[dict]:
        """Get only lab items.
        
        Returns:
            List of lab items.
        """
        items = await self.get_items()
        return [item for item in items if item.get("type") == "lab"]

    async def get_tasks_for_lab(self, lab_title: str) -> list[dict]:
        """Get tasks for a specific lab.
        
        Args:
            lab_title: Lab title to filter by.
            
        Returns:
            List of task items for the lab.
        """
        items = await self.get_items()
        # Find the lab first
        lab = next((item for item in items if item.get("title", "").lower() == lab_title.lower() and item.get("type") == "lab"), None)
        if not lab:
            return []
        
        # Get tasks that have this lab as parent or in attributes
        lab_id = lab.get("id")
        tasks = [item for item in items if item.get("type") == "task" and item.get("parent_id") == lab_id]
        return tasks

    async def get_pass_rates(self, lab: str) -> list[dict]:
        """Get pass rates for a lab.
        
        Args:
            lab: Lab identifier (e.g., "lab-04").
            
        Returns:
            List of pass rate data per task.
        """
        try:
            resp = await self._client.get(
                f"{self.base_url}/analytics/pass-rates",
                params={"lab": lab},
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError:
            return []

    async def get_learners(self) -> list[dict]:
        """Get enrolled learners.
        
        Returns:
            List of learner records.
        """
        try:
            resp = await self._client.get(f"{self.base_url}/learners/")
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
