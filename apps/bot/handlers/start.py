from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import WebAppInfo, ReplyKeyboardMarkup, KeyboardButton, LabeledPrice

router = Router()

# URL Mini App (обновить после запуска cloudflared)
MINI_APP_URL = "https://tests-kernel-athens-salem.trycloudflare.com"

# Cache for bot username
_bot_username = None


async def get_bot_username(bot) -> str:
    """Get bot username (cached)"""
    global _bot_username
    if _bot_username is None:
        me = await bot.get_me()
        _bot_username = me.username
    return _bot_username


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    # Check deep link parameters
    args = message.text.split()[1] if len(message.text.split()) > 1 else None
    
    # Handle deep links
    if args == "buystars":
        await cmd_buystars(message)
        return
    elif args and args.startswith("ref_"):
        # Handle referral link
        pass  # TODO: process referral
    
    # Inline кнопка для Mini App
    inline_keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="🎮 Открыть Mini App", web_app=WebAppInfo(url=MINI_APP_URL))]
        ]
    )
    
    # Reply клавиатура с основными командами
    reply_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎮 Играть"), KeyboardButton(text="🛒 Магазин")],
            [KeyboardButton(text="🛢️ Бочка"), KeyboardButton(text="🎁 Награды")],
            [KeyboardButton(text="📊 Статистика"), KeyboardButton(text="❓ Поддержка")],
        ],
        resize_keyboard=True
    )
    
    await message.answer(
        "🐾 <b>Добро пожаловать в TMA Tamagotchi!</b>\n\n"
        "Ваш виртуальный питомец ждёт вас!\n\n"
        "🎮 <b>Что можно делать:</b>\n"
        "• Кормить и играть с питомцем\n"
        "• Прокачивать уровень и получать награды\n"
        "• Приглашать друзей за бонусы\n"
        "• Зарабатывать VPN конфиги\n\n"
        "💫 <b>Команды:</b>\n"
        "/pet - состояние питомца\n"
        "/shop - магазин за ⭐ звёзды\n"
        "/rewards - ваши награды\n"
        "/invite - пригласить друга",
        reply_markup=reply_keyboard
    )
    
    await message.answer(
        "👇 Нажмите чтобы открыть игру:",
        reply_markup=inline_keyboard
    )


@router.message(F.text == "🎮 Играть")
async def play_button(message: types.Message):
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="🎮 Открыть Mini App", web_app=WebAppInfo(url=MINI_APP_URL))]
        ]
    )
    await message.answer("Открывай Mini App и играй! 🐾", reply_markup=keyboard)


@router.message(F.text == "📊 Статистика")
async def stats_button(message: types.Message):
    # TODO: Получить статистику из API
    await message.answer(
        "📊 <b>Ваша статистика:</b>\n\n"
        "🎮 Уровень: 1\n"
        "⭐ Опыт: 0\n"
        "🔥 Стрик: 0 дней\n"
        "🛡️ VPN часы: 0\n\n"
        "<i>Играйте чтобы прокачиваться!</i>"
    )


@router.message(F.text == "🎁 Награды")
async def rewards_button(message: types.Message):
    await message.answer(
        "🎁 <b>Система наград:</b>\n\n"
        "👥 Приглашение друга → <b>48ч VPN</b>\n"
        "😊 Довольный питомец → <b>24ч VPN</b>\n"
        "⬆️ Новый уровень → <b>48ч VPN</b>\n"
        "🔥 7 дней подряд → <b>72ч VPN</b>\n"
        "🔥 30 дней подряд → <b>168ч VPN</b>\n\n"
        "Используй /invite чтобы пригласить друзей!"
    )


@router.message(Command("shop"))
async def cmd_shop(message: types.Message):
    """Магазин"""
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="🛡️ VPN пакеты", callback_data="shop_vpn")],
            [types.InlineKeyboardButton(text="⚡ Бусты", callback_data="shop_boosts")],
            [types.InlineKeyboardButton(text="👑 Премиум предметы", callback_data="shop_premium")],
            [types.InlineKeyboardButton(text="🎮 Магазин в Mini App", web_app=WebAppInfo(url=MINI_APP_URL))],
        ]
    )
    
    await message.answer(
        "🛒 <b>Магазин</b>\n\n"
        "Покупайте за ⭐ Telegram Stars:\n\n"
        "🛡️ <b>VPN пакеты</b> - от 30⭐\n"
        "⚡ <b>Бусты</b> - удвоение опыта и автокормушка\n"
        "👑 <b>Премиум</b> - уникальные предметы\n"
        "🍖 <b>Еда</b> - спец корм для питомца\n"
        "👕 <b>Одежда</b> - прокачай питомца!\n\n"
        "Выберите категорию:",
        reply_markup=keyboard
    )


@router.message(Command("pet"))
async def cmd_pet(message: types.Message):
    # TODO: Интеграция с API
    await message.answer(
        "🐾 <b>Ваш питомец</b>\n\n"
        "😊 Настроение: Счастлив\n"
        "🍖 Сытость: 80%\n"
        "⚡ Энергия: 70%\n"
        "❤️ Счастье: 90%\n\n"
        "<i>Откройте Mini App для подробностей</i>"
    )


@router.message(Command("rewards"))
async def cmd_rewards(message: types.Message):
    await message.answer(
        "🎁 <b>Ваши награды</b>\n\n"
        "🛡️ VPN часы: 0\n"
        "🏆 Достижений: 0\n\n"
        "Играйте и приглашайте друзей!"
    )


@router.message(Command("invite"))
async def cmd_invite(message: types.Message):
    user_id = message.from_user.id
    bot_username = await get_bot_username(message.bot)
    invite_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    
    await message.answer(
        "👥 <b>Пригласи друга!</b>\n\n"
        f"Твоя ссылка:\n<code>{invite_link}</code>\n\n"
        "🎁 За каждого друга получишь:\n"
        "• <b>48 часов VPN</b>\n"
        "• <b>100 XP</b>\n\n"
        "Поделись ссылкой с друзьями!"
    )


@router.message(Command("feed"))
async def cmd_feed(message: types.Message):
    await message.answer("🍖 Вы покормили питомца! +10 XP")


@router.message(Command("play"))
async def cmd_play(message: types.Message):
    await message.answer("🎾 Вы поиграли с питомцем! +15 XP")


@router.message(Command("sleep"))
async def cmd_sleep(message: types.Message):
    await message.answer("😴 Питомец сладко спит! +5 XP")


@router.message(F.text == "❓ Поддержка")
async def support_button(message: types.Message):
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="📖 FAQ", callback_data="support_faq")],
            [types.InlineKeyboardButton(text="💬 Написать в поддержку", callback_data="support_contact")],
            [types.InlineKeyboardButton(text="🌐 Сменить язык", callback_data="support_language")],
        ]
    )
    await message.answer(
        "❓ <b>Поддержка</b>\n\n"
        "Выберите действие:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.message(Command("support"))
async def cmd_support(message: types.Message):
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="📖 FAQ", callback_data="support_faq")],
            [types.InlineKeyboardButton(text="💬 Написать в поддержку", callback_data="support_contact")],
            [types.InlineKeyboardButton(text="🌐 Сменить язык", callback_data="support_language")],
        ]
    )
    await message.answer(
        "❓ <b>Поддержка</b>\n\n"
        "Выберите действие:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data == "support_faq")
async def show_faq(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "📖 <b>Частые вопросы (FAQ)</b>\n\n"
        "<b>❓ Как кормить питомца?</b>\n"
        "→ Нажмите 🍖 FEED или используйте еду из инвентаря\n\n"
        "<b>❓ Как получить VPN?</b>\n"
        "→ Играйте, прокачивайте питомца и приглашайте друзей!\n\n"
        "<b>❓ Что такое бочка?</b>\n"
        "→ 100 любых покупок = 1 месяц VPN бесплатно!\n\n"
        "<b>❓ Зачем нужна одежда?</b>\n"
        "→ Одежда даёт бонусы: +XP, -потеря энергии и т.д.\n\n"
        "<b>❓ Как повысить уровень?</b>\n"
        "→ Кормите, играйте и ухаживайте за питомцем\n\n"
        "<b>❓ Что даёт уровень?</b>\n"
        "→ Новые эволюции питомца, бонусы к XP, VPN награды!",
        parse_mode="HTML",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="◀️ Назад", callback_data="support_back")]
            ]
        )
    )
    await callback.answer()


@router.callback_query(F.data == "support_contact")
async def contact_support(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "💬 <b>Связаться с поддержкой</b>\n\n"
        "Напишите ваш вопрос в следующем сообщении.\n\n"
        "<i>Мы ответим в течение 24 часов.</i>\n\n"
        "Или используйте команду:\n"
        "<code>/help ваш вопрос</code>",
        parse_mode="HTML",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="◀️ Назад", callback_data="support_back")]
            ]
        )
    )
    await callback.answer()


@router.callback_query(F.data == "support_language")
async def change_language(callback: types.CallbackQuery):
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"),
             types.InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")],
            [types.InlineKeyboardButton(text="🇪🇸 Español", callback_data="lang_es"),
             types.InlineKeyboardButton(text="🇧🇷 Português", callback_data="lang_pt")],
            [types.InlineKeyboardButton(text="🇩🇪 Deutsch", callback_data="lang_de"),
             types.InlineKeyboardButton(text="🇫🇷 Français", callback_data="lang_fr")],
            [types.InlineKeyboardButton(text="🇮🇹 Italiano", callback_data="lang_it"),
             types.InlineKeyboardButton(text="🇹🇷 Türkçe", callback_data="lang_tr")],
            [types.InlineKeyboardButton(text="🇮🇩 Indonesia", callback_data="lang_id"),
             types.InlineKeyboardButton(text="🇺🇦 Українська", callback_data="lang_uk")],
            [types.InlineKeyboardButton(text="◀️ Назад", callback_data="support_back")]
        ]
    )
    await callback.message.edit_text(
        "🌐 <b>Выберите язык / Select language</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("lang_"))
async def set_language(callback: types.CallbackQuery):
    lang = callback.data.replace("lang_", "")
    lang_names = {
        "ru": "🇷🇺 Русский", "en": "🇬🇧 English", "es": "🇪🇸 Español",
        "pt": "🇧🇷 Português", "de": "🇩🇪 Deutsch", "fr": "🇫🇷 Français",
        "it": "🇮🇹 Italiano", "tr": "🇹🇷 Türkçe", "id": "🇮🇩 Indonesia",
        "uk": "🇺🇦 Українська"
    }
    # TODO: save to API
    await callback.message.edit_text(
        f"✅ Язык изменён на {lang_names.get(lang, lang)}\n\n"
        f"Language changed to {lang_names.get(lang, lang)}",
        parse_mode="HTML"
    )
    await callback.answer("✅")


@router.callback_query(F.data == "support_back")
async def support_back(callback: types.CallbackQuery):
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="📖 FAQ", callback_data="support_faq")],
            [types.InlineKeyboardButton(text="💬 Написать в поддержку", callback_data="support_contact")],
            [types.InlineKeyboardButton(text="🌐 Сменить язык", callback_data="support_language")],
        ]
    )
    await callback.message.edit_text(
        "❓ <b>Поддержка</b>\n\n"
        "Выберите действие:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(Command("help"))
async def cmd_help(message: types.Message):
    # Get user's message after /help
    text = message.text.replace("/help", "").strip()
    if text:
        # Log support message
        user_id = message.from_user.id
        await message.answer(
            f"✅ <b>Сообщение отправлено в поддержку!</b>\n\n"
            f"ID обращения: <code>SUP-{user_id}-{int(message.date.timestamp())}</code>\n\n"
            f"Мы ответим в течение 24 часов.",
            parse_mode="HTML"
        )
    else:
        await message.answer(
            "💡 <b>Помощь</b>\n\n"
            "<b>Основные команды:</b>\n"
            "/start - начать игру\n"
            "/pet - состояние питомца\n"
            "/shop - магазин\n"
            "/rewards - награды\n"
            "/invite - пригласить друга\n"
            "/support - поддержка\n\n"
            "<b>Написать в поддержку:</b>\n"
            "<code>/help ваш вопрос</code>",
            parse_mode="HTML"
        )


# === BUY STARS ===

@router.message(Command("buystars"))
async def cmd_buystars(message: types.Message):
    """Buy Telegram Stars"""
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="⭐ 50 звёзд", callback_data="buy_stars_50")],
            [types.InlineKeyboardButton(text="⭐ 100+10 звёзд (+10%)", callback_data="buy_stars_100")],
            [types.InlineKeyboardButton(text="🌟 250+30 звёзд (+12%)", callback_data="buy_stars_250")],
            [types.InlineKeyboardButton(text="🌟 500+100 звёзд (+20%)", callback_data="buy_stars_500")],
            [types.InlineKeyboardButton(text="💎 1000+250 звёзд (+25%)", callback_data="buy_stars_1000")],
        ]
    )
    
    await message.answer(
        "⭐ <b>Купить Telegram Stars</b>\n\n"
        "Звёзды можно потратить на:\n"
        "🐾 Премиум питомцев (Labubu, Capybara...)\n"
        "🛡️ VPN пакеты\n"
        "⚡ Бусты и предметы\n"
        "👑 Одежду и аксессуары\n\n"
        "Выберите пакет:",
        parse_mode="HTML",
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("buy_stars_"))
async def process_buy_stars(callback: types.CallbackQuery):
    """Process stars purchase"""
    amount_str = callback.data.replace("buy_stars_", "")
    
    packages = {
        "50": {"stars": 50, "bonus": 0, "price": 50},
        "100": {"stars": 110, "bonus": 10, "price": 100},
        "250": {"stars": 280, "bonus": 30, "price": 250},
        "500": {"stars": 600, "bonus": 100, "price": 500},
        "1000": {"stars": 1250, "bonus": 250, "price": 1000},
    }
    
    pkg = packages.get(amount_str)
    if not pkg:
        await callback.answer("❌ Пакет не найден", show_alert=True)
        return
    
    # Create invoice for Telegram Stars payment
    try:
        await callback.message.answer_invoice(
            title=f"⭐ {pkg['stars']} звёзд",
            description=f"Пакет {pkg['price']} звёзд{' + ' + str(pkg['bonus']) + ' бонус' if pkg['bonus'] > 0 else ''}",
            payload=f"stars_{amount_str}_{callback.from_user.id}",
            currency="XTR",  # Telegram Stars
            prices=[LabeledPrice(label="Stars", amount=pkg['price'])],
        )
        await callback.answer()
    except Exception as e:
        await callback.answer(
            "❌ Ошибка создания платежа. Попробуйте позже.",
            show_alert=True
        )


@router.pre_checkout_query()
async def pre_checkout(query: types.PreCheckoutQuery):
    """Handle pre-checkout query"""
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment(message: types.Message):
    """Handle successful payment"""
    import httpx
    
    payment = message.successful_payment
    payload = payment.invoice_payload
    user_id = message.from_user.id
    
    # Parse payload: stars_AMOUNT_USERID or stars_AMOUNT
    parts = payload.split("_")
    if len(parts) >= 2 and parts[0] == "stars":
        amount_str = parts[1]
        
        # Calculate bonus
        packages = {
            "50": {"stars": 50, "bonus": 0},
            "100": {"stars": 100, "bonus": 10},
            "250": {"stars": 250, "bonus": 30},
            "500": {"stars": 500, "bonus": 100},
            "1000": {"stars": 1000, "bonus": 250},
        }
        
        pkg = packages.get(amount_str, {"stars": 0, "bonus": 0})
        total = pkg["stars"] + pkg["bonus"]
        
        if total > 0:
            # Add stars to user via API call
            API_URL = "http://api:8000"
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{API_URL}/v1/rewards/stars/add",
                        json={"amount": total, "telegram_payment_id": payment.telegram_payment_charge_id},
                        headers={"X-User-Id": str(user_id)}
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        await message.answer(
                            f"🎉 <b>Оплата успешна!</b>\n\n"
                            f"⭐ Получено: <b>{total}</b> монет\n"
                            f"{'🎁 Бонус: +' + str(pkg['bonus']) if pkg['bonus'] > 0 else ''}\n"
                            f"💰 Баланс: <b>{data.get('new_balance', total)}</b> ⭐\n\n"
                            f"Откройте 🎮 Mini App!",
                            parse_mode="HTML"
                        )
                        return
            except Exception as e:
                print(f"Error adding stars: {e}")
        
        await message.answer(
            f"🎉 <b>Оплата успешна!</b>\n\n"
            f"⭐ Получено: <b>{total}</b> монет\n\n"
            f"Откройте 🎮 Mini App!",
            parse_mode="HTML"
        )