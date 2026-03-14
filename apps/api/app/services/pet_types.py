"""
Pet Types - 10 free + 10 premium trending pets
"""

# Free pets - available to everyone
FREE_PETS = [
    {
        "id": "kitty",
        "name": "Kitty",
        "emoji": "🐱",
        "description": "Classic cute kitty. Your loyal companion!",
        "color": "#FFB347",
        "color_dark": "#E89830",
        "rarity": "common",
        "price_stars": 0,
        "visual": {
            "body": "round",
            "ears": "triangle",
            "tail": "long",
            "whiskers": True,
            "spots": None
        }
    },
    {
        "id": "puppy",
        "name": "Puppy",
        "emoji": "🐶",
        "description": "Playful and loyal puppy!",
        "color": "#D4A574",
        "color_dark": "#B8956A",
        "rarity": "common",
        "price_stars": 0,
        "visual": {
            "body": "round",
            "ears": "floppy",
            "tail": "short",
            "whiskers": False,
            "tongue": True
        }
    },
    {
        "id": "bunny",
        "name": "Bunny",
        "emoji": "🐰",
        "description": "Soft fluffy bunny with long ears!",
        "color": "#F5F5F5",
        "color_dark": "#E0E0E0",
        "rarity": "common",
        "price_stars": 0,
        "visual": {
            "body": "oval",
            "ears": "long",
            "tail": "puff",
            "whiskers": True,
            "inner_ear": "#FFB6C1"
        }
    },
    {
        "id": "hamster",
        "name": "Hamster",
        "emoji": "🐹",
        "description": "Chubby cheeks hamster!",
        "color": "#F4A460",
        "color_dark": "#D2691E",
        "rarity": "common",
        "price_stars": 0,
        "visual": {
            "body": "chubby",
            "ears": "small_round",
            "tail": None,
            "cheeks": True,
            "whiskers": True
        }
    },
    {
        "id": "bear_cub",
        "name": "Bear Cub",
        "emoji": "🐻",
        "description": "Adorable little bear cub!",
        "color": "#8B4513",
        "color_dark": "#654321",
        "rarity": "common",
        "price_stars": 0,
        "visual": {
            "body": "big_round",
            "ears": "bear",
            "tail": None,
            "snout": True,
            "whiskers": False
        }
    },
    {
        "id": "fox",
        "name": "Fox",
        "emoji": "🦊",
        "description": "Clever and cute fox!",
        "color": "#FF6B35",
        "color_dark": "#E55A2B",
        "rarity": "common",
        "price_stars": 0,
        "visual": {
            "body": "sleek",
            "ears": "triangle_big",
            "tail": "fluffy",
            "whiskers": True,
            "white_belly": True
        }
    },
    {
        "id": "panda",
        "name": "Panda",
        "emoji": "🐼",
        "description": "Lazy bamboo-loving panda!",
        "color": "#FFFFFF",
        "color_dark": "#E8E8E8",
        "rarity": "common",
        "price_stars": 0,
        "visual": {
            "body": "big_round",
            "ears": "bear",
            "tail": None,
            "eye_patches": True,
            "patch_color": "#000000"
        }
    },
    {
        "id": "frog",
        "name": "Frog",
        "emoji": "🐸",
        "description": "Happy ribbit frog!",
        "color": "#7CB342",
        "color_dark": "#689F38",
        "rarity": "common",
        "price_stars": 0,
        "visual": {
            "body": "blob",
            "ears": None,
            "tail": None,
            "big_eyes": True,
            "mouth_wide": True
        }
    },
    {
        "id": "chick",
        "name": "Chick",
        "emoji": "🐥",
        "description": "Fluffy yellow chick!",
        "color": "#FFD700",
        "color_dark": "#FFC107",
        "rarity": "common",
        "price_stars": 0,
        "visual": {
            "body": "tiny_round",
            "ears": None,
            "tail": "feather",
            "beak": True,
            "wings": True
        }
    },
    {
        "id": "hedgehog",
        "name": "Hedgehog",
        "emoji": "🦔",
        "description": "Spiky but cute hedgehog!",
        "color": "#A0522D",
        "color_dark": "#8B4513",
        "rarity": "common",
        "price_stars": 0,
        "visual": {
            "body": "oval",
            "ears": "tiny",
            "tail": None,
            "spikes": True,
            "snout": True
        }
    },
]

# Premium pets - trending characters (paid with Telegram Stars)
PREMIUM_PETS = [
    {
        "id": "labubu",
        "name": "Labubu",
        "emoji": "🧸✨",
        "description": "Viral Popmart monster! TikTok famous!",
        "color": "#98FB98",
        "color_dark": "#7CCD7C",
        "rarity": "legendary",
        "price_stars": 150,
        "trend": "TikTok viral 2024",
    },
    {
        "id": "zhdun",
        "name": "Zhdun",
        "emoji": "🫠",
        "description": "The famous waiting blob! Patience master.",
        "color": "#C0C0C0",
        "color_dark": "#A9A9A9",
        "rarity": "epic",
        "price_stars": 100,
        "trend": "Meme legend",
    },
    {
        "id": "capybara",
        "name": "Capybara",
        "emoji": "🦫",
        "description": "OK I pull up! Chill vibes only.",
        "color": "#8B7355",
        "color_dark": "#6B5344",
        "rarity": "epic",
        "price_stars": 100,
        "trend": "Viral meme 2023-2024",
    },
    {
        "id": "axolotl",
        "name": "Axolotl",
        "emoji": "🦎💗",
        "description": "Pink water dragon! Minecraft famous!",
        "color": "#FFB6C1",
        "color_dark": "#FF69B4",
        "rarity": "epic",
        "price_stars": 80,
        "trend": "Minecraft & TikTok",
    },
    {
        "id": "shiba",
        "name": "Shiba Doge",
        "emoji": "🐕",
        "description": "Much wow! Very crypto! Such cute!",
        "color": "#FFDAB9",
        "color_dark": "#EECFA1",
        "rarity": "legendary",
        "price_stars": 120,
        "trend": "Crypto meme king",
    },
    {
        "id": "cat_loaf",
        "name": "Cat Loaf",
        "emoji": "🍞🐱",
        "description": "Bread-shaped kitty! Maximum loaf!",
        "color": "#DEB887",
        "color_dark": "#D2B48C",
        "rarity": "rare",
        "price_stars": 60,
        "trend": "Reddit famous",
    },
    {
        "id": "blobfish",
        "name": "Blobfish",
        "emoji": "🐟😢",
        "description": "World's saddest fish. Relatable mood.",
        "color": "#FFC0CB",
        "color_dark": "#FFB6C1",
        "rarity": "rare",
        "price_stars": 50,
        "trend": "Meme classic",
    },
    {
        "id": "pochacco",
        "name": "Pochacco",
        "emoji": "🐾⚪",
        "description": "Sanrio sporty pup! Athletic cutie!",
        "color": "#FFFFFF",
        "color_dark": "#F0F0F0",
        "rarity": "epic",
        "price_stars": 90,
        "trend": "Sanrio comeback",
    },
    {
        "id": "cinnamoroll",
        "name": "Cinnamoroll",
        "emoji": "☁️🐕",
        "description": "Flying cloud puppy! Sanrio #1!",
        "color": "#ADD8E6",
        "color_dark": "#87CEEB",
        "rarity": "legendary",
        "price_stars": 130,
        "trend": "Sanrio #1 character",
    },
    {
        "id": "kuromi",
        "name": "Kuromi",
        "emoji": "🐰🖤",
        "description": "Punk bunny with attitude! Hot Topic vibes!",
        "color": "#2F2F2F",
        "color_dark": "#1A1A1A",
        "rarity": "legendary",
        "price_stars": 140,
        "trend": "Gen Z favorite",
    },
]

ALL_PETS = FREE_PETS + PREMIUM_PETS

def get_pet_by_id(pet_id: str) -> dict:
    """Get pet data by ID"""
    for pet in ALL_PETS:
        if pet["id"] == pet_id:
            return pet
    return FREE_PETS[0]  # Default to kitty

def get_free_pets() -> list:
    """Get all free pets"""
    return FREE_PETS

def get_premium_pets() -> list:
    """Get all premium pets"""
    return PREMIUM_PETS

def is_pet_free(pet_id: str) -> bool:
    """Check if pet is free"""
    for pet in FREE_PETS:
        if pet["id"] == pet_id:
            return True
    return False

def get_pet_price(pet_id: str) -> int:
    """Get pet price in stars"""
    pet = get_pet_by_id(pet_id)
    return pet.get("price_stars", 0)
