"""
Internationalization (i18n) system
10 most popular languages for Telegram Mini Apps
"""

TRANSLATIONS = {
    # === RUSSIAN (Default) ===
    "ru": {
        "lang_name": "Русский",
        "lang_flag": "🇷🇺",
        
        # Welcome
        "welcome_title": "Добро пожаловать в TamaGuardian!",
        "welcome_text": "Ваш виртуальный питомец ждёт вас!",
        
        # Pet states
        "pet_hungry": "Ваш питомец голоден!",
        "pet_tired": "Ваш питомец устал...",
        "pet_sad": "Ваш питомец грустит...",
        "pet_happy": "Ваш питомец очень счастлив!",
        "pet_fine": "Ваш питомец в порядке!",
        "pet_sick": "Ваш питомец болеет! Дайте лекарство!",
        "pet_sleeping": "Zzz... Ваш питомец спит...",
        "pet_dirty": "Вашему питомцу нужна ванна!",
        
        # Actions
        "action_feed": "КОРМ",
        "action_play": "ИГРАТЬ",
        "action_sleep": "СПАТЬ",
        "action_wake": "БУДИТЬ",
        "action_bath": "ВАННА",
        "action_train": "УЧИТЬ",
        "action_heal": "ЛЕЧИТЬ",
        "action_light_on": "ВКЛ СВЕТ",
        "action_light_off": "ВЫКЛ СВЕТ",
        "action_feed_done": "Вы покормили питомца!",
        "action_play_done": "Вы поиграли с питомцем!",
        "action_sleep_done": "Питомец сладко спит!",
        
        # Button labels (dynamic)
        "sleep_btn": "СПАТЬ",
        "wake_btn": "БУДИТЬ",
        "light_on_btn": "ВКЛ СВЕТ",
        "light_off_btn": "ВЫКЛ СВЕТ",
        
        # Navigation
        "nav_home": "ДОМ",
        "nav_grow": "РОСТ",
        "nav_style": "СТИЛЬ",
        "nav_shop": "МАГАЗ",
        "nav_top": "ТОП",
        "nav_menu": "МЕНЮ",
        
        # Stats
        "stat_hunger": "Сытость",
        "stat_energy": "Энергия",
        "stat_happiness": "Счастье",
        "stat_hygiene": "Чистота",
        "stat_health": "Здоровье",
        "stat_level": "Уровень",
        "stat_xp": "Опыт",
        
        # Shop
        "shop_title": "🛒 МАГАЗИН",
        "shop_buy": "Купить",
        "shop_price": "Цена",
        "shop_category_all": "Все",
        "shop_category_food": "Еда",
        "shop_category_clothing": "Одежда",
        "shop_category_accessory": "Аксессуары",
        "shop_category_boost": "Бусты",
        "shop_category_vpn": "VPN",
        "shop_purchase_success": "Покупка успешна!",
        "shop_purchase_telegram": "Оплата через Telegram Stars",
        
        # Modals
        "wardrobe_title": "👕 ГАРДЕРОБ",
        "settings_title": "⚙️ НАСТРОЙКИ",
        "leaderboard_title": "🏆 РЕЙТИНГ",
        
        # Wardrobe
        "equipped": "НАДЕТО",
        "inventory": "ИНВЕНТАРЬ",
        "no_items": "📦 Нет предметов!",
        "buy_in_shop": "Купите что-нибудь в МАГАЗИНЕ",
        "all_equipped": "✔ Всё надето!",
        
        # Market
        "market_title": "🏪 МАРКЕТ",
        "market_p2p": "P2P Торговая площадка",
        "market_desc": "Покупай и продавай игрокам",
        "commission": "Комиссия: 3%",
        "sell_item": "💰 ПРОДАТЬ",
        "sell_title": "💰 ПРОДАЖА",
        "select_item": "Выберите предмет:",
        "set_price": "Установите цену (Звёзды):",
        "you_receive": "Вы получите",
        "after_fee": "после комиссии 3%",
        "list_for_sale": "✔ ВЫСТАВИТЬ",
        "my_listings": "📝 МОИ ЛОТЫ",
        "no_listings": "Нет товаров",
        "be_first": "Будь первым!",
        "cancel": "Отмена",
        "buy": "КУПИТЬ",
        
        # Stars
        "buy_stars": "⭐ КУПИТЬ ЗВЁЗДЫ",
        "your_balance": "Ваш баланс",
        "stars": "звёзд",
        "tap_to_buy": "Нажми для покупки",
        
        # Loading
        "loading": "Загрузка...",
        
        # Invite
        "invite_title": "👥 ПРИГЛАСИТЬ ДРУЗЕЙ",
        "invite_reward": "Награда за каждого!",
        "invited": "ПРИГЛАШЕНО",
        "per_friend": "ЗА ДРУГА",
        "share_link": "📤 ПОДЕЛИТЬСЯ",
        "your_code": "Ваш код:",
        
        # Change Pet
        "change_pet": "🔄 СМЕНИТЬ ПИТОМЦА",
        "select_new_pet": "ВЫБРАТЬ НОВОГО",
        "progress_saved": "⚠️ Прогресс будет сохранён",
        
        # Barrel
        "barrel_title": "Бочка наград",
        "barrel_progress": "Прогресс",
        "barrel_reward": "Награда: 1 месяц VPN бесплатно!",
        "barrel_filled": "БОЧКА ЗАПОЛНЕНА!",
        "barrel_purchases": "покупок",
        
        # Progression
        "progression_title": "Прогрессия",
        "progression_level": "Уровень",
        "progression_next_evo": "Следующая эволюция",
        "progression_current": "Текущая",
        "progression_bonuses": "Активные бонусы",
        "progression_rewards": "Награды за уровень",
        
        # Evolution names
        "evo_baby": "Малыш",
        "evo_kitten": "Котёнок",
        "evo_cat": "Кот",
        "evo_wise": "Мудрый кот",
        "evo_master": "Мастер",
        "evo_legend": "Легенда",
        "evo_mythic": "Мифический",
        "evo_divine": "Божественный",
        
        # Rewards
        "rewards_title": "Награды",
        "rewards_vpn_balance": "Баланс VPN",
        "rewards_hours": "часов",
        "rewards_invite_friend": "Пригласить друга",
        "rewards_daily": "Ежедневный бонус",
        "rewards_streak": "Дней подряд",
        
        # Support
        "support_title": "Поддержка",
        "support_text": "Нужна помощь? Напишите нам!",
        "support_faq": "Частые вопросы",
        "support_contact": "Связаться с поддержкой",
        
        # FAQ
        "faq_q1": "Как кормить питомца?",
        "faq_a1": "Нажмите кнопку 🍖 FEED или используйте еду из инвентаря",
        "faq_q2": "Как получить VPN?",
        "faq_a2": "Играйте, прокачивайте питомца и приглашайте друзей!",
        "faq_q3": "Что такое бочка?",
        "faq_a3": "100 любых покупок = 1 месяц VPN бесплатно!",
        "faq_q4": "Зачем нужна одежда?",
        "faq_a4": "Одежда даёт бонусы: +XP, -потеря энергии и т.д.",
        "faq_q5": "Как повысить уровень?",
        "faq_a5": "Кормите, играйте и ухаживайте за питомцем для XP",
        
        # Errors
        "error_auth": "Ошибка авторизации",
        "error_network": "Ошибка сети",
        "error_unknown": "Неизвестная ошибка",
        
        # Bot messages
        "bot_welcome": "🐾 <b>Добро пожаловать в TMA Tamagotchi!</b>\n\nВаш виртуальный питомец ждёт вас!",
        "bot_open_app": "🎮 Открыть Mini App",
        "bot_shop": "🛒 Магазин",
        "bot_barrel": "🛢️ Бочка",
        "bot_rewards": "🎁 Награды",
        "bot_stats": "📊 Статистика",
        "bot_support": "❓ Поддержка",
    },
    
    # === ENGLISH ===
    "en": {
        "lang_name": "English",
        "lang_flag": "🇬🇧",
        
        "welcome_title": "Welcome to TamaGuardian!",
        "welcome_text": "Your virtual pet is waiting for you!",
        
        # Pet states
        "pet_hungry": "Your pet is hungry!",
        "pet_tired": "Your pet is tired...",
        "pet_sad": "Your pet is sad...",
        "pet_happy": "Your pet is very happy!",
        "pet_fine": "Your pet is doing fine!",
        "pet_sick": "Your pet is sick! Give medicine!",
        "pet_sleeping": "Zzz... Your pet is sleeping...",
        "pet_dirty": "Your pet needs a bath!",
        
        # Actions
        "action_feed": "FEED",
        "action_play": "PLAY",
        "action_sleep": "SLEEP",
        "action_wake": "WAKE",
        "action_bath": "BATH",
        "action_train": "TRAIN",
        "action_heal": "HEAL",
        "action_light_on": "LIGHT ON",
        "action_light_off": "LIGHT OFF",
        "action_feed_done": "You fed your pet!",
        "action_play_done": "You played with your pet!",
        "action_sleep_done": "Your pet is sleeping sweetly!",
        
        # Button labels (dynamic)
        "sleep_btn": "SLEEP",
        "wake_btn": "WAKE",
        "light_on_btn": "LIGHT ON",
        "light_off_btn": "LIGHT OFF",
        
        # Navigation
        "nav_home": "HOME",
        "nav_grow": "GROW",
        "nav_style": "STYLE",
        "nav_shop": "SHOP",
        "nav_top": "TOP",
        "nav_menu": "MENU",
        
        # Stats
        "stat_hunger": "Hunger",
        "stat_energy": "Energy",
        "stat_happiness": "Happiness",
        "stat_hygiene": "Hygiene",
        "stat_health": "Health",
        "stat_level": "Level",
        "stat_xp": "XP",
        
        # Shop
        "shop_title": "🛒 SHOP",
        "shop_buy": "Buy",
        "shop_price": "Price",
        "shop_category_all": "All",
        "shop_category_food": "Food",
        "shop_category_clothing": "Clothing",
        "shop_category_accessory": "Accessories",
        "shop_category_boost": "Boosts",
        "shop_category_vpn": "VPN",
        "shop_purchase_success": "Purchase successful!",
        "shop_purchase_telegram": "Pay with Telegram Stars",
        
        # Modals
        "wardrobe_title": "👕 WARDROBE",
        "settings_title": "⚙️ SETTINGS",
        "leaderboard_title": "🏆 RATING",
        
        # Wardrobe
        "equipped": "EQUIPPED",
        "inventory": "INVENTORY",
        "no_items": "📦 No items yet!",
        "buy_in_shop": "Buy something in SHOP",
        "all_equipped": "✔ All items equipped!",
        
        # Market
        "market_title": "🏪 MARKET",
        "market_p2p": "P2P Marketplace",
        "market_desc": "Buy & sell items from players",
        "commission": "Commission: 3%",
        "sell_item": "💰 SELL MY ITEM",
        "sell_title": "💰 SELL ITEM",
        "select_item": "Select item to sell:",
        "set_price": "Set price (Stars):",
        "you_receive": "You'll receive",
        "after_fee": "after 3% fee",
        "list_for_sale": "✔ LIST FOR SALE",
        "my_listings": "📝 MY LISTINGS",
        "no_listings": "No items for sale",
        "be_first": "Be the first to list!",
        "cancel": "Cancel",
        "buy": "BUY",
        
        # Stars
        "buy_stars": "⭐ BUY TELEGRAM STARS",
        "your_balance": "Your balance",
        "stars": "stars",
        "tap_to_buy": "Tap to buy stars",
        
        # Loading
        "loading": "Loading...",
        
        # Invite
        "invite_title": "👥 INVITE FRIENDS",
        "invite_reward": "Get rewards for each friend!",
        "invited": "INVITED",
        "per_friend": "PER FRIEND",
        "share_link": "📤 SHARE LINK",
        "your_code": "Your code:",
        
        # Change Pet
        "change_pet": "🔄 CHANGE PET",
        "select_new_pet": "SELECT NEW PET",
        "progress_saved": "⚠️ Your progress will be saved",
        
        "barrel_title": "Reward Barrel",
        "barrel_progress": "Progress",
        "barrel_reward": "Reward: 1 month VPN FREE!",
        "barrel_filled": "BARREL FILLED!",
        "barrel_purchases": "purchases",
        
        "progression_title": "Progression",
        "progression_level": "Level",
        "progression_next_evo": "Next Evolution",
        "progression_current": "Current",
        "progression_bonuses": "Active Bonuses",
        "progression_rewards": "Level Rewards",
        
        "evo_baby": "Baby",
        "evo_kitten": "Kitten",
        "evo_cat": "Cat",
        "evo_wise": "Wise Cat",
        "evo_master": "Master",
        "evo_legend": "Legend",
        "evo_mythic": "Mythical",
        "evo_divine": "Divine",
        
        "rewards_title": "Rewards",
        "rewards_vpn_balance": "VPN Balance",
        "rewards_hours": "hours",
        "rewards_invite_friend": "Invite Friend",
        "rewards_daily": "Daily Bonus",
        "rewards_streak": "Day Streak",
        
        "support_title": "Support",
        "support_text": "Need help? Contact us!",
        "support_faq": "FAQ",
        "support_contact": "Contact Support",
        
        "faq_q1": "How to feed my pet?",
        "faq_a1": "Click 🍖 FEED button or use food from inventory",
        "faq_q2": "How to get VPN?",
        "faq_a2": "Play, level up your pet and invite friends!",
        "faq_q3": "What is the barrel?",
        "faq_a3": "100 purchases of any amount = 1 month FREE VPN!",
        "faq_q4": "Why need clothing?",
        "faq_a4": "Clothing gives bonuses: +XP, -energy loss, etc.",
        "faq_q5": "How to level up?",
        "faq_a5": "Feed, play and take care of your pet for XP",
        
        "error_auth": "Authentication error",
        "error_network": "Network error",
        "error_unknown": "Unknown error",
        
        "bot_welcome": "🐾 <b>Welcome to TMA Tamagotchi!</b>\n\nYour virtual pet is waiting!",
        "bot_open_app": "🎮 Open Mini App",
        "bot_shop": "🛒 Shop",
        "bot_barrel": "🛢️ Barrel",
        "bot_rewards": "🎁 Rewards",
        "bot_stats": "📊 Stats",
        "bot_support": "❓ Support",
    },
    
    # === SPANISH ===
    "es": {
        "lang_name": "Español",
        "lang_flag": "🇪🇸",
        
        "welcome_title": "¡Bienvenido a TamaGuardian!",
        "welcome_text": "¡Tu mascota virtual te espera!",
        
        "pet_hungry": "¡Tu mascota tiene hambre!",
        "pet_tired": "Tu mascota está cansada...",
        "pet_sad": "Tu mascota está triste...",
        "pet_happy": "¡Tu mascota está muy feliz!",
        "pet_fine": "¡Tu mascota está bien!",
        
        "action_feed": "Alimentar",
        "action_play": "Jugar",
        "action_sleep": "Dormir",
        
        "stat_hunger": "Hambre",
        "stat_energy": "Energía",
        "stat_happiness": "Felicidad",
        "stat_level": "Nivel",
        "stat_xp": "EXP",
        
        "shop_title": "Tienda",
        "shop_buy": "Comprar",
        "barrel_title": "Barril de Recompensas",
        "barrel_reward": "¡Recompensa: 1 mes VPN GRATIS!",
        
        "support_title": "Soporte",
        "support_text": "¿Necesitas ayuda? ¡Contáctanos!",
    },
    
    # === PORTUGUESE ===
    "pt": {
        "lang_name": "Português",
        "lang_flag": "🇧🇷",
        
        "welcome_title": "Bem-vindo ao TamaGuardian!",
        "welcome_text": "Seu pet virtual está esperando!",
        
        "pet_hungry": "Seu pet está com fome!",
        "pet_tired": "Seu pet está cansado...",
        "pet_happy": "Seu pet está muito feliz!",
        
        "action_feed": "Alimentar",
        "action_play": "Brincar",
        "action_sleep": "Dormir",
        
        "shop_title": "Loja",
        "barrel_title": "Barril de Recompensas",
        "support_title": "Suporte",
    },
    
    # === GERMAN ===
    "de": {
        "lang_name": "Deutsch",
        "lang_flag": "🇩🇪",
        
        "welcome_title": "Willkommen bei TamaGuardian!",
        "welcome_text": "Dein virtuelles Haustier wartet auf dich!",
        
        "pet_hungry": "Dein Haustier ist hungrig!",
        "pet_tired": "Dein Haustier ist müde...",
        "pet_happy": "Dein Haustier ist sehr glücklich!",
        
        "action_feed": "Füttern",
        "action_play": "Spielen",
        "action_sleep": "Schlafen",
        
        "shop_title": "Shop",
        "barrel_title": "Belohnungsfass",
        "support_title": "Support",
    },
    
    # === FRENCH ===
    "fr": {
        "lang_name": "Français",
        "lang_flag": "🇫🇷",
        
        "welcome_title": "Bienvenue à TamaGuardian!",
        "welcome_text": "Votre animal virtuel vous attend!",
        
        "pet_hungry": "Votre animal a faim!",
        "pet_tired": "Votre animal est fatigué...",
        "pet_happy": "Votre animal est très heureux!",
        
        "action_feed": "Nourrir",
        "action_play": "Jouer",
        "action_sleep": "Dormir",
        
        "shop_title": "Boutique",
        "barrel_title": "Tonneau de Récompenses",
        "support_title": "Support",
    },
    
    # === ITALIAN ===
    "it": {
        "lang_name": "Italiano",
        "lang_flag": "🇮🇹",
        
        "welcome_title": "Benvenuto in TamaGuardian!",
        "welcome_text": "Il tuo animale virtuale ti aspetta!",
        
        "pet_hungry": "Il tuo animale ha fame!",
        "pet_happy": "Il tuo animale è molto felice!",
        
        "action_feed": "Nutrire",
        "action_play": "Giocare",
        "action_sleep": "Dormire",
        
        "shop_title": "Negozio",
        "support_title": "Supporto",
    },
    
    # === TURKISH ===
    "tr": {
        "lang_name": "Türkçe",
        "lang_flag": "🇹🇷",
        
        "welcome_title": "TamaGuardian'a Hoş Geldiniz!",
        "welcome_text": "Sanal evcil hayvanınız sizi bekliyor!",
        
        "pet_hungry": "Evcil hayvanınız aç!",
        "pet_happy": "Evcil hayvanınız çok mutlu!",
        
        "action_feed": "Besle",
        "action_play": "Oyna",
        "action_sleep": "Uyut",
        
        "shop_title": "Mağaza",
        "support_title": "Destek",
    },
    
    # === INDONESIAN ===
    "id": {
        "lang_name": "Indonesia",
        "lang_flag": "🇮🇩",
        
        "welcome_title": "Selamat datang di TamaGuardian!",
        "welcome_text": "Hewan peliharaan virtualmu menunggu!",
        
        "pet_hungry": "Hewan peliharaanmu lapar!",
        "pet_happy": "Hewan peliharaanmu sangat bahagia!",
        
        "action_feed": "Beri Makan",
        "action_play": "Bermain",
        "action_sleep": "Tidur",
        
        "shop_title": "Toko",
        "support_title": "Bantuan",
    },
    
    # === UKRAINIAN ===
    "uk": {
        "lang_name": "Українська",
        "lang_flag": "🇺🇦",
        
        "welcome_title": "Ласкаво просимо до TamaGuardian!",
        "welcome_text": "Ваш віртуальний улюбленець чекає на вас!",
        
        "pet_hungry": "Ваш улюбленець голодний!",
        "pet_tired": "Ваш улюбленець втомився...",
        "pet_happy": "Ваш улюбленець дуже щасливий!",
        "pet_fine": "Ваш улюбленець в порядку!",
        
        "action_feed": "Годувати",
        "action_play": "Грати",
        "action_sleep": "Спати",
        
        "stat_hunger": "Ситість",
        "stat_energy": "Енергія",
        "stat_happiness": "Щастя",
        
        "shop_title": "Магазин",
        "barrel_title": "Бочка нагород",
        "barrel_reward": "Нагорода: 1 місяць VPN безкоштовно!",
        
        "support_title": "Підтримка",
        "support_text": "Потрібна допомога? Напишіть нам!",
    },
}


def get_text(key: str, lang: str = "ru") -> str:
    """Get translated text by key"""
    # Fallback chain: requested lang -> English -> Russian -> key
    if lang in TRANSLATIONS and key in TRANSLATIONS[lang]:
        return TRANSLATIONS[lang][key]
    if key in TRANSLATIONS.get("en", {}):
        return TRANSLATIONS["en"][key]
    if key in TRANSLATIONS.get("ru", {}):
        return TRANSLATIONS["ru"][key]
    return key


def get_available_languages() -> list:
    """Get list of available languages"""
    return [
        {"code": code, "name": data["lang_name"], "flag": data["lang_flag"]}
        for code, data in TRANSLATIONS.items()
    ]


def detect_language(telegram_language_code: str = None) -> str:
    """Detect user language from Telegram language code"""
    if telegram_language_code and telegram_language_code[:2] in TRANSLATIONS:
        return telegram_language_code[:2]
    return "ru"  # Default to Russian
