from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

def back_keyboard() -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="⬅️ Назад")],
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def contact_keyboard() -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="📱 Поделиться контактом", request_contact=True)],
        [KeyboardButton(text="⬅️ Назад")],
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, one_time_keyboard=True)