"""Command handlers - business logic without Telegram dependency."""

from typing import Any


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
        "/scores <lab> - Get your scores for a lab"
    )


async def handle_help() -> str:
    """Handle /help command.
    
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
        # Fallback without API client
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
        # Fallback without API client
        return (
            "📋 Available Labs:\n\n"
            "Lab 4: Security Basics\n"
            "Lab 5: Web Application Security\n"
            "Lab 6: Bot Development\n"
            "Lab 7: Analytics Dashboard\n\n"
            "Use /scores <lab_name> to check your progress."
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
    
    # Fallback: try to get tasks for the lab
    tasks = await api_client.get_tasks_for_lab(lab_name)
    if tasks:
        result = f"📊 Tasks for {lab_name}:\n\n"
        for task in tasks:
            title = task.get("title", "Unknown")
            result += f"• {title}\n"
        result += "\nUse /scores with the exact lab ID for detailed scores."
        return result.strip()
    
    return f"❌ No data found for lab '{lab_name}'.\n\nCheck the lab name and try again."


async def handle_intent(message: str, llm_client: Any = None, api_client: Any = None) -> str:
    """Handle natural language queries using intent routing.
    
    Args:
        message: User's natural language query.
        llm_client: Optional LLM client for intent detection.
        api_client: Optional LMS API client for data.
        
    Returns:
        Response based on detected intent.
    """
    message_lower = message.lower()
    
    # Simple keyword-based intent detection (fallback without LLM)
    if "health" in message_lower or "status" in message_lower or "working" in message_lower:
        return await handle_health(api_client)
    elif "lab" in message_lower and ("list" in message_lower or "show" in message_lower or "available" in message_lower):
        return await handle_labs(api_client)
    elif "score" in message_lower or "grade" in message_lower or "pass" in message_lower:
        # Try to extract lab name
        words = message_lower.split()
        for i, word in enumerate(words):
            if "lab" in word or word.startswith("lab"):
                lab_name = word if word.startswith("lab") else f"lab-{words[i+1]}" if i+1 < len(words) else "lab-04"
                return await handle_scores(lab_name, api_client)
        return "Please specify which lab you want scores for. Example: /scores lab-04"
    elif "help" in message_lower or "command" in message_lower:
        return await handle_help()
    else:
        if llm_client:
            # Use LLM for intent detection
            response = await llm_client.chat([
                {"role": "system", "content": "You are an LMS bot assistant. Help the user with their question about labs, scores, and submissions."},
                {"role": "user", "content": message}
            ])
            return response
        else:
            return (
                "🤔 I'm not sure what you mean. Try using commands:\n\n"
                "/start - Welcome message\n"
                "/help - Available commands\n"
                "/health - Backend status\n"
                "/labs - List labs\n"
                "/scores <lab> - Your scores"
            )
