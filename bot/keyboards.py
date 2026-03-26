"""Inline keyboard buttons for the bot."""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_main_menu() -> InlineKeyboardMarkup:
    """Get main menu inline keyboard.
    
    Returns:
        Inline keyboard with main action buttons.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 My Scores", callback_data="scores"),
                InlineKeyboardButton(text="📋 Labs", callback_data="labs"),
            ],
            [
                InlineKeyboardButton(text="🔍 Health Check", callback_data="health"),
                InlineKeyboardButton(text="❓ Help", callback_data="help"),
            ],
        ]
    )


def get_lab_selection_keyboard(labs: list[dict]) -> InlineKeyboardMarkup:
    """Get keyboard for selecting a lab.
    
    Args:
        labs: List of lab items.
        
    Returns:
        Inline keyboard with lab buttons.
    """
    keyboard = []
    row = []
    
    for lab in labs[:10]:  # Max 10 buttons
        lab_id = lab.get("attributes", {}).get("lab", "")
        title = lab.get("title", "Unknown")
        row.append(
            InlineKeyboardButton(
                text=title,
                callback_data=f"lab_{lab_id}",
            )
        )
        if len(row) >= 2:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_scores_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard for common lab scores.
    
    Returns:
        Inline keyboard with popular lab buttons.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Lab 01", callback_data="scores_lab-01"),
                InlineKeyboardButton(text="Lab 02", callback_data="scores_lab-02"),
            ],
            [
                InlineKeyboardButton(text="Lab 03", callback_data="scores_lab-03"),
                InlineKeyboardButton(text="Lab 04", callback_data="scores_lab-04"),
            ],
            [
                InlineKeyboardButton(text="Lab 05", callback_data="scores_lab-05"),
                InlineKeyboardButton(text="Lab 06", callback_data="scores_lab-06"),
            ],
            [
                InlineKeyboardButton(text="Lab 07", callback_data="scores_lab-07"),
            ],
        ]
    )


def get_back_keyboard() -> InlineKeyboardMarkup:
    """Get back button keyboard.
    
    Returns:
        Inline keyboard with back button.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="« Back to Menu", callback_data="back")],
        ]
    )
