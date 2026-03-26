"""LLM client with tool calling support."""

import httpx
import json


class LLMClient:
    """Client for LLM API (Qwen Code) with tool calling."""

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
        self._available = None
        self._tools = []

    def set_tools(self, tools: list[dict]) -> None:
        """Set available tools for the LLM.
        
        Args:
            tools: List of tool definitions in OpenAI format.
        """
        self._tools = tools

    async def is_available(self) -> bool:
        """Check if LLM API is available."""
        if self._available is not None:
            return self._available
        
        try:
            resp = await self._client.get(f"{self.base_url}/models")
            self._available = resp.status_code == 200
            return self._available
        except httpx.HTTPError:
            self._available = False
            return False

    async def chat_with_tools(self, messages: list[dict]) -> dict:
        """Send a chat completion request with tool calling.
        
        Args:
            messages: List of message dicts with 'role' and 'content'.
            
        Returns:
            Dict with 'response' text and optional 'tool_calls'.
        """
        payload = {
            "model": self.model,
            "messages": messages,
        }
        
        if self._tools:
            payload["tools"] = self._tools
            payload["tool_choice"] = "auto"
        
        try:
            resp = await self._client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            
            choice = data["choices"][0]["message"]
            result = {"response": choice.get("content", ""), "tool_calls": []}
            
            if "tool_calls" in choice:
                for tc in choice["tool_calls"]:
                    result["tool_calls"].append({
                        "name": tc["function"]["name"],
                        "arguments": json.loads(tc["function"]["arguments"]),
                    })
            
            return result
        except httpx.HTTPError as e:
            return {"response": f"LLM error: {e}", "tool_calls": []}

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()


def get_bot_tools() -> list[dict]:
    """Define all available tools for the bot."""
    return [
        {
            "type": "function",
            "function": {
                "name": "get_health_status",
                "description": "Check if the LMS backend is healthy and get item count",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "list_labs",
                "description": "Get list of all available labs with descriptions",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_scores_for_lab",
                "description": "Get pass rates and scores for a specific lab",
                "parameters": {
                    "type": "object",
                    "properties": {"lab": {"type": "string", "description": "Lab identifier (e.g., 'lab-01', 'lab-04')"}},
                    "required": ["lab"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_learners",
                "description": "Get list of enrolled students/learners",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_score_distribution",
                "description": "Get score distribution (4 buckets) for a lab",
                "parameters": {
                    "type": "object",
                    "properties": {"lab": {"type": "string", "description": "Lab identifier"}},
                    "required": ["lab"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_timeline",
                "description": "Get submission timeline for a lab",
                "parameters": {
                    "type": "object",
                    "properties": {"lab": {"type": "string", "description": "Lab identifier"}},
                    "required": ["lab"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_group_performance",
                "description": "Get per-group performance for a lab",
                "parameters": {
                    "type": "object",
                    "properties": {"lab": {"type": "string", "description": "Lab identifier"}},
                    "required": ["lab"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_top_learners",
                "description": "Get top N learners for a lab",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "lab": {"type": "string", "description": "Lab identifier"},
                        "limit": {"type": "integer", "description": "Number of top learners (default: 5)"},
                    },
                    "required": ["lab"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_completion_rate",
                "description": "Get completion rate percentage for a lab",
                "parameters": {
                    "type": "object",
                    "properties": {"lab": {"type": "string", "description": "Lab identifier"}},
                    "required": ["lab"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "sync_data",
                "description": "Trigger ETL sync to fetch latest data from autochecker",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_help",
                "description": "Get list of available commands and how to use the bot",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "compare_labs",
                "description": "Compare pass rates across multiple labs to find highest/lowest",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "metric": {"type": "string", "description": "Comparison metric: 'pass_rate', 'completion', 'difficulty'"},
                    },
                    "required": ["metric"],
                },
            },
        },
    ]
