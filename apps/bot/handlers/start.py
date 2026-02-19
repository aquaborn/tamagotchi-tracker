from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import WebAppInfo

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="🎮 Открыть Mini App", web_app=WebAppInfo(url="https://ВАШ-NGROK-URL.ngrok-free.app"))]
        ]
    )
    await message.answer(
        "Добро пожаловать в TMA Tamagotchi!\n\n"
        "Используйте Mini App для ухода за вашим питомцем.\n"
        "Доступные команды:\n"
        "/pet - посмотреть состояние питомца\n"
        "/feed - покормить питомца\n"
        "/play - поиграть с питомцем\n"
        "/sleep - уложить питомца спать",
        reply_markup=keyboard
    )

@router.message(Command("pet"))
async def cmd_pet(message: types.Message):
    # Здесь будет интеграция с API
    await message.answer("Pet state: здоров, сыт и доволен! (в разработке)")

@router.message(Command("feed"))
async def cmd_feed(message: types.Message):
    # Здесь будет интеграция с API
    await message.answer("Вы покормили питомца! (в разработке)")

@router.message(Command("play"))
async def cmd_play(message: types.Message):
    # Здесь будет интеграция с API
    await message.answer("Вы поиграли с питомцем! (в разработке)")

@router.message(Command("sleep"))
async def cmd_sleep(message: types.Message):
    # Здесь будет интеграция с API
    await message.answer("Питомец сладко спит! (в разработке)")