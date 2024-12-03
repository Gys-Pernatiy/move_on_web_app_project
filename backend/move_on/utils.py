import random


def calculate_reward(distance, steps, avg_speed, user):
    """
    Расчёт награды за прогулку.

    Аргументы:
    - distance: Пройденная дистанция (км).
    - steps: Количество шагов.
    - avg_speed: Средняя скорость (км/ч).
    - user: Экземпляр пользователя для учёта его навыков и бонусов.

    Возвращает:
    - Общую награду с учётом всех факторов.
    """
    # Основные множители
    distance_factor = distance * 10
    step_factor = steps / 100
    speed_factor = 1 if 5 <= avg_speed <= 12 else 0.7

    # Дополнительные бонусы
    efficiency_bonus = 1 + (user.efficiency_level * 0.3)  # 30% за уровень эффективности
    endurance_bonus = 1 + (user.endurance_level * 0.6)  # 60% за уровень выносливости
    streak_bonus = 1 + (user.daily_streak * 0.05)  # 5% за день стрика, максимум x2
    streak_bonus = min(streak_bonus, 2)  # Ограничение стрика

    # Базовая награда
    base_reward = (distance_factor + step_factor) * speed_factor

    # Учитываем все бонусы
    total_reward = base_reward * efficiency_bonus * endurance_bonus * streak_bonus

    # Удачная прогулка
    luck_chance = user.luck_level * 5  # 5% за уровень удачи
    if random.randint(1, 100) <= luck_chance:  # Если выпадет удача
        total_reward *= random.choice([1.5, 2])  # Умножаем на x1.5 или x2

    return round(total_reward, 2)
