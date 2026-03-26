"""Intent router for natural language queries."""

import re
from typing import Any


def extract_lab_name(text: str) -> str | None:
    """Extract lab name from text.
    
    Args:
        text: User input text.
        
    Returns:
        Lab name (e.g., "lab-04") or None.
    """
    # Pattern: lab-04, lab 04, lab04, Lab 4, etc.
    patterns = [
        r"lab[- ]?(\d{1,2})",
        r"lab\s*#?(\d{1,2})",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            num = match.group(1).zfill(2)
            return f"lab-{num}"
    
    return None


def detect_intent_keyword(text: str) -> dict:
    """Detect intent using keyword matching (fallback when LLM unavailable).
    
    Args:
        text: User input text.
        
    Returns:
        Dict with 'intent', 'confidence', and 'parameters'.
    """
    text_lower = text.lower().strip()
    
    # Greeting patterns
    if any(g in text_lower for g in ["hello", "hi ", "hi!", "hey", "good morning", "good afternoon"]):
        return {"intent": "greeting", "confidence": 0.9, "parameters": {}}
    
    # Help patterns
    if any(h in text_lower for h in ["help", "command", "what can", "what do", "how to use"]):
        return {"intent": "help", "confidence": 0.9, "parameters": {}}
    
    # Health patterns
    if any(h in text_lower for h in ["health", "status", "working", "up", "running", "backend", "server", "online"]):
        return {"intent": "health", "confidence": 0.85, "parameters": {}}
    
    # Labs patterns
    if any(l in text_lower for l in ["what lab", "labs", "available lab", "list lab", "show lab"]):
        return {"intent": "labs", "confidence": 0.85, "parameters": {}}
    
    # Scores patterns
    if any(s in text_lower for s in ["score", "grade", "pass rate", "result", "my progress"]):
        lab = extract_lab_name(text_lower)
        return {
            "intent": "scores",
            "confidence": 0.85,
            "parameters": {"lab": lab} if lab else {}
        }
    
    # Check for lab queries without "scores" keyword
    lab = extract_lab_name(text_lower)
    if lab:
        return {"intent": "scores", "confidence": 0.7, "parameters": {"lab": lab}}
    
    return {"intent": "unknown", "confidence": 0.5, "parameters": {}}


async def route_intent(
    text: str,
    llm_client: Any = None,
    api_client: Any = None,
    handlers: dict | None = None
) -> str:
    """Route user message to appropriate handler based on intent.
    
    Args:
        text: User input text.
        llm_client: Optional LLM client for intent detection.
        api_client: Optional LMS API client for data.
        handlers: Dict of handler functions.
        
    Returns:
        Response text.
    """
    if handlers is None:
        handlers = {}
    
    # Detect intent (try LLM first, fallback to keywords)
    intent_data = {"intent": "unknown", "confidence": 0.5, "parameters": {}}
    
    if llm_client:
        llm_available = await llm_client.is_available()
        if llm_available:
            intent_data = await llm_client.detect_intent(text)
    
    # Fallback to keyword detection
    if intent_data["confidence"] < 0.7:
        intent_data = detect_intent_keyword(text)
    
    intent = intent_data["intent"]
    params = intent_data.get("parameters", {})
    
    # Route to appropriate handler
    if intent == "greeting":
        if "greeting" in handlers:
            return await handlers["greeting"]()
        return "👋 Hello! I'm your LMS Bot. Use /help to see available commands."
    
    elif intent == "help":
        if "help" in handlers:
            return await handlers["help"]()
        return "Use /help to see available commands."
    
    elif intent == "health":
        if "health" in handlers:
            return await handlers["health"](api_client)
        return "Backend status unknown."
    
    elif intent == "labs":
        if "labs" in handlers:
            return await handlers["labs"](api_client)
        return "Labs list unknown."
    
    elif intent == "scores":
        lab = params.get("lab")
        if lab:
            if "scores" in handlers:
                return await handlers["scores"](lab, api_client)
            return f"Scores for {lab} unknown."
        else:
            return "❌ Please specify which lab. Example: 'show scores for lab 04'"
    
    elif intent == "unknown":
        return (
            "🤔 I'm not sure what you mean. Try:\n\n"
            "• 'show labs' - List available labs\n"
            "• 'scores for lab 04' - Check your scores\n"
            "• 'is backend working' - Check status\n"
            "• Or use commands: /help, /labs, /scores <lab>"
        )
    
    return "Please use /help to see available commands."
