# bot/keyboards.py

from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram import types


def start_kb():
    kb = ReplyKeyboardBuilder()
    kb.add(types.KeyboardButton(text="Начать игру"))
    return kb.as_markup(resize_keyboard=True)


def options_kb(options: list[str]):
    """
    callback_data = answer:<index>
    """
    builder = InlineKeyboardBuilder()
    for idx, opt in enumerate(options):
        builder.button(text=opt, callback_data=f"answer:{idx}")
    builder.adjust(1)
    return builder.as_markup()
