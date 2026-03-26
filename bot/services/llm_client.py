"""LLM client for intent detection and natural language processing."""

import httpx


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
        self._available = None

    async def is_available(self) -> bool:
        """Check if LLM API is available.
        
        Returns:
            True if LLM API is reachable and responding.
        """
        if self._available is not None:
            return self._available
        
        try:
            resp = await self._client.get(f"{self.base_url}/models")
            self._available = resp.status_code == 200
            return self._available
        except httpx.HTTPError:
            self._available = False
            return False

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

    async def detect_intent(self, user_message: str) -> dict:
        """Detect user intent from natural language message.
        
        Args:
            user_message: User's natural language query.
            
        Returns:
            Dict with 'intent', 'confidence', and 'parameters'.
        """
        system_prompt = """You are an intent classifier for an LMS (Learning Management System) Telegram bot.
Classify the user's message into one of these intents:
- "health" - checking if backend/system is working
- "labs" - asking about available labs
- "scores" - asking about scores/grades/pass rates for a specific lab
- "help" - asking for help or available commands
- "greeting" - saying hello/hi
- "unknown" - none of the above

Respond ONLY with a JSON object in this format:
{"intent": "intent_name", "confidence": 0.9, "parameters": {"lab": "lab-04"}}

Examples:
- "is the backend working?" → {"intent": "health", "confidence": 0.95, "parameters": {}}
- "what labs are available?" → {"intent": "labs", "confidence": 0.95, "parameters": {}}
- "show me scores for lab 04" → {"intent": "scores", "confidence": 0.9, "parameters": {"lab": "lab-04"}}
- "help me" → {"intent": "help", "confidence": 0.95, "parameters": {}}
- "hello" → {"intent": "greeting", "confidence": 0.95, "parameters": {}}
"""

        try:
            response = await self.chat([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ])
            
            # Parse the JSON response
            import json
            # Try to extract JSON from response
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
            else:
                return {"intent": "unknown", "confidence": 0.5, "parameters": {}}
        except Exception:
            return {"intent": "unknown", "confidence": 0.5, "parameters": {}}

    async def answer_query(self, user_message: str, context: dict) -> str:
        """Answer a user query using LLM with context.
        
        Args:
            user_message: User's question.
            context: Additional context (labs data, scores, etc.).
            
        Returns:
            AI-generated answer.
        """
        system_prompt = """You are a helpful assistant for an LMS (Learning Management System).
Help students check their lab submissions, scores, and understand the system.
Be friendly, concise, and helpful. Use the provided context to answer questions."""

        context_str = "\n".join(f"{k}: {v}" for k, v in context.items())
        
        try:
            return await self.chat([
                {"role": "system", "content": system_prompt},
                {"role": "system", "content": f"Context:\n{context_str}"},
                {"role": "user", "content": user_message},
            ])
        except Exception as e:
            return f"Sorry, I couldn't process that. Try using commands like /help, /labs, or /scores."

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()
