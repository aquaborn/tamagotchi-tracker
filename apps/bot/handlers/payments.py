"""
Обработчик платежей через Telegram Stars
"""
from aiogram import Router, types, F
from aiogram.types import LabeledPrice, PreCheckoutQuery
import logging
import httpx

logger = logging.getLogger(__name__)

router = Router()

# Цены на товары в звёздах
STAR_PRICES = {
    "vpn_3days": {"stars": 30, "label": "VPN 3 дня", "hours": 72},
    "vpn_1week": {"stars": 60, "label": "VPN 1 неделя", "hours": 168},
    "vpn_2weeks": {"stars": 100, "label": "VPN 2 недели", "hours": 336},
    "vpn_1month": {"stars": 180, "label": "VPN 1 месяц", "hours": 720},
    "xp_boost_x2": {"stars": 50, "label": "XP Буст x2 (24ч)", "item_id": 5},
    "xp_boost_x3": {"stars": 75, "label": "XP Буст x3 (12ч)", "item_id": 6},
    "auto_feeder": {"stars": 100, "label": "Автокормушка (7 дней)", "item_id": 8},
    "crown": {"stars": 150, "label": "Королевская корона (+25% XP)", "item_id": 11},
    # Пакеты внутриигровых звёзд
    "coins_100": {"stars": 10, "label": "100 ⭐ монет", "coins": 100},
    "coins_500": {"stars": 45, "label": "500 ⭐ монет (+10%)", "coins": 550},
    "coins_1000": {"stars": 80, "label": "1000 ⭐ монет (+25%)", "coins": 1250},
    "coins_5000": {"stars": 350, "label": "5000 ⭐ монет (+40%)", "coins": 7000},
}

API_URL = "http://api:8000"


async def send_invoice(message: types.Message, product_id: str):
    """Отправить счёт на оплату звёздами"""
    if product_id not in STAR_PRICES:
        await message.answer("❌ Товар не найден")
        return
    
    product = STAR_PRICES[product_id]
    
    prices = [LabeledPrice(label=product["label"], amount=product["stars"])]
    
    await message.answer_invoice(
        title=product["label"],
        description=f"Оплата {product['stars']} ⭐ звёзд",
        payload=product_id,
        currency="XTR",  # XTR = Telegram Stars
        prices=prices,
    )


@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    """Подтверждение предоплаты"""
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def process_successful_payment(message: types.Message):
    """Обработка успешной оплаты"""
    payment = message.successful_payment
    product_id = payment.invoice_payload
    user_id = message.from_user.id
    
    logger.info(f"Payment received: user={user_id}, product={product_id}, stars={payment.total_amount}")
    
    if product_id not in STAR_PRICES:
        await message.answer("❌ Ошибка: неизвестный товар")
        return
    
    product = STAR_PRICES[product_id]
    
    try:
        # Отправляем запрос в API для выдачи покупки
        async with httpx.AsyncClient() as client:
            barrel_info = ""
            
            # Если это VPN пакет
            if product_id.startswith("vpn_"):
                response = await client.post(
                    f"{API_URL}/v1/rewards/add-vpn-hours",
                    json={
                        "user_id": user_id,
                        "hours": product["hours"],
                        "reason": f"purchase_{product_id}"
                    }
                )
            # Если это покупка внутриигровых монет
            elif product_id.startswith("coins_"):
                coins_amount = product["coins"]
                response = await client.post(
                    f"{API_URL}/v1/rewards/stars/add",
                    json={
                        "amount": coins_amount,
                        "telegram_payment_id": payment.telegram_payment_charge_id
                    },
                    headers={"X-User-Id": str(user_id)}
                )
                if response.status_code == 200:
                    data = response.json()
                    await message.answer(
                        f"✅ Оплата успешна!\n\n"
                        f"🌟 Вы получили: <b>{coins_amount} ⭐ монет</b>\n"
                        f"💰 Новый баланс: <b>{data.get('new_balance', 0)} ⭐</b>\n\n"
                        f"Спасибо за покупку! 🙏",
                        parse_mode="HTML"
                    )
                    return
            else:
                # Покупка предмета из магазина
                response = await client.post(
                    f"{API_URL}/v1/shop/confirm-purchase",
                    params={
                        "item_id": product.get("item_id", 1),
                        "quantity": 1,
                        "telegram_payment_id": payment.telegram_payment_charge_id
                    },
                    headers={"X-User-Id": str(user_id)}
                )
                
                # Проверяем бочку
                if response.status_code == 200:
                    data = response.json()
                    barrel = data.get("barrel", {})
                    if barrel.get("filled"):
                        barrel_info = (
                            f"\n\n🛢️ <b>БОЧКА ЗАПОЛНЕНА!</b>\n"
                            f"🎁 Награда: <b>1 МЕСЯЦ VPN!</b>"
                        )
                    else:
                        progress = barrel.get("progress", 0)
                        barrel_info = f"\n\n🛢️ Бочка: {progress}/100"
            
            if response.status_code == 200:
                await message.answer(
                    f"✅ Оплата успешна!\n\n"
                    f"🎁 Вы получили: {product['label']}\n"
                    f"⭐ Потрачено: {product['stars']} звёзд"
                    f"{barrel_info}\n\n"
                    f"Спасибо за покупку! 🙏",
                    parse_mode="HTML"
                )
            else:
                logger.error(f"API error: {response.status_code} - {response.text}")
                await message.answer(
                    f"⚠️ Оплата прошла, но возникла ошибка при активации.\n"
                    f"Напишите в поддержку с этим ID: {payment.telegram_payment_charge_id}"
                )
                
    except Exception as e:
        logger.error(f"Payment processing error: {e}")
        await message.answer(
            f"⚠️ Ошибка обработки платежа.\n"
            f"ID платежа: {payment.telegram_payment_charge_id}\n"
            f"Обратитесь в поддержку."
        )


@router.message(F.text == "🛢️ Бочка")
async def show_barrel(message: types.Message):
    """Показать статус бочки"""
    user_id = message.from_user.id
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_URL}/v1/shop/barrel",
                headers={"X-User-Id": str(user_id)}
            )
            
            if response.status_code == 200:
                data = response.json()
                barrel = data["barrel"]
                progress = barrel["progress"]
                target = barrel["target"]
                completions = barrel["completions"]
                
                # Визуальный прогресс-бар
                filled = int(progress / 10)
                empty = 10 - filled
                progress_bar = "🟦" * filled + "⬜" * empty
                
                await message.answer(
                    f"🛢️ <b>Бочка наград</b>\n\n"
                    f"{progress_bar}\n"
                    f"<b>{progress}/{target}</b> покупок\n\n"
                    f"🎁 Награда: <b>1 месяц VPN</b>\n"
                    f"🏆 Заполнено раз: {completions}\n\n"
                    f"<i>Делай любые покупки - бочка наполняется!</i>",
                    parse_mode="HTML"
                )
            else:
                await message.answer("❌ Ошибка загрузки данных")
    except Exception as e:
        logger.error(f"Barrel status error: {e}")
        await message.answer("❌ Ошибка соединения")


@router.message(F.text == "🛒 Магазин")
async def show_shop_menu(message: types.Message):
    """Показать меню магазина"""
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="⭐ Купить монеты", callback_data="shop_coins")],
            [types.InlineKeyboardButton(text="🛡️ VPN пакеты", callback_data="shop_vpn")],
            [types.InlineKeyboardButton(text="⚡ Бусты", callback_data="shop_boosts")],
            [types.InlineKeyboardButton(text="👑 Премиум предметы", callback_data="shop_premium")],
            [types.InlineKeyboardButton(text="🛢️ Бочка", callback_data="shop_barrel")],
            [types.InlineKeyboardButton(text="🎮 Открыть Mini App", callback_data="open_app")],
        ]
    )
    
    await message.answer(
        "🛒 <b>Магазин</b>\n\n"
        "Выберите категорию товаров:\n\n"
        "🛢️ <i>100 покупок = месяц VPN бесплатно!</i>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


from aiogram.filters import Command

@router.message(Command("buystars"))
async def buystars_command(message: types.Message):
    """Команда /buystars - купить внутриигровые монеты"""
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="100 ⭐ - 10 Telegram Stars", callback_data="buy_coins_100")],
            [types.InlineKeyboardButton(text="550 ⭐ - 45 TG Stars (+10%)", callback_data="buy_coins_500")],
            [types.InlineKeyboardButton(text="1250 ⭐ - 80 TG Stars (+25%)", callback_data="buy_coins_1000")],
            [types.InlineKeyboardButton(text="7000 ⭐ - 350 TG Stars (+40%)", callback_data="buy_coins_5000")],
        ]
    )
    
    await message.answer(
        "⭐ <b>Купить игровые монеты</b>\n\n"
        "Выберите пакет:\n\n"
        "• 100 ⭐ - <b>10</b> TG Stars\n"
        "• 550 ⭐ - <b>45</b> TG Stars (+10% бонус)\n"
        "• 1250 ⭐ - <b>80</b> TG Stars (+25% бонус)\n"
        "• 7000 ⭐ - <b>350</b> TG Stars (+40% бонус)\n\n"
        "<i>Оплата через Telegram Stars</i>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data == "shop_coins")
async def show_coins_products(callback: types.CallbackQuery):
    """Показать пакеты монет"""
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="100 ⭐ - 10 TG Stars", callback_data="buy_coins_100")],
            [types.InlineKeyboardButton(text="550 ⭐ - 45 TG Stars (+10%)", callback_data="buy_coins_500")],
            [types.InlineKeyboardButton(text="1250 ⭐ - 80 TG Stars (+25%)", callback_data="buy_coins_1000")],
            [types.InlineKeyboardButton(text="7000 ⭐ - 350 TG Stars (+40%)", callback_data="buy_coins_5000")],
            [types.InlineKeyboardButton(text="◀️ Назад", callback_data="shop_back")],
        ]
    )
    
    await callback.message.edit_text(
        "⭐ <b>Купить игровые монеты</b>\n\n"
        "• 100 ⭐ - <b>10</b> TG Stars\n"
        "• 550 ⭐ - <b>45</b> TG Stars (+10%)\n"
        "• 1250 ⭐ - <b>80</b> TG Stars (+25%)\n"
        "• 7000 ⭐ - <b>350</b> TG Stars (+40%)\n\n"
        "<i>Монеты используются для покупок в магазине!</i>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data == "shop_barrel")
async def show_barrel_callback(callback: types.CallbackQuery):
    """Показать бочку через callback"""
    user_id = callback.from_user.id
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_URL}/v1/shop/barrel",
                headers={"X-User-Id": str(user_id)}
            )
            
            if response.status_code == 200:
                data = response.json()
                barrel = data["barrel"]
                progress = barrel["progress"]
                
                filled = int(progress / 10)
                empty = 10 - filled
                progress_bar = "🟦" * filled + "⬜" * empty
                
                keyboard = types.InlineKeyboardMarkup(
                    inline_keyboard=[
                        [types.InlineKeyboardButton(text="◀️ Назад", callback_data="shop_back")]
                    ]
                )
                
                await callback.message.edit_text(
                    f"🛢️ <b>Бочка наград</b>\n\n"
                    f"{progress_bar}\n"
                    f"<b>{progress}/100</b> покупок\n\n"
                    f"🎁 Награда: <b>1 месяц VPN</b>\n"
                    f"🏆 Заполнено: {barrel['completions']} раз\n\n"
                    f"<i>Любая покупка = +1 к бочке!</i>",
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
            else:
                await callback.answer("Ошибка загрузки", show_alert=True)
    except Exception as e:
        logger.error(f"Barrel callback error: {e}")
        await callback.answer("Ошибка", show_alert=True)


@router.callback_query(F.data == "shop_vpn")
async def show_vpn_products(callback: types.CallbackQuery):
    """Показать VPN пакеты"""
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="🛡️ 3 дня - 30⭐", callback_data="buy_vpn_3days")],
            [types.InlineKeyboardButton(text="🔐 1 неделя - 60⭐", callback_data="buy_vpn_1week")],
            [types.InlineKeyboardButton(text="🏰 2 недели - 100⭐", callback_data="buy_vpn_2weeks")],
            [types.InlineKeyboardButton(text="🚀 1 месяц - 180⭐", callback_data="buy_vpn_1month")],
            [types.InlineKeyboardButton(text="◀️ Назад", callback_data="shop_back")],
        ]
    )
    
    await callback.message.edit_text(
        "🛡️ **VPN Пакеты**\n\n"
        "Выберите пакет VPN доступа:\n\n"
        "• 3 дня - **30** ⭐\n"
        "• 1 неделя - **60** ⭐\n"
        "• 2 недели - **100** ⭐\n"
        "• 1 месяц - **180** ⭐",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "shop_boosts")
async def show_boost_products(callback: types.CallbackQuery):
    """Показать бусты"""
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="⭐ XP x2 (24ч) - 50⭐", callback_data="buy_xp_boost_x2")],
            [types.InlineKeyboardButton(text="🌟 XP x3 (12ч) - 75⭐", callback_data="buy_xp_boost_x3")],
            [types.InlineKeyboardButton(text="🤖 Автокормушка (7д) - 100⭐", callback_data="buy_auto_feeder")],
            [types.InlineKeyboardButton(text="◀️ Назад", callback_data="shop_back")],
        ]
    )
    
    await callback.message.edit_text(
        "⚡ **Бусты**\n\n"
        "• XP Буст x2 (24 часа) - **50** ⭐\n"
        "• XP Буст x3 (12 часов) - **75** ⭐\n"
        "• Автокормушка (7 дней) - **100** ⭐",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "shop_premium")
async def show_premium_products(callback: types.CallbackQuery):
    """Показать премиум предметы"""
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="👑 Корона (+25% XP) - 150⭐", callback_data="buy_crown")],
            [types.InlineKeyboardButton(text="◀️ Назад", callback_data="shop_back")],
        ]
    )
    
    await callback.message.edit_text(
        "👑 **Премиум предметы**\n\n"
        "• Королевская корона - **150** ⭐\n"
        "  _+25% к получаемому опыту навсегда_",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "shop_back")
async def back_to_shop(callback: types.CallbackQuery):
    """Назад в главное меню магазина"""
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="🛡️ VPN пакеты", callback_data="shop_vpn")],
            [types.InlineKeyboardButton(text="⚡ Бусты", callback_data="shop_boosts")],
            [types.InlineKeyboardButton(text="👑 Премиум предметы", callback_data="shop_premium")],
        ]
    )
    
    await callback.message.edit_text(
        "🛒 **Магазин**\n\n"
        "Выберите категорию товаров:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@router.callback_query(F.data.startswith("buy_"))
async def process_buy(callback: types.CallbackQuery):
    """Обработка покупки"""
    product_id = callback.data.replace("buy_", "")
    
    if product_id not in STAR_PRICES:
        await callback.answer("❌ Товар не найден", show_alert=True)
        return
    
    await callback.answer()
    await send_invoice(callback.message, product_id)
