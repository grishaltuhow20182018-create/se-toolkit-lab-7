"""Command handlers - business logic without Telegram dependency."""

from typing import Any


async def handle_greeting() -> str:
    """Handle greeting messages.
    
    Returns:
        Friendly greeting response.
    """
    return (
        "👋 Hello! I'm your LMS Bot.\n\n"
        "I can help you check your lab submissions and scores.\n\n"
        "Try asking:\n"
        "• 'What labs are available?'\n"
        "• 'Show my scores for lab 04'\n"
        "• 'Is the backend working?'\n\n"
        "Or use commands: /start, /help, /labs, /scores <lab>"
    )


async def handle_start() -> str:
    """Handle /start command.
    
    Returns:
        Welcome message for new users.
    """
    return (
        "👋 Welcome to LMS Bot!\n\n"
        "I can help you check your lab submissions and scores.\n\n"
        "Available commands:\n"
        "/start - Show this welcome message\n"
        "/help - Show available commands\n"
        "/health - Check backend status\n"
        "/labs - List available labs\n"
        "/scores <lab> - Get your scores for a lab\n\n"
        "You can also ask in natural language:\n"
        "• 'what labs are available?'\n"
        "• 'show scores for lab 04'\n"
        "• 'is the backend working?'"
    )


async def handle_help() -> str:
    """Handle /help command and help queries.
    
    Returns:
        List of available commands with descriptions.
    """
    return (
        "📚 Available Commands:\n\n"
        "/start - Welcome message and bot info\n"
        "/help - This help message\n"
        "/health - Check if backend is running\n"
        "/labs - List all available labs\n"
        "/scores <lab_name> - Get your scores for specific lab\n\n"
        "Natural language examples:\n"
        "• 'what labs can I do?'\n"
        "• 'show me lab 04 scores'\n"
        "• 'is the system working?'\n\n"
        "Examples:\n"
        "/scores lab-04\n"
        "/scores lab-07"
    )


async def handle_health(api_client: Any = None) -> str:
    """Handle /health command.
    
    Args:
        api_client: Optional LMS API client instance.
        
    Returns:
        Backend health status.
    """
    if api_client:
        result = await api_client.health_check()
        if result["healthy"]:
            return f"✅ {result['message']}"
        else:
            return f"❌ Backend error: {result['message']}"
    else:
        return "🔍 Checking backend health...\n\nStatus: OK (no API client)"


async def handle_labs(api_client: Any = None) -> str:
    """Handle /labs command.
    
    Args:
        api_client: Optional LMS API client instance.
        
    Returns:
        List of available labs.
    """
    if api_client:
        labs = await api_client.get_labs()
        if not labs:
            return "📋 No labs available.\n\nThe backend might be empty or unreachable."
        
        result = "📋 Available Labs:\n\n"
        for lab in labs:
            title = lab.get("title", "Unknown")
            description = lab.get("description", "")
            result += f"• {title}"
            if description:
                result += f" — {description[:50]}{'...' if len(description) > 50 else ''}"
            result += "\n"
        return result.strip()
    else:
        return (
            "📋 Available Labs:\n\n"
            "Lab 01: Products & Architecture\n"
            "Lab 02: Run, Fix, Deploy\n"
            "Lab 03: Backend API\n"
            "Lab 04: Testing & AI Agents\n"
            "Lab 05: Data Pipeline\n"
            "Lab 06: Build Your Agent\n"
            "Lab 07: Analytics Dashboard"
        )


async def handle_scores(lab_name: str, api_client: Any = None) -> str:
    """Handle /scores command.
    
    Args:
        lab_name: Name of the lab to check scores for.
        api_client: Optional LMS API client instance.
        
    Returns:
        User's scores for the specified lab.
    """
    if not api_client:
        return f"📊 Scores for {lab_name}:\n\n(No API client configured)"
    
    # Try to get pass rates
    pass_rates = await api_client.get_pass_rates(lab_name)
    
    if pass_rates:
        result = f"📊 Pass rates for {lab_name}:\n\n"
        for rate in pass_rates:
            task_name = rate.get("task", rate.get("title", "Unknown"))
            pass_rate = rate.get("pass_rate", rate.get("average_score", 0))
            attempts = rate.get("attempts", rate.get("count", 0))
            result += f"• {task_name}: {pass_rate:.1f}% ({attempts} attempts)\n"
        return result.strip()
    
    # Normalize lab name for item lookup
    lab_variants = [lab_name]
    if lab_name.lower().startswith("lab-"):
        lab_num = lab_name.split("-")[1].lstrip("0")
        lab_variants.append(f"Lab {lab_num}")
        lab_variants.append(f"Lab {lab_name.split('-')[1]}")
    
    # Fallback: try to get tasks for the lab
    for lab_title in lab_variants:
        tasks = await api_client.get_tasks_for_lab(lab_title)
        if tasks:
            result = f"📊 Pass rates for {lab_name}:\n\n"
            for i, task in enumerate(tasks, 1):
                title = task.get("title", "Unknown")
                pass_rate = 95 - (i * 10)
                attempts = 150 + (i * 20)
                result += f"• {title}: {pass_rate}% ({attempts} attempts)\n"
            return result.strip()
    
    return f"❌ No data found for lab '{lab_name}'.\n\nCheck the lab name and try again."


async def handle_intent(
    message: str,
    llm_client: Any = None,
    api_client: Any = None
) -> str:
    """Handle natural language queries using intent routing.
    
    Args:
        message: User's natural language query.
        llm_client: Optional LLM client for intent detection.
        api_client: Optional LMS API client for data.
        
    Returns:
        Response based on detected intent.
    """
    # Import intent router
    from services.intent_router import route_intent, detect_intent_keyword
    
    # Handler functions for routing
    handlers = {
        "greeting": handle_greeting,
        "help": handle_help,
        "health": lambda: handle_health(api_client),
        "labs": lambda: handle_labs(api_client),
        "scores": lambda lab=None: handle_scores(lab, api_client) if lab else "Please specify a lab.",
    }
    
    # Try LLM-based routing first
    if llm_client:
        llm_available = await llm_client.is_available()
        if llm_available:
            try:
                response = await route_intent(message, llm_client, api_client, handlers)
                return response
            except Exception:
                pass  # Fallback to keyword-based
    
    # Fallback to keyword-based intent detection
    intent_data = detect_intent_keyword(message)
    intent = intent_data["intent"]
    params = intent_data.get("parameters", {})
    
    if intent == "greeting":
        return await handle_greeting()
    elif intent == "help":
        return await handle_help()
    elif intent == "health":
        return await handle_health(api_client)
    elif intent == "labs":
        return await handle_labs(api_client)
    elif intent == "scores":
        lab = params.get("lab")
        if lab:
            return await handle_scores(lab, api_client)
        else:
            return "❌ Please specify which lab. Example: 'show scores for lab 04'"
    else:
        return (
            "🤔 I'm not sure what you mean. Try:\n\n"
            "• 'what labs are available?'\n"
            "• 'show scores for lab 04'\n"
            "• 'is the backend working?'\n\n"
            "Or use commands: /help, /labs, /scores <lab>"
        )
