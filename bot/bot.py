#!/usr/bin/env python3
"""LMS Telegram Bot - Entry point with tool-based LLM routing."""

import argparse
import asyncio

from config import settings
from handlers.commands.handlers import (
    handle_greeting,
    handle_help,
    handle_health,
    handle_intent,
    handle_labs,
    handle_scores,
    handle_start,
)
from keyboards import get_main_menu, get_scores_keyboard
from services.api_client import LMSAPIClient
from services.llm_client import LLMClient, get_bot_tools
from services.tool_executor import ToolExecutor


def parse_command(text: str) -> tuple[str, str | None]:
    """Parse command text."""
    parts = text.strip().split(maxsplit=1)
    if not parts:
        return "", None
    return parts[0].lower(), parts[1] if len(parts) > 1 else None


async def process_command(
    command: str,
    api_client: LMSAPIClient | None = None,
    llm_client: LLMClient | None = None,
    tool_executor: ToolExecutor | None = None,
    argument: str | None = None
) -> str:
    """Process command or natural language query."""
    if command.startswith("/"):
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
            return "❌ Specify lab: /scores lab-04"
        else:
            full = f"{command} {argument}" if argument else command
            return await handle_intent(full, llm_client, api_client, tool_executor)
    else:
        full = f"{command} {argument}" if argument else command
        return await handle_intent(full, llm_client, api_client, tool_executor)


async def run_test_mode(command_text: str) -> None:
    """Run bot in test mode."""
    api_client = None
    llm_client = None
    tool_executor = None
    
    if settings.lms_api_key and settings.lms_api_base_url:
        api_client = LMSAPIClient(
            base_url=settings.lms_api_base_url,
            api_key=settings.lms_api_key,
        )
        tool_executor = ToolExecutor(api_client)
    
    if settings.llm_api_key and settings.llm_api_base_url:
        llm_client = LLMClient(
            api_key=settings.llm_api_key,
            base_url=settings.llm_api_base_url,
            model=settings.llm_api_model,
        )
        llm_client.set_tools(get_bot_tools())
    
    try:
        command, argument = parse_command(command_text)
        response = await process_command(command, api_client, llm_client, tool_executor, argument)
        print(response)
    finally:
        if api_client:
            await api_client.close()
        if llm_client:
            await llm_client.close()


async def run_telegram_mode() -> None:
    """Run bot in Telegram mode."""
    if not settings.bot_token:
        print("❌ BOT_TOKEN not set")
        return

    try:
        from aiogram import Bot, Dispatcher, types, F
        from aiogram.filters import CommandStart
        from aiogram.types import CallbackQuery
    except ImportError:
        print("❌ aiogram not installed")
        return

    # Initialize clients
    api_client = LMSAPIClient(
        base_url=settings.lms_api_base_url,
        api_key=settings.lms_api_key,
    )
    llm_client = LLMClient(
        api_key=settings.llm_api_key,
        base_url=settings.llm_api_base_url,
        model=settings.llm_api_model,
    )
    llm_client.set_tools(get_bot_tools())
    tool_executor = ToolExecutor(api_client)

    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()

    @dp.message(CommandStart())
    async def start_handler(message: types.Message) -> None:
        response = await handle_start()
        await message.answer(response, reply_markup=get_main_menu())

    @dp.message(F.text == "/help")
    async def help_handler(message: types.Message) -> None:
        response = await handle_help()
        await message.answer(response)

    @dp.message(F.text == "/health")
    async def health_handler(message: types.Message) -> None:
        response = await handle_health(api_client)
        await message.answer(response)

    @dp.message(F.text == "/labs")
    async def labs_handler(message: types.Message) -> None:
        response = await handle_labs(api_client)
        await message.answer(response)

    @dp.message(F.text.startswith("/scores"))
    async def scores_handler(message: types.Message) -> None:
        parts = message.text.split(maxsplit=1)
        if len(parts) > 1:
            response = await handle_scores(parts[1], api_client)
        else:
            response = "❌ Specify lab: /scores lab-04"
            await message.answer(response, reply_markup=get_scores_keyboard())
            return
        await message.answer(response)

    @dp.message()
    async def intent_handler(message: types.Message) -> None:
        response = await handle_intent(
            message.text or "", llm_client, api_client, tool_executor
        )
        await message.answer(response)

    @dp.callback_query(F.data == "back")
    async def back_handler(callback: CallbackQuery) -> None:
        await callback.message.edit_text("Main menu:", reply_markup=get_main_menu())

    @dp.callback_query(F.data == "labs")
    async def labs_callback(callback: CallbackQuery) -> None:
        response = await handle_labs(api_client)
        await callback.message.edit_text(response, reply_markup=get_main_menu())

    @dp.callback_query(F.data == "health")
    async def health_callback(callback: CallbackQuery) -> None:
        response = await handle_health(api_client)
        await callback.message.edit_text(response, reply_markup=get_main_menu())

    @dp.callback_query(F.data == "help")
    async def help_callback(callback: CallbackQuery) -> None:
        response = await handle_help()
        await callback.message.edit_text(response, reply_markup=get_main_menu())

    @dp.callback_query(F.data == "scores")
    async def scores_callback(callback: CallbackQuery) -> None:
        await callback.message.edit_text(
            "Select a lab:", reply_markup=get_scores_keyboard()
        )

    @dp.callback_query(F.data.startswith("scores_lab-"))
    async def scores_lab_callback(callback: CallbackQuery) -> None:
        lab = callback.data.replace("scores_", "")
        response = await handle_scores(lab, api_client)
        await callback.message.edit_text(response, reply_markup=get_scores_keyboard())

    print("🤖 Bot started...")
    try:
        await dp.start_polling(bot)
    finally:
        await api_client.close()
        await llm_client.close()
        await bot.session.close()


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="LMS Telegram Bot")
    parser.add_argument("--test", type=str, help="Test mode command")
    args = parser.parse_args()

    if args.test:
        asyncio.run(run_test_mode(args.test))
    else:
        try:
            asyncio.run(run_telegram_mode())
        except KeyboardInterrupt:
            print("\n👋 Stopped")


if __name__ == "__main__":
    main()
