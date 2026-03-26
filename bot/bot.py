#!/usr/bin/env python3
"""LMS Telegram Bot - Entry point.

Usage:
    uv run bot.py                  # Run in Telegram mode (requires BOT_TOKEN)
    uv run bot.py --test "/start"  # Run in test mode (no Telegram connection)
"""

import argparse
import asyncio

from config import settings
from handlers.commands.handlers import (
    handle_help,
    handle_health,
    handle_intent,
    handle_labs,
    handle_scores,
    handle_start,
)
from services.api_client import LMSAPIClient


def parse_command(text: str) -> tuple[str, str | None]:
    """Parse command text into command and arguments.
    
    Args:
        text: User input text (e.g., "/scores lab-04" or "/start").
        
    Returns:
        Tuple of (command, argument). Argument is None if not provided.
    """
    parts = text.strip().split(maxsplit=1)
    if not parts:
        return "", None
    
    command = parts[0].lower()
    argument = parts[1] if len(parts) > 1 else None
    return command, argument


async def process_command(
    command: str, 
    api_client: LMSAPIClient | None = None,
    argument: str | None = None
) -> str:
    """Process a command and return the response.
    
    Args:
        command: Command string (e.g., "/start", "/help").
        api_client: Optional LMS API client for backend data.
        argument: Optional command argument.
        
    Returns:
        Response text to send to user.
    """
    if command == "/start":
        return await handle_start()
    elif command == "/help":
        return await handle_help()
    elif command == "/health":
        return await handle_health(api_client)
    elif command == "/labs":
        return await handle_labs(api_client)
    elif command == "/scores":
        if argument:
            return await handle_scores(argument, api_client)
        else:
            return "❌ Please specify a lab name. Example: /scores lab-04"
    else:
        # Try intent-based routing for natural language
        return await handle_intent(f"{command} {argument}" if argument else command, api_client=api_client)


async def run_test_mode(command_text: str) -> None:
    """Run bot in test mode - process command and print result.
    
    Args:
        command_text: Command to test (e.g., "/start" or "/scores lab-04").
    """
    # Initialize API client if credentials are available
    api_client = None
    if settings.lms_api_key and settings.lms_api_base_url:
        api_client = LMSAPIClient(
            base_url=settings.lms_api_base_url,
            api_key=settings.lms_api_key,
        )
    
    try:
        command, argument = parse_command(command_text)
        response = await process_command(command, api_client, argument)
        print(response)
    finally:
        if api_client:
            await api_client.close()


async def run_telegram_mode() -> None:
    """Run bot in Telegram mode - connect to Telegram and handle updates.
    
    This function will be implemented in Task 2.
    """
    if not settings.bot_token:
        print("❌ Error: BOT_TOKEN is not set in .env.bot.secret")
        print("Please copy .env.bot.example to .env.bot.secret and fill in your bot token.")
        sys.exit(1)

    # Import aiogram only when needed (not required for test mode)
    try:
        from aiogram import Bot, Dispatcher, types
        from aiogram.filters import CommandStart
    except ImportError:
        print("❌ Error: aiogram is not installed. Run: uv sync")
        sys.exit(1)

    # Initialize API client
    api_client = LMSAPIClient(
        base_url=settings.lms_api_base_url,
        api_key=settings.lms_api_key,
    )

    # Initialize bot and dispatcher
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()

    # Handler for /start command
    @dp.message(CommandStart())
    async def start_handler(message: types.Message) -> None:
        """Handle /start command from Telegram."""
        response = await handle_start()
        await message.answer(response)

    # Handler for /help command
    @dp.message(lambda msg: msg.text == "/help")
    async def help_handler(message: types.Message) -> None:
        """Handle /help command from Telegram."""
        response = await handle_help()
        await message.answer(response)

    # Handler for /health command
    @dp.message(lambda msg: msg.text == "/health")
    async def health_handler(message: types.Message) -> None:
        """Handle /health command from Telegram."""
        response = await handle_health(api_client)
        await message.answer(response)

    # Handler for /labs command
    @dp.message(lambda msg: msg.text == "/labs")
    async def labs_handler(message: types.Message) -> None:
        """Handle /labs command from Telegram."""
        response = await handle_labs(api_client)
        await message.answer(response)

    # Handler for /scores command
    @dp.message(lambda msg: msg.text and msg.text.startswith("/scores"))
    async def scores_handler(message: types.Message) -> None:
        """Handle /scores command from Telegram."""
        parts = message.text.split(maxsplit=1)
        if len(parts) > 1:
            response = await handle_scores(parts[1], api_client)
        else:
            response = "❌ Please specify a lab name. Example: /scores lab-04"
        await message.answer(response)

    # Handler for other messages (intent routing)
    @dp.message()
    async def intent_handler(message: types.Message) -> None:
        """Handle natural language queries."""
        response = await handle_intent(message.text or "", api_client=api_client)
        await message.answer(response)

    # Start polling
    print(f"🤖 Bot started. Polling for updates...")
    try:
        await dp.start_polling(bot)
    finally:
        await api_client.close()
        await bot.session.close()


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="LMS Telegram Bot")
    parser.add_argument(
        "--test",
        type=str,
        metavar="COMMAND",
        help="Run in test mode with the specified command (e.g., --test '/start')",
    )

    args = parser.parse_args()

    if args.test:
        # Test mode: process command and print result
        asyncio.run(run_test_mode(args.test))
    else:
        # Telegram mode: run the bot
        try:
            asyncio.run(run_telegram_mode())
        except KeyboardInterrupt:
            print("\n👋 Bot stopped.")


if __name__ == "__main__":
    main()
