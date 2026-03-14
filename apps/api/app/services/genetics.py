"""
Genetics & Breeding System - генетика питомцев и скрещивание
"""
import random
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple

# === ГЕНЫ ===
GENE_POOLS = {
    "color": {
        "common": ["orange", "gray", "black", "white", "brown"],
        "uncommon": ["cream", "silver", "ginger", "chocolate"],
        "rare": ["golden", "platinum", "blue", "lavender"],
        "epic": ["rainbow", "cosmic", "crystal"],
        "legendary": ["void", "celestial", "aurora"],
        "mythic": ["prismatic", "ethereal"]
    },
    "pattern": {
        "common": ["solid", "tabby", "spots"],
        "uncommon": ["stripes", "patches", "tuxedo"],
        "rare": ["marble", "rosettes", "brindle"],
        "epic": ["galaxy", "flames", "frost"],
        "legendary": ["lightning", "nebula", "sakura"],
        "mythic": ["dimensional", "holographic"]
    },
    "eyes": {
        "common": ["green", "yellow", "amber", "brown"],
        "uncommon": ["blue", "gold", "copper"],
        "rare": ["heterochromia", "violet", "silver"],
        "epic": ["glowing", "starry", "fire"],
        "legendary": ["diamond", "void", "aurora"],
        "mythic": ["galaxy", "hypnotic"]
    },
    "trait": {
        "common": ["playful", "lazy", "curious", "calm"],
        "uncommon": ["fast", "strong", "smart", "charming"],
        "rare": ["lucky", "resilient", "wise", "fierce"],
        "epic": ["mythical", "ancient", "elemental"],
        "legendary": ["divine", "immortal", "cosmic"],
        "mythic": ["omniscient", "transcendent"]
    },
    "special": {
        "rare": ["tiny_wings", "glowing_aura", "sparkles"],
        "epic": ["wings", "horns", "halo"],
        "legendary": ["dragon_wings", "phoenix_tail", "unicorn_horn"],
        "mythic": ["reality_warp", "time_shift"]
    }
}

# Шансы редкостей при генерации
RARITY_WEIGHTS = {
    "common": 50,
    "uncommon": 25,
    "rare": 15,
    "epic": 7,
    "legendary": 2.5,
    "mythic": 0.5
}

# Шансы мутаций при breeding
MUTATION_CHANCES = {
    "common": 0.01,      # 1%
    "uncommon": 0.03,    # 3%
    "rare": 0.05,        # 5%
    "epic": 0.02,        # 2%
    "legendary": 0.005,  # 0.5%
    "mythic": 0.001      # 0.1%
}

# Мутации
MUTATIONS = {
    "common": ["крепкие кости", "густая шерсть", "острый слух"],
    "uncommon": ["быстрые лапы", "железный желудок", "ночное зрение"],
    "rare": ["золотой блеск", "серебряное сияние", "радужные глаза"],
    "epic": ["маленькие крылья", "светящийся нимб", "огненный хвост"],
    "legendary": ["драконьи крылья", "хвост феникса", "рог единорога"],
    "mythic": ["искривление реальности", "бессмертная душа"]
}

# Бонусы от редкости
RARITY_MULTIPLIERS = {
    "common": 1.0,
    "uncommon": 1.1,
    "rare": 1.25,
    "epic": 1.5,
    "legendary": 2.0,
    "mythic": 3.0
}

# Cooldown после breeding (в часах)
BREEDING_COOLDOWN = {
    "common": 12,
    "uncommon": 18,
    "rare": 24,
    "epic": 36,
    "legendary": 48,
    "mythic": 72
}

# Максимум breeding
MAX_BREEDING_COUNT = {
    "common": 5,
    "uncommon": 5,
    "rare": 4,
    "epic": 3,
    "legendary": 2,
    "mythic": 1
}


def roll_rarity() -> str:
    """Случайная редкость с весами"""
    total = sum(RARITY_WEIGHTS.values())
    roll = random.uniform(0, total)
    
    cumulative = 0
    for rarity, weight in RARITY_WEIGHTS.items():
        cumulative += weight
        if roll <= cumulative:
            return rarity
    return "common"


def generate_gene(gene_type: str, rarity: str = None) -> Tuple[str, str]:
    """
    Генерация одного гена.
    Возвращает (значение, редкость_гена)
    """
    if rarity is None:
        rarity = roll_rarity()
    
    pool = GENE_POOLS.get(gene_type, {})
    
    # Ищем значения для этой редкости или ниже
    for r in [rarity, "epic", "rare", "uncommon", "common"]:
        if r in pool and pool[r]:
            return (random.choice(pool[r]), r)
    
    return ("default", "common")


def generate_genes(pet_type: str = "cat", target_rarity: str = None) -> Dict:
    """
    Генерация полного набора генов для нового питомца
    """
    if target_rarity is None:
        target_rarity = roll_rarity()
    
    genes = {
        "pet_type": pet_type,
    }
    
    # Основные гены
    for gene_type in ["color", "pattern", "eyes", "trait"]:
        # Для более редких питомцев выше шанс редких генов
        if target_rarity in ["legendary", "mythic"]:
            gene_rarity = random.choice(["rare", "epic", "legendary"])
        elif target_rarity in ["epic", "rare"]:
            gene_rarity = random.choice(["uncommon", "rare", "epic"])
        else:
            gene_rarity = roll_rarity()
        
        value, actual_rarity = generate_gene(gene_type, gene_rarity)
        genes[gene_type] = value
        genes[f"{gene_type}_rarity"] = actual_rarity
    
    # Специальный ген (только для редких+)
    if target_rarity in ["rare", "epic", "legendary", "mythic"]:
        if random.random() < 0.3:  # 30% шанс
            special_value, special_rarity = generate_gene("special", target_rarity)
            if special_value != "default":
                genes["special"] = special_value
                genes["special_rarity"] = special_rarity
    
    return genes


def calculate_overall_rarity(genes: Dict) -> str:
    """Вычислить общую редкость на основе генов"""
    rarity_scores = {
        "common": 1,
        "uncommon": 2,
        "rare": 3,
        "epic": 4,
        "legendary": 5,
        "mythic": 6
    }
    
    gene_rarities = []
    for key, value in genes.items():
        if key.endswith("_rarity"):
            gene_rarities.append(rarity_scores.get(value, 1))
    
    if not gene_rarities:
        return "common"
    
    avg_score = sum(gene_rarities) / len(gene_rarities)
    
    # Бонус за специальный ген
    if "special" in genes:
        avg_score += 0.5
    
    # Определяем итоговую редкость
    if avg_score >= 5.5:
        return "mythic"
    elif avg_score >= 4.5:
        return "legendary"
    elif avg_score >= 3.5:
        return "epic"
    elif avg_score >= 2.5:
        return "rare"
    elif avg_score >= 1.5:
        return "uncommon"
    else:
        return "common"


def breed_pets(parent1_genes: Dict, parent2_genes: Dict, 
               parent1_rarity: str, parent2_rarity: str) -> Tuple[Dict, str, List[str]]:
    """
    Скрещивание двух питомцев.
    Возвращает (гены_потомка, редкость, список_мутаций)
    """
    child_genes = {}
    mutations = []
    
    # Наследуем гены от родителей
    for gene_type in ["color", "pattern", "eyes", "trait"]:
        # 50/50 шанс от каждого родителя
        if random.random() < 0.5:
            if gene_type in parent1_genes:
                child_genes[gene_type] = parent1_genes[gene_type]
                child_genes[f"{gene_type}_rarity"] = parent1_genes.get(f"{gene_type}_rarity", "common")
            else:
                child_genes[gene_type], child_genes[f"{gene_type}_rarity"] = generate_gene(gene_type)
        else:
            if gene_type in parent2_genes:
                child_genes[gene_type] = parent2_genes[gene_type]
                child_genes[f"{gene_type}_rarity"] = parent2_genes.get(f"{gene_type}_rarity", "common")
            else:
                child_genes[gene_type], child_genes[f"{gene_type}_rarity"] = generate_gene(gene_type)
    
    # Тип питомца (случайно от одного из родителей)
    child_genes["pet_type"] = random.choice([
        parent1_genes.get("pet_type", "cat"),
        parent2_genes.get("pet_type", "cat")
    ])
    
    # Специальный ген (наследуется с 25% шансом)
    if "special" in parent1_genes and random.random() < 0.25:
        child_genes["special"] = parent1_genes["special"]
        child_genes["special_rarity"] = parent1_genes.get("special_rarity", "rare")
    elif "special" in parent2_genes and random.random() < 0.25:
        child_genes["special"] = parent2_genes["special"]
        child_genes["special_rarity"] = parent2_genes.get("special_rarity", "rare")
    
    # Мутации!
    for mutation_rarity, chance in MUTATION_CHANCES.items():
        # Бонус к шансу от редкости родителей
        rarity_bonus = 1.0
        if parent1_rarity in ["legendary", "mythic"] or parent2_rarity in ["legendary", "mythic"]:
            rarity_bonus = 2.0
        elif parent1_rarity in ["epic", "rare"] or parent2_rarity in ["epic", "rare"]:
            rarity_bonus = 1.5
        
        if random.random() < chance * rarity_bonus:
            mutation_pool = MUTATIONS.get(mutation_rarity, [])
            if mutation_pool:
                mutation = random.choice(mutation_pool)
                if mutation not in mutations:
                    mutations.append(mutation)
                    # Мутация также добавляет бонус к редкости
                    if mutation_rarity in ["legendary", "mythic"]:
                        child_genes["has_legendary_mutation"] = True
    
    # Вычисляем редкость потомка
    child_rarity = calculate_overall_rarity(child_genes)
    
    # Бонус от мутаций
    if mutations:
        rarity_order = ["common", "uncommon", "rare", "epic", "legendary", "mythic"]
        current_idx = rarity_order.index(child_rarity)
        bonus = min(len(mutations), 2)  # Максимум +2 ранга
        new_idx = min(current_idx + bonus, len(rarity_order) - 1)
        child_rarity = rarity_order[new_idx]
    
    return child_genes, child_rarity, mutations


def can_breed(pet_rarity: str, breeding_count: int, cooldown_until: Optional[datetime]) -> Tuple[bool, str]:
    """
    Проверить можно ли питомцу размножаться
    Возвращает (можно, причина)
    """
    # Проверяем лимит breeding
    max_count = MAX_BREEDING_COUNT.get(pet_rarity, 5)
    if breeding_count >= max_count:
        return False, f"Достигнут лимит размножений ({max_count})"
    
    # Проверяем cooldown
    if cooldown_until and datetime.now(timezone.utc) < cooldown_until:
        remaining = cooldown_until - datetime.now(timezone.utc)
        hours = int(remaining.total_seconds() / 3600)
        minutes = int((remaining.total_seconds() % 3600) / 60)
        return False, f"Cooldown: {hours}ч {minutes}мин"
    
    return True, "OK"


def get_breeding_cooldown(rarity: str) -> timedelta:
    """Получить длительность cooldown после breeding"""
    hours = BREEDING_COOLDOWN.get(rarity, 24)
    return timedelta(hours=hours)


def get_stat_multiplier(rarity: str, mutations: List[str]) -> float:
    """Вычислить множитель статов от редкости и мутаций"""
    base = RARITY_MULTIPLIERS.get(rarity, 1.0)
    
    # Бонус от мутаций
    mutation_bonus = len(mutations) * 0.05  # +5% за каждую мутацию
    
    return base + mutation_bonus


def generate_nft_metadata(pet_id: int, pet_type: str, rarity: str, 
                          genes: Dict, mutations: List[str], 
                          generation: int, level: int) -> Dict:
    """
    Генерация метаданных для NFT в формате TON
    """
    # Атрибуты для OpenSea/Getgems формата
    attributes = [
        {"trait_type": "Type", "value": pet_type.capitalize()},
        {"trait_type": "Rarity", "value": rarity.capitalize()},
        {"trait_type": "Generation", "value": f"Gen {generation}"},
        {"trait_type": "Level", "value": level},
    ]
    
    # Добавляем гены
    for gene_type in ["color", "pattern", "eyes", "trait"]:
        if gene_type in genes:
            attributes.append({
                "trait_type": gene_type.capitalize(),
                "value": genes[gene_type].capitalize()
            })
    
    # Специальный ген
    if "special" in genes:
        attributes.append({
            "trait_type": "Special",
            "value": genes["special"].replace("_", " ").capitalize()
        })
    
    # Мутации
    for i, mutation in enumerate(mutations[:3]):  # Максимум 3 мутации
        attributes.append({
            "trait_type": f"Mutation {i+1}",
            "value": mutation.capitalize()
        })
    
    # Статы как числовые атрибуты
    attributes.append({
        "display_type": "boost_percentage",
        "trait_type": "Stat Boost",
        "value": int((get_stat_multiplier(rarity, mutations) - 1) * 100)
    })
    
    metadata = {
        "name": f"PIXEL PET #{pet_id}",
        "description": f"A {rarity} {pet_type} from the PIXEL PET universe. Generation {generation}.",
        "image": f"https://pixel-pet.app/api/pet/{pet_id}/image",
        "external_url": f"https://pixel-pet.app/pet/{pet_id}",
        "attributes": attributes,
        
        # TON specific
        "content_url": f"https://pixel-pet.app/api/pet/{pet_id}/image",
        "content_type": "image/png",
        
        # Дополнительные данные
        "properties": {
            "genes": genes,
            "mutations": mutations,
            "breeding_count": 0,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    }
    
    return metadata


# === Стоимость breeding в Stars ===
BREEDING_COST = {
    "common": 50,
    "uncommon": 100,
    "rare": 200,
    "epic": 400,
    "legendary": 800,
    "mythic": 1500
}

def get_breeding_cost(parent1_rarity: str, parent2_rarity: str) -> int:
    """Стоимость breeding на основе редкости родителей"""
    cost1 = BREEDING_COST.get(parent1_rarity, 100)
    cost2 = BREEDING_COST.get(parent2_rarity, 100)
    return (cost1 + cost2) // 2
