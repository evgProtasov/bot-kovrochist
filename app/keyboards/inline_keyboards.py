from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="Заказать ковёр", callback_data="order_rug")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons, resize_keyboard=True)

def get_type_rug_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="ЭВА ковёр", callback_data="type_rug:eva")],
        [InlineKeyboardButton(text="Ворсовый ковёр", callback_data="type_rug:wool")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons, resize_keyboard=True)

def get_color_eva_rug_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="Чёрный", callback_data="color_rug_eva:black")],
        [InlineKeyboardButton(text="Серый", callback_data="color_rug_eva:gray")],
        [InlineKeyboardButton(text="Бежевый", callback_data="color_rug_eva:beige")],
        [InlineKeyboardButton(text="Коричневый", callback_data="color_rug_eva:brown")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_type_rug")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons, resize_keyboard=True)

def get_color_wool_rug_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="Чёрный", callback_data="color_rug_wool:black")],
        [InlineKeyboardButton(text="Коричневый", callback_data="color_rug_wool:brown")],
        [InlineKeyboardButton(text="Серый", callback_data="color_rug_wool:grey")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_type_rug")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons, resize_keyboard=True)

def get_edging_rug_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="Стропа чёрная", callback_data="rug_edging:black_strap")],
        [InlineKeyboardButton(text="Стропа коричневая", callback_data="rug_edging:brown_strap")],
        [InlineKeyboardButton(text="Без окантовки", callback_data="rug_edging:no_edging")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_color_rug")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons, resize_keyboard=True)