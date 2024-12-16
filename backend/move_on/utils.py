import numpy as np
from scipy.signal import find_peaks
from geopy.distance import geodesic


def calculate_steps(acceleration_data, threshold=1.2):
    """
    Расчёт количества шагов на основе данных акселерометра.
    :param acceleration_data: Список значений ускорений [{'x': ..., 'y': ..., 'z': ...}, ...].
    :param threshold: Порог для определения шага.
    :return: Количество шагов.
    """
    magnitudes = [
        np.sqrt(data['x']**2 + data['y']**2 + data['z']**2) for data in acceleration_data
    ]
    peaks, _ = find_peaks(magnitudes, height=threshold)
    return len(peaks)


def calculate_distance(steps, step_length=0.75):
    """
    Расчёт дистанции на основе количества шагов.
    :param steps: Количество шагов.
    :param step_length: Длина одного шага (в метрах), по умолчанию 0.75 м.
    :return: Пройденная дистанция (в метрах).
    """
    return steps * step_length


def calculate_speed(acceleration_data, delta_time):
    """
    Расчёт скорости на основе данных акселерометра.
    :param acceleration_data: Список значений ускорений [{'x': ..., 'y': ..., 'z': ...}, ...].
    :param delta_time: Время между измерениями (в секундах).
    :return: Средняя скорость (в м/с).
    """
    magnitudes = [
        np.sqrt(data['x']**2 + data['y']**2 + data['z']**2) for data in acceleration_data
    ]
    # Убираем гравитацию (~9.81 м/с²) из ускорений
    adjusted_magnitudes = [max(0, mag - 9.81) for mag in magnitudes]
    # Интегрируем ускорение по времени, чтобы получить скорость
    speed = sum(adjusted_magnitudes) * delta_time / len(acceleration_data)
    return speed


def calculate_speed_from_gps(prev_coords, current_coords, delta_time):
    """
    Расчёт скорости на основе GPS-координат.
    :param prev_coords: Предыдущие координаты (широта, долгота) в формате (lat, lon).
    :param current_coords: Текущие координаты (широта, долгота) в формате (lat, lon).
    :param delta_time: Время между измерениями (в секундах).
    :return: Скорость (в м/с).
    """
    distance = geodesic(prev_coords, current_coords).meters  # Дистанция в метрах
    speed = distance / delta_time if delta_time > 0 else 0
    return speed


def calculate_reward(distance_km, steps, avg_speed_kmh, daily_streak, endurance_level, efficiency_level, luck_level):
    """
    Рассчитывает итоговую награду за прогулку.

    :param distance_km: Дистанция (в километрах).
    :param steps: Количество шагов.
    :param avg_speed_kmh: Средняя скорость (в км/ч).
    :param daily_streak: Дней в ежедневном стрике.
    :param endurance_level: Уровень выносливости (в процентах).
    :param efficiency_level: Уровень эффективности (в процентах).
    :param luck_level: Уровень удачи.
    :return: Итоговая награда.
    """

    # Длительность прогулки (в условных единицах, отобразим как пример)
    walk_duration = 10  # Это фиксировано в таблице как пример

    # Фактор средней скорости (1 при 5-12 км/ч, 0.7 при 1-4 км/ч, 0.7 при 13-20 км/ч)
    if 5 <= avg_speed_kmh <= 12:
        speed_factor = 1
    elif 1 <= avg_speed_kmh < 5 or 13 <= avg_speed_kmh <= 20:
        speed_factor = 0.7
    else:
        speed_factor = 0  # Слишком медленно или слишком быстро

    # Ежедневный множитель
    daily_multiplier = min(1 + daily_streak * 0.2, 2)  # До 5+ дней максимум х2

    # Бонус выносливости (60% за уровень)
    endurance_bonus = endurance_level * 0.6

    # Множитель эффективности (30% за уровень)
    efficiency_multiplier = 1 + efficiency_level * 0.3

    # Шанс удачи (5% базовый, +2% за уровень удачи)
    luck_chance = 5 + luck_level * 2

    # Итоговая награда
    base_reward = (distance_km * 10 + steps / 100) * speed_factor
    reward_with_multipliers = base_reward * daily_multiplier * efficiency_multiplier
    luck_bonus = reward_with_multipliers * (luck_chance / 100)

    total_reward = reward_with_multipliers + luck_bonus + endurance_bonus

    return round(total_reward, 2)
