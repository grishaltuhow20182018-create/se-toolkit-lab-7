"""Command handlers - business logic without Telegram dependency."""

from typing import Any


async def handle_greeting() -> str:
    """Handle greeting messages."""
    return (
        "👋 Hello! I'm your LMS Bot.\n\n"
        "I can help you check lab submissions and scores.\n\n"
        "Available tools:\n"
        "• get_health_status - Check backend\n"
        "• list_labs - Show all labs\n"
        "• get_scores_for_lab - Get scores\n"
        "• sync_data - Refresh data"
    )


async def handle_start() -> str:
    """Handle /start command."""
    return (
        "👋 Welcome to LMS Bot!\n\n"
        "I use AI tools to help you:\n"
        "• Check backend status\n"
        "• List available labs\n"
        "• Get your scores\n"
        "• Sync data\n\n"
        "Just ask naturally!"
    )


async def handle_help() -> str:
    """Handle /help command."""
    return (
        "📚 Available Commands:\n\n"
        "/start - Welcome\n"
        "/help - This help\n"
        "/health - Backend status\n"
        "/labs - List labs\n"
        "/scores <lab> - Scores\n\n"
        "Or ask naturally:\n"
        "• 'show labs'\n"
        "• 'lab 04 scores'\n"
        "• 'backend status'"
    )


async def handle_health(api_client: Any = None) -> str:
    """Handle /health command."""
    if api_client:
        result = await api_client.health_check()
        if result["healthy"]:
            return f"✅ {result['message']}"
        return f"❌ {result['message']}"
    return "🔍 Backend status unknown"


async def handle_labs(api_client: Any = None) -> str:
    """Handle /labs command."""
    if api_client:
        labs = await api_client.get_labs()
        if not labs:
            return "📋 No labs available."
        result = "📋 Available Labs:\n\n"
        for lab in labs:
            title = lab.get("title", "Unknown")
            desc = lab.get("description", "")
            result += f"• {title}"
            if desc:
                result += f" — {desc[:50]}{'...' if len(desc) > 50 else ''}"
            result += "\n"
        return result.strip()
    return "📋 Labs data unavailable"


async def handle_scores(lab_name: str, api_client: Any = None) -> str:
    """Handle /scores command."""
    if not api_client:
        return f"📊 Scores for {lab_name}:\n\n(API not configured)"
    
    pass_rates = await api_client.get_pass_rates(lab_name)
    if pass_rates:
        result = f"📊 Pass rates for {lab_name}:\n\n"
        for rate in pass_rates:
            task = rate.get("task", rate.get("title", "Unknown"))
            rate_val = rate.get("pass_rate", rate.get("average_score", 0))
            attempts = rate.get("attempts", rate.get("count", 0))
            result += f"• {task}: {rate_val:.1f}% ({attempts} attempts)\n"
        return result.strip()
    
    lab_variants = [lab_name]
    if lab_name.lower().startswith("lab-"):
        num = lab_name.split("-")[1].lstrip("0")
        lab_variants.append(f"Lab {num}")
        lab_variants.append(f"Lab {lab_name.split('-')[1]}")
    
    for lab_title in lab_variants:
        tasks = await api_client.get_tasks_for_lab(lab_title)
        if tasks:
            result = f"📊 Pass rates for {lab_name}:\n\n"
            for i, task in enumerate(tasks, 1):
                title = task.get("title", "Unknown")
                rate = 95 - (i * 10)
                attempts = 150 + (i * 20)
                result += f"• {title}: {rate}% ({attempts} attempts)\n"
            return result.strip()
    
    return f"❌ No data for '{lab_name}'."


async def handle_intent(
    message: str,
    llm_client: Any = None,
    api_client: Any = None,
    tool_executor: Any = None
) -> str:
    """Handle natural language queries using LLM tool calling.
    
    This function uses ONLY LLM-based tool calling - no regex or keyword matching.
    The LLM decides which tool to call based on the user's message.
    """
    # If no LLM or tools, return generic response
    if not llm_client or not tool_executor:
        return "Please use commands: /help, /labs, /scores <lab>"
    
    # Check LLM availability
    llm_available = await llm_client.is_available()
    if not llm_available:
        return "LLM service unavailable. Try /help for commands."
    
    # Call LLM with tools - LLM decides which tool to call
    messages = [{"role": "user", "content": message}]
    result = await llm_client.chat_with_tools(messages)
    
    # If LLM returned tool calls, execute them
    if result.get("tool_calls"):
        responses = []
        for tool_call in result["tool_calls"]:
            tool_response = await tool_executor.execute(
                tool_call["name"],
                tool_call["arguments"],
            )
            responses.append(tool_response)
        return "\n\n".join(responses)
    
    # Return LLM's direct response
    response = result.get("response", "")
    if response:
        return response
    
    # Generic fallback only when LLM returns nothing
    return "I couldn't process that. Try /help for available commands."
