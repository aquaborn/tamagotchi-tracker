"""
Admin commands for Tamagochi bot
Commands:
/admin - Show admin help
/give_stars <user_id> <amount> - Give stars to user
/give_item <user_id> <item_id> - Give item to user
/give_vpn <user_id> <hours> - Give VPN hours to user
/user_info <user_id> - Get user info
/set_level <user_id> <level> - Set user level
/broadcast <message> - Send message to all users
"""

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import logging

from settings import settings

logger = logging.getLogger(__name__)
router = Router()

# Database connection
engine = create_async_engine(settings.database_url, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in settings.admin_ids


@router.message(Command("admin"))
async def admin_help(message: Message):
    """Show admin commands help"""
    if not is_admin(message.from_user.id):
        return
    
    help_text = """
🔐 <b>ADMIN COMMANDS</b>

<b>Stars & Currency:</b>
/give_stars &lt;user_id&gt; &lt;amount&gt;
/take_stars &lt;user_id&gt; &lt;amount&gt;

<b>Items & Inventory:</b>
/give_item &lt;user_id&gt; &lt;item_id&gt; [quantity]
/list_items - Show all shop items

<b>VPN:</b>
/give_vpn &lt;user_id&gt; &lt;hours&gt;

<b>User Management:</b>
/user_info &lt;user_id&gt;
/set_level &lt;user_id&gt; &lt;level&gt;
/set_xp &lt;user_id&gt; &lt;xp&gt;

<b>🎰 Star Roulette:</b>
/roulette - статус рулетки
/roulette_draw - провести розыгрыш
/roulette_participants - участники

<b>Statistics:</b>
/stats - Bot statistics
/top_users - Top users by level
/users - List all users with IDs

<b>Note:</b> user_id = Telegram ID
    """
    await message.answer(help_text)


@router.message(Command("give_stars"))
async def give_stars(message: Message):
    """Give stars to user: /give_stars <user_id> <amount>"""
    if not is_admin(message.from_user.id):
        return
    
    args = message.text.split()[1:]
    if len(args) < 2:
        await message.answer("❌ Usage: /give_stars <user_id> <amount>")
        return
    
    try:
        user_id = int(args[0])
        amount = int(args[1])
    except ValueError:
        await message.answer("❌ Invalid user_id or amount")
        return
    
    async with async_session() as session:
        result = await session.execute(
            text("UPDATE users SET stars_balance = stars_balance + :amount WHERE telegram_id = :user_id RETURNING username, stars_balance"),
            {"user_id": user_id, "amount": amount}
        )
        row = result.fetchone()
        await session.commit()
        
        if row:
            await message.answer(f"✅ Gave {amount} ⭐ to @{row[0] or user_id}\nNew balance: {row[1]} ⭐")
        else:
            await message.answer(f"❌ User {user_id} not found")


@router.message(Command("take_stars"))
async def take_stars(message: Message):
    """Take stars from user: /take_stars <user_id> <amount>"""
    if not is_admin(message.from_user.id):
        return
    
    args = message.text.split()[1:]
    if len(args) < 2:
        await message.answer("❌ Usage: /take_stars <user_id> <amount>")
        return
    
    try:
        user_id = int(args[0])
        amount = int(args[1])
    except ValueError:
        await message.answer("❌ Invalid user_id or amount")
        return
    
    async with async_session() as session:
        result = await session.execute(
            text("UPDATE users SET stars_balance = GREATEST(0, stars_balance - :amount) WHERE telegram_id = :user_id RETURNING username, stars_balance"),
            {"user_id": user_id, "amount": amount}
        )
        row = result.fetchone()
        await session.commit()
        
        if row:
            await message.answer(f"✅ Took {amount} ⭐ from @{row[0] or user_id}\nNew balance: {row[1]} ⭐")
        else:
            await message.answer(f"❌ User {user_id} not found")


@router.message(Command("give_item"))
async def give_item(message: Message):
    """Give item to user: /give_item <user_id> <item_id> [quantity]"""
    if not is_admin(message.from_user.id):
        return
    
    args = message.text.split()[1:]
    if len(args) < 2:
        await message.answer("❌ Usage: /give_item <user_id> <item_id> [quantity]")
        return
    
    try:
        user_id = int(args[0])
        item_id = int(args[1])
        quantity = int(args[2]) if len(args) > 2 else 1
    except ValueError:
        await message.answer("❌ Invalid parameters")
        return
    
    async with async_session() as session:
        # Get user internal ID
        user_result = await session.execute(
            text("SELECT id, username FROM users WHERE telegram_id = :user_id"),
            {"user_id": user_id}
        )
        user = user_result.fetchone()
        
        if not user:
            await message.answer(f"❌ User {user_id} not found")
            return
        
        # Get item info
        item_result = await session.execute(
            text("SELECT name, emoji FROM shop_items WHERE id = :item_id"),
            {"item_id": item_id}
        )
        item = item_result.fetchone()
        
        if not item:
            await message.answer(f"❌ Item {item_id} not found")
            return
        
        # Check if user already has this item
        inv_result = await session.execute(
            text("SELECT id, quantity FROM user_inventory WHERE user_id = :uid AND item_id = :iid"),
            {"uid": user[0], "iid": item_id}
        )
        existing = inv_result.fetchone()
        
        if existing:
            await session.execute(
                text("UPDATE user_inventory SET quantity = quantity + :qty WHERE id = :inv_id"),
                {"qty": quantity, "inv_id": existing[0]}
            )
        else:
            await session.execute(
                text("INSERT INTO user_inventory (user_id, item_id, quantity) VALUES (:uid, :iid, :qty)"),
                {"uid": user[0], "iid": item_id, "qty": quantity}
            )
        
        await session.commit()
        await message.answer(f"✅ Gave {item[1]} {item[0]} x{quantity} to @{user[1] or user_id}")


@router.message(Command("give_vpn"))
async def give_vpn(message: Message):
    """Give VPN hours: /give_vpn <user_id> <hours>"""
    if not is_admin(message.from_user.id):
        return
    
    args = message.text.split()[1:]
    if len(args) < 2:
        await message.answer("❌ Usage: /give_vpn <user_id> <hours>")
        return
    
    try:
        user_id = int(args[0])
        hours = int(args[1])
    except ValueError:
        await message.answer("❌ Invalid parameters")
        return
    
    async with async_session() as session:
        result = await session.execute(
            text("UPDATE users SET vpn_hours_balance = vpn_hours_balance + :hours WHERE telegram_id = :user_id RETURNING username, vpn_hours_balance"),
            {"user_id": user_id, "hours": hours}
        )
        row = result.fetchone()
        await session.commit()
        
        if row:
            await message.answer(f"✅ Gave {hours}h VPN to @{row[0] or user_id}\nTotal: {row[1]}h 🛡️")
        else:
            await message.answer(f"❌ User {user_id} not found")


@router.message(Command("user_info"))
async def user_info(message: Message):
    """Get user info: /user_info <user_id>"""
    if not is_admin(message.from_user.id):
        return
    
    args = message.text.split()[1:]
    if len(args) < 1:
        await message.answer("❌ Usage: /user_info <user_id>")
        return
    
    try:
        user_id = int(args[0])
    except ValueError:
        await message.answer("❌ Invalid user_id")
        return
    
    async with async_session() as session:
        result = await session.execute(
            text("""
                SELECT 
                    telegram_id, username, first_name, 
                    level, experience, stars_balance, 
                    vpn_hours_balance, referral_count, streak_days,
                    pet_type, barrel_progress, total_purchases,
                    created_at
                FROM users WHERE telegram_id = :user_id
            """),
            {"user_id": user_id}
        )
        user = result.fetchone()
        
        if not user:
            await message.answer(f"❌ User {user_id} not found")
            return
        
        info = f"""
👤 <b>USER INFO</b>

<b>ID:</b> {user[0]}
<b>Username:</b> @{user[1] or 'N/A'}
<b>Name:</b> {user[2] or 'N/A'}

<b>Level:</b> {user[3]} (XP: {user[4]})
<b>Stars:</b> ⭐ {user[5]}
<b>VPN:</b> 🛡️ {user[6]}h
<b>Referrals:</b> 👥 {user[7]}
<b>Streak:</b> 🔥 {user[8]} days

<b>Pet:</b> {user[9] or 'None'}
<b>Barrel:</b> {user[10]}/100
<b>Purchases:</b> {user[11]}

<b>Joined:</b> {user[12].strftime('%Y-%m-%d') if user[12] else 'N/A'}
        """
        await message.answer(info)


@router.message(Command("set_level"))
async def set_level(message: Message):
    """Set user level: /set_level <user_id> <level>"""
    if not is_admin(message.from_user.id):
        return
    
    args = message.text.split()[1:]
    if len(args) < 2:
        await message.answer("❌ Usage: /set_level <user_id> <level>")
        return
    
    try:
        user_id = int(args[0])
        level = int(args[1])
    except ValueError:
        await message.answer("❌ Invalid parameters")
        return
    
    async with async_session() as session:
        result = await session.execute(
            text("UPDATE users SET level = :level WHERE telegram_id = :user_id RETURNING username"),
            {"user_id": user_id, "level": level}
        )
        row = result.fetchone()
        await session.commit()
        
        if row:
            await message.answer(f"✅ Set level {level} for @{row[0] or user_id}")
        else:
            await message.answer(f"❌ User {user_id} not found")


@router.message(Command("set_xp"))
async def set_xp(message: Message):
    """Set user XP: /set_xp <user_id> <xp>"""
    if not is_admin(message.from_user.id):
        return
    
    args = message.text.split()[1:]
    if len(args) < 2:
        await message.answer("❌ Usage: /set_xp <user_id> <xp>")
        return
    
    try:
        user_id = int(args[0])
        xp = int(args[1])
    except ValueError:
        await message.answer("❌ Invalid parameters")
        return
    
    async with async_session() as session:
        result = await session.execute(
            text("UPDATE users SET experience = :xp WHERE telegram_id = :user_id RETURNING username, experience"),
            {"user_id": user_id, "xp": xp}
        )
        row = result.fetchone()
        await session.commit()
        
        if row:
            await message.answer(f"✅ Set XP {xp} for @{row[0] or user_id}")
        else:
            await message.answer(f"❌ User {user_id} not found")


@router.message(Command("list_items"))
async def list_items(message: Message):
    """List all shop items"""
    if not is_admin(message.from_user.id):
        return
    
    async with async_session() as session:
        result = await session.execute(
            text("SELECT id, name, emoji, price_stars, category FROM shop_items ORDER BY id LIMIT 30")
        )
        items = result.fetchall()
        
        if not items:
            await message.answer("❌ No items in shop")
            return
        
        text_lines = ["🛒 <b>SHOP ITEMS</b>\n"]
        for item in items:
            text_lines.append(f"<b>{item[0]}.</b> {item[2]} {item[1]} - ⭐{item[3]} ({item[4]})")
        
        await message.answer("\n".join(text_lines))


@router.message(Command("stats"))
async def bot_stats(message: Message):
    """Show bot statistics"""
    if not is_admin(message.from_user.id):
        return
    
    async with async_session() as session:
        # Total users
        users_result = await session.execute(text("SELECT COUNT(*) FROM users"))
        total_users = users_result.scalar()
        
        # Active today (by last_activity_date)
        active_result = await session.execute(
            text("SELECT COUNT(*) FROM users WHERE last_activity_date = CURRENT_DATE")
        )
        active_today = active_result.scalar()
        
        # Total stars
        stars_result = await session.execute(text("SELECT SUM(stars_balance) FROM users"))
        total_stars = stars_result.scalar() or 0
        
        # Total purchases
        purchases_result = await session.execute(text("SELECT SUM(total_purchases) FROM users"))
        total_purchases = purchases_result.scalar() or 0
        
        stats_text = f"""
📊 <b>BOT STATISTICS</b>

👥 <b>Total Users:</b> {total_users}
📅 <b>Active Today:</b> {active_today}
⭐ <b>Total Stars:</b> {total_stars:,}
🛒 <b>Total Purchases:</b> {total_purchases:,}
        """
        await message.answer(stats_text)


@router.message(Command("top_users"))
async def top_users(message: Message):
    """Show top users by level"""
    if not is_admin(message.from_user.id):
        return
    
    async with async_session() as session:
        result = await session.execute(
            text("""
                SELECT username, first_name, level, experience, stars_balance 
                FROM users 
                ORDER BY level DESC, experience DESC 
                LIMIT 10
            """)
        )
        users = result.fetchall()
        
        if not users:
            await message.answer("❌ No users found")
            return
        
        text_lines = ["🏆 <b>TOP 10 USERS</b>\n"]
        for i, user in enumerate(users, 1):
            name = user[0] or user[1] or "Anonymous"
            text_lines.append(f"{i}. @{name} - LVL {user[2]} (XP: {user[3]}) ⭐{user[4]}")
        
        await message.answer("\n".join(text_lines))


@router.message(Command("users"))
async def list_users(message: Message):
    """List all users with Telegram IDs for admin reference"""
    if not is_admin(message.from_user.id):
        return
    
    async with async_session() as session:
        result = await session.execute(
            text("""
                SELECT 
                    telegram_id, 
                    username, 
                    first_name, 
                    level, 
                    stars_balance,
                    pet_type
                FROM users 
                ORDER BY created_at DESC 
                LIMIT 50
            """)
        )
        users = result.fetchall()
        
        if not users:
            await message.answer("❌ No users found")
            return
        
        text_lines = ["👥 <b>ALL USERS</b> (last 50)\n"]
        text_lines.append("<code>ID → @username (Level) ⭐stars</code>\n")
        
        for user in users:
            tg_id = user[0]
            username = f"@{user[1]}" if user[1] else user[2] or "Anonymous"
            level = user[3]
            stars = user[4]
            pet = user[5] or "-"
            
            text_lines.append(
                f"<code>{tg_id}</code> → {username} (L{level}) ⭐{stars} {pet}"
            )
        
        # Split message if too long
        full_text = "\n".join(text_lines)
        if len(full_text) > 4000:
            await message.answer("\n".join(text_lines[:30]))
            await message.answer("\n".join(text_lines[30:]))
        else:
            await message.answer(full_text)


# === STAR ROULETTE ADMIN COMMANDS ===

@router.message(Command("roulette"))
async def roulette_status(message: Message):
    """Показать статус рулетки"""
    if not is_admin(message.from_user.id):
        return
    
    import httpx
    from datetime import datetime, timezone
    
    # Получаем инфо о рулетке через API
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "http://api:8000/v1/rewards/roulette",
                headers={"X-Telegram-User-Id": str(message.from_user.id)},
                timeout=10
            )
            data = resp.json()
    except Exception as e:
        await message.answer(f"❌ API Error: {e}")
        return
    
    twist = data.get("twist", {})
    hours_left = data.get("time_left_seconds", 0) // 3600
    mins_left = (data.get("time_left_seconds", 0) % 3600) // 60
    
    status_text = f"""
🎰 <b>STAR ROULETTE STATUS</b>

🆔 ID: <code>{data.get('roulette_id', 'N/A')}</code>
💰 Банк: <b>{data.get('total_pool', 0)} ⭐</b>
👥 Участников: {data.get('participants_count', 0)}
⏰ До розыгрыша: {hours_left}ч {mins_left}м

🎯 Твист: {twist.get('emoji', '🎲')} <b>{twist.get('name', 'Базовый')}</b>
{twist.get('description', '')}

✅ Розыгрыш проведён: {'Да' if data.get('is_drawn') else 'Нет'}

<b>Commands:</b>
/roulette_draw - провести розыгрыш
/roulette_participants - список участников
    """
    await message.answer(status_text)


@router.message(Command("roulette_draw"))
async def roulette_draw(message: Message):
    """Провести розыгрыш рулетки"""
    if not is_admin(message.from_user.id):
        return
    
    import httpx
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "http://api:8000/v1/rewards/roulette/draw",
                headers={"X-Telegram-User-Id": str(message.from_user.id)},
                timeout=15
            )
            data = resp.json()
    except Exception as e:
        await message.answer(f"❌ API Error: {e}")
        return
    
    if not data.get("success"):
        await message.answer(f"❌ {data.get('message', 'Ошибка')}")
        return
    
    # Форматируем уведомление
    winners = data.get("winners", [])
    pool_total = data.get("pool_total", 0)
    
    result_text = f"""
🎉 <b>ROULETTE RESULTS!</b> 🎉
━━━━━━━━━━━━━━━━━━━━
🆔 {data.get('roulette_id')}
💰 Банк: <b>{pool_total} ⭐</b>
👥 Участников: {data.get('participants_count', 0)}
━━━━━━━━━━━━━━━━━━━━

🏆 <b>WINNERS:</b>
"""
    
    place_emojis = ["🥇", "🥈", "🥉"]
    
    for w in winners:
        place = w.get("place", 1)
        emoji = place_emojis[place-1] if place <= 3 else "🎖️"
        vpn_bonus = f" + {w['vpn_bonus']}h VPN!" if w.get('vpn_bonus', 0) > 0 else ""
        
        result_text += f"""
{emoji} <b>{place} место:</b>
   👤 @{w.get('username', 'user')} (ID: <code>{w['user_id']}</code>)
   💫 Выигрыш: <b>{w['prize']} ⭐</b>{vpn_bonus}
   📋 <code>/give_stars {w['user_id']} {w['prize']}</code>
"""
    
    result_text += "\n━━━━━━━━━━━━━━━━━━━━"
    
    await message.answer(result_text)
    
    # Если есть share texts, показываем отдельно
    share_texts = data.get("share_texts", [])
    if share_texts:
        await message.answer(
            "📢 <b>Share texts for winners:</b>\n\n" + 
            "\n---\n".join(share_texts)
        )


@router.message(Command("roulette_participants"))
async def roulette_participants(message: Message):
    """Показать участников рулетки"""
    if not is_admin(message.from_user.id):
        return
    
    import httpx
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "http://api:8000/v1/rewards/roulette/history",
                headers={"X-Telegram-User-Id": str(message.from_user.id)},
                timeout=10
            )
            data = resp.json()
    except Exception as e:
        await message.answer(f"❌ API Error: {e}")
        return
    
    today = data.get("today", {})
    
    text = f"""
🎰 <b>TODAY'S ROULETTE</b>

💰 Банк: {today.get('pool_total', 0)} ⭐
👥 Участников: {today.get('participants', 0)}
✅ Розыгрыш: {'Проведён' if today.get('drawn') else 'Ожидается'}
    """
    
    if today.get("winners"):
        text += "\n🏆 <b>Winners:</b>\n"
        for w in today["winners"]:
            text += f"  {w['place']}. @{w.get('username')} - {w['prize']}⭐\n"
    
    await message.answer(text)
