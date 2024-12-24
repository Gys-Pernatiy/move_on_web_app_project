import json
import logging
from datetime import datetime, timedelta
from math import radians, sin, cos, sqrt, atan2

from django.db.models import Window, F, Count, Sum
from django.db.models.functions import Rank
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet
from .models import User, Walk, Task, WalkSession, Referral, Statistics
from .serializers import UserSerializer, WalkSerializer, TaskSerializer, CompleteTaskSerializer
from django.utils.timezone import now
from scipy.signal import butter, filtfilt, find_peaks
import numpy as np
from haversine import haversine, Unit
from .utils import *

logger = logging.getLogger(__name__)


class WalkViewSet(ViewSet):
    @swagger_auto_schema(
        operation_description="Запуск прогулки.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['telegram_id'],
            properties={
                'telegram_id': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description='Telegram ID пользователя'
                ),
            },
        ),
        responses={
            200: openapi.Response(
                description="Прогулка начата",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'walk_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'start_time': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                    },
                ),
            ),
            400: openapi.Response(description="Ошибка, энергия недостаточна"),
            404: openapi.Response(description="Пользователь не найден"),
        },
    )
    def create(self, request):
        """
        Запуск прогулки.
        """
        data = request.data
        telegram_id = data.get('telegram_id')
        user = get_object_or_404(User, telegram_id=telegram_id)

        user.update_energy()
        if user.energy < user.max_energy:
            return Response({"error": "Энергия должна быть полной для начала прогулки"}, status=400)

        WalkSession.objects.filter(user=user).delete()
        walk_session = WalkSession.objects.create(user=user)

        return Response({
            "walk_id": walk_session.id,
            "message": "Прогулка начата",
            "start_time": walk_session.start_time.isoformat()
        })

    @swagger_auto_schema(
        operation_description="Обновление данных прогулки.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['walk_id', 'accX', 'accY', 'accZ', 'latitude', 'longitude'],
            properties={
                'walk_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID прогулки'),
                'accX': openapi.Schema(type=openapi.TYPE_NUMBER, description='Ускорение по оси X'),
                'accY': openapi.Schema(type=openapi.TYPE_NUMBER, description='Ускорение по оси Y'),
                'accZ': openapi.Schema(type=openapi.TYPE_NUMBER, description='Ускорение по оси Z'),
                'latitude': openapi.Schema(type=openapi.TYPE_NUMBER, description='Широта'),
                'longitude': openapi.Schema(type=openapi.TYPE_NUMBER, description='Долгота'),
                'speed': openapi.Schema(type=openapi.TYPE_NUMBER, description='Скорость'),
            },
        ),
        responses={
            200: openapi.Response(
                description="Данные прогулки обновлены",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'steps': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'distance': openapi.Schema(type=openapi.TYPE_NUMBER),
                        'current_speed': openapi.Schema(type=openapi.TYPE_NUMBER),
                        'average_speed': openapi.Schema(type=openapi.TYPE_NUMBER),
                    },
                ),
            ),
            400: openapi.Response(description="Недостаточно данных"),
            404: openapi.Response(description="Прогулка не найдена"),
        },
    )
    def update(self, request, pk=None):
        """
        Обновление данных прогулки.
        """
        data = request.data
        walk_id = data.get("walk_id")
        acc_x = data.get("accX")
        acc_y = data.get("accY")
        acc_z = data.get("accZ")
        latitude = data.get("latitude")
        longitude = data.get("longitude")
        speed_from_gps = data.get("speed", 0)
        logger.info(f"Received accX: {acc_x}, accY: {acc_y}, accZ: {acc_z}")
        logger.info(f"Received latitude: {latitude}, longitude: {longitude}, speed: {speed_from_gps}")
        if latitude == 0 and longitude == 0:
            logger.info("Default coordinates received. GPS may not be available.")

        if not walk_id:
            logger.info("walk_id is required")
            return Response({"error": "walk_id is required"}, status=400)

        if any(param is None for param in [acc_x, acc_y, acc_z, latitude, longitude]):
            logger.info("Incomplete data provided")
            return Response({"error": "Incomplete data provided"}, status=400)

        try:
            walk_session = WalkSession.objects.get(id=walk_id)
            user = walk_session.user

            user.update_energy()
            if user.energy <= 0:
                walk_session.is_interrupted = True
                walk_session.save()
                return self.finish(request, pk=walk_session.id)

            if acc_x is not None and acc_y is not None and acc_z is not None:
                acceleration_data = [{"x": acc_x, "y": acc_y, "z": acc_z}]
                steps = calculate_steps(acceleration_data)
                walk_session.steps += steps

            if latitude is not None and longitude is not None:
                if walk_session.last_latitude and walk_session.last_longitude:
                    prev_coords = (walk_session.last_latitude, walk_session.last_longitude)
                    current_coords = (latitude, longitude)

                    distance = calculate_speed_from_gps(prev_coords, current_coords, 1)
                    if 2 < distance < 50:
                        walk_session.distance += distance

                walk_session.last_latitude = latitude
                walk_session.last_longitude = longitude

            delta_time = (
                datetime.now() - walk_session.last_step_time).total_seconds() if walk_session.last_step_time else 1
            current_speed = speed_from_gps or calculate_speed(acceleration_data, delta_time)
            walk_session.last_step_time = datetime.now()

            elapsed_time = (datetime.now() - walk_session.start_time).total_seconds()
            walk_session.avg_speed = walk_session.distance / elapsed_time if elapsed_time > 0 else 0

            walk_session.save()

            return Response({
                "steps": walk_session.steps,
                "distance": round(walk_session.distance, 2),
                "current_speed": round(current_speed, 2),
                "average_speed": round(walk_session.avg_speed, 2)
            })

        except WalkSession.DoesNotExist:
            return Response({"error": "Walk session not found"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

    @swagger_auto_schema(
        operation_description="Завершение прогулки.",
        responses={
            200: openapi.Response(
                description="Прогулка завершена",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'reward': openapi.Schema(type=openapi.TYPE_NUMBER),
                    },
                ),
            ),
            404: openapi.Response(description="Прогулка не найдена"),
        },
    )
    def finish(self, request, pk=None):
        """
        Завершение прогулки.
        """
        try:
            walk_session = WalkSession.objects.get(id=pk)
            reward = calculate_reward(
                distance_km=walk_session.distance / 1000,
                steps=walk_session.steps,
                avg_speed_kmh=walk_session.avg_speed * 3.6,
                daily_streak=walk_session.user.daily_streak,
                endurance_level=walk_session.user.endurance_level,
                efficiency_level=walk_session.user.efficiency_level,
                luck_level=walk_session.user.luck_level,
            )

            Walk.objects.create(
                user=walk_session.user,
                start_time=walk_session.start_time,
                end_time=now(),
                steps=walk_session.steps,
                distance=walk_session.distance,
                avg_speed=walk_session.avg_speed,
                reward=reward,
            )

            walk_session.delete()

            return Response({
                "message": "Прогулка завершена",
                "reward": reward
            })

        except WalkSession.DoesNotExist:
            return Response({"error": "Walk session not found"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=500)


class LogView(APIView):
    """
    Получает логи с фронтенда и выводит их в консоль.
    """
    def post(self, request, *args, **kwargs):
        level = request.data.get("level", "info")
        message = request.data.get("message", "No message provided")
        user_id = request.data.get("user_id", "Unknown User")

        print(f"[{level.upper()}] User: {user_id} - {message}")
        return Response({"status": "log received"}, status=status.HTTP_200_OK)


def update_data(request):
    walk = get_object_or_404(Walk, id=request.POST['walk_id'])
    walk.steps += int(request.POST.get('steps', 0))
    walk.distance += float(request.POST.get('distance', 0))
    walk.avg_speed = walk.distance / ((now() - walk.start_time).total_seconds() / 3600)
    walk.save()
    return JsonResponse({
        "steps": walk.steps,
        "distance": walk.distance,
        "average_speed": walk.avg_speed,
        "current_speed": float(request.POST.get('speed', 0))
    })


# @csrf_exempt
# def update_walk(request):
#     if request.method == 'POST':
#         try:
#             data = json.loads(request.body)
#             walk_id = data.get('walk_id')
#             steps = data.get('steps', 0)
#             avg_speed = data.get('avg_speed', 0)
#             user = get_object_or_404(User, telegram_id=data.get('telegram_id'))
#
#             walk = get_object_or_404(Walk, id=walk_id, user=user)
#
#             if 1 <= avg_speed <= 20:
#                 walk.steps += max(0, steps)
#                 walk.avg_speed = avg_speed
#             else:
#                 walk.is_valid = False
#
#             user.energy = max(0, user.energy - 1)
#
#             walk.save()
#             user.save()
#
#             return JsonResponse({
#                 'remaining_energy': user.energy,
#                 'walk_steps': walk.steps,
#                 'walk_avg_speed': walk.avg_speed,
#             })
#         except Exception as e:
#             return JsonResponse({"error": str(e)}, status=500)
#     return JsonResponse({"error": "Invalid request method"}, status=405)


@swagger_auto_schema(
    methods=['get'],
    operation_description="Возвращает текущую энергию пользователя.",
    responses={
        200: openapi.Response(
            description="Уровень энергии пользователя",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'energy': openapi.Schema(type=openapi.TYPE_INTEGER, description='Текущая энергия пользователя'),
                },
            ),
        ),
        404: "Пользователь не найден",
        500: "Ошибка сервера",
    }
)
@api_view(['GET'])
def get_energy(request, telegram_id):
    """
    Возвращает текущую энергию пользователя по его Telegram ID.
    """
    try:
        user = User.objects.get(telegram_id=telegram_id)
        return JsonResponse({'energy': user.energy}, status=200)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@swagger_auto_schema(
    methods=['get'],
    operation_description="Возвращает историю прогулок пользователя, отсортированную по дате. Поддерживает пагинацию для большого количества прогулок.",
    manual_parameters=[
        openapi.Parameter(
            'telegram_id',
            openapi.IN_PATH,
            description="Telegram ID пользователя, для которого запрашивается история прогулок",
            type=openapi.TYPE_INTEGER
        ),
        openapi.Parameter(
            'page',
            openapi.IN_QUERY,
            description="Номер страницы для пагинации",
            type=openapi.TYPE_INTEGER
        ),
    ],
    responses={
        200: openapi.Response(
            description="История прогулок пользователя",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'count': openapi.Schema(type=openapi.TYPE_INTEGER, description='Общее количество прогулок'),
                    'next': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_URI, description='URL следующей страницы'),
                    'previous': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_URI, description='URL предыдущей страницы'),
                    'results': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID прогулки'),
                                'user': openapi.Schema(type=openapi.TYPE_STRING, description='Имя пользователя'),
                                'start_time': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, description='Время начала прогулки'),
                                'end_time': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, description='Время завершения прогулки'),
                                'steps': openapi.Schema(type=openapi.TYPE_INTEGER, description='Количество шагов'),
                                'distance': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT, description='Пройденное расстояние'),
                                'avg_speed': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT, description='Средняя скорость'),
                                'reward': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT, description='Полученная награда'),
                                'is_lucky_walk': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Флаг, указывающий, была ли прогулка удачной'),
                                'is_valid': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Флаг, указывающий, была ли прогулка валидной'),
                                'created_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, description='Дата создания записи'),
                            }
                        )
                    )
                }
            )
        ),
        404: "Пользователь не найден",
        500: "Ошибка сервера",
    }
)
@api_view(['GET'])
def walk_history(request, telegram_id):
    """
    Возвращает историю прогулок пользователя, отсортированную по дате.
    Поддерживает пагинацию для большого количества прогулок.
    """
    try:
        user = get_object_or_404(User, telegram_id=telegram_id)
        paginator = PageNumberPagination()
        paginator.page_size = 10
        walks = Walk.objects.filter(user=user).order_by('-start_time').select_related('user')
        paginated_walks = paginator.paginate_queryset(walks, request)

        serializer = WalkSerializer(paginated_walks, many=True)
        return paginator.get_paginated_response(serializer.data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['GET'])
def get_tasks(request, telegram_id):
    """
    Возвращает список заданий пользователя по его Telegram ID.
    """
    try:
        user = get_object_or_404(User, telegram_id=telegram_id)
        tasks = Task.objects.filter(user=user).select_related('user')
        serializer = TaskSerializer(tasks, many=True)
        return JsonResponse({'tasks': serializer.data}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@swagger_auto_schema(
    methods=['post'],
    operation_description="Отмечает задачу как выполненную и начисляет награду.",
    request_body=CompleteTaskSerializer,
    responses={
        200: openapi.Response(
            description="Задача успешно выполнена",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'task_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID завершённой задачи'),
                    'new_points': openapi.Schema(type=openapi.TYPE_INTEGER, description='Обновлённые очки пользователя'),
                },
            ),
        ),
        400: "Ошибка: Неверные данные",
        500: "Ошибка: Системная ошибка",
    }
)
@api_view(['POST'])
def tasks_complete(request):
    """
    Отмечает задачу как выполненную и начисляет награду.
    """
    try:
        task_id = request.data.get('task_id')
        telegram_id = request.data.get('telegram_id')

        logger.info(f"Received task_id: {task_id}, telegram_id: {telegram_id}")

        if not task_id or not telegram_id:
            return Response({"error": "task_id and telegram_id are required"}, status=status.HTTP_400_BAD_REQUEST)

        user = get_object_or_404(User, telegram_id=telegram_id)
        task = get_object_or_404(Task, id=task_id, user=user)

        if task.is_completed:
            return Response({'error': 'Task already completed'}, status=status.HTTP_400_BAD_REQUEST)

        logger.info(f"Task reward: {task.reward}")
        task.is_completed = True
        task.save()

        user.points += task.reward
        user.save()

        logger.info(f"Task completed: {task.is_completed}, User points: {user.points}")

        return Response({'task_id': task.id, 'new_points': user.points}, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def get_statistics(request, telegram_id):
    try:
        user = User.objects.get(telegram_id=telegram_id)
    except User.DoesNotExist:
        return Response({"error": "Пользователь не найден"}, status=status.HTTP_404_NOT_FOUND)
    statistics = user.statistics

    return JsonResponse({
        'total_steps': statistics.total_steps,
        'total_distance': statistics.total_distance,
        'total_rewards': statistics.total_rewards,
    })


@swagger_auto_schema(
    methods=['get'],
    operation_description="Возвращает историю стрика пользователя за последние 15 дней.",
    responses={
        200: openapi.Response(
            description="История стрика",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'days': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'date': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE, description="Дата."),
                                'isCurrent': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Является ли день текущим."),
                                'coinsEarned': openapi.Schema(type=openapi.TYPE_INTEGER, description="Количество заработанных монет."),
                                'bonusReceived': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Получен ли бонус."),
                            },
                        ),
                    ),
                    'currentStreak': openapi.Schema(type=openapi.TYPE_INTEGER, description="Текущий стрик."),
                    'maxDailyStreak': openapi.Schema(type=openapi.TYPE_INTEGER, description="Максимальный достигнутый стрик."),
                },
            ),
        ),
        404: openapi.Response(description="Пользователь не найден."),
        500: openapi.Response(description="Ошибка сервера."),
    }
)
@api_view(['GET'])
def streak_history(request, telegram_id):
    """
    Возвращает историю стрика за последние 15 дней с информацией:
    - Является ли день текущим.
    - Количество коинов, полученных за день.
    - Был ли получен бонус.
    - Текущий стрик.
    - Статус бонусов за каждые 5 дней.
    """
    user = get_object_or_404(User, telegram_id=telegram_id)
    daily_bonus = user.daily_bonus

    today = now().date()
    days = []
    current_streak = daily_bonus.streak
    streak_rewards = daily_bonus.streak_rewards

    for i in range(-5, 10):
        date = today + timedelta(days=i)
        is_current = date == today
        coins_earned = daily_bonus.claimed_days.get(str(date), {}).get("coinsEarned", 0)
        bonus_received = str(date) in daily_bonus.claimed_days

        days.append({
            'date': date,
            'isCurrent': is_current,
            'coinsEarned': coins_earned,
            'bonusReceived': bonus_received,
        })

    milestone_rewards = {
        milestone: streak_rewards.get(str(milestone), False)
        for milestone in [5, 10, 15]
    }

    return Response({
        'days': days,
        'currentStreak': current_streak,
        'maxDailyStreak': daily_bonus.max_streak,
        'milestoneRewards': milestone_rewards,
    })


@swagger_auto_schema(
    methods=['post'],
    operation_description="Начисляет ежедневный бонус пользователю.",
    responses={
        200: openapi.Response(
            description="Бонус успешно начислен.",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description="Подтверждение успешного начисления."),
                    'bonus': openapi.Schema(type=openapi.TYPE_INTEGER, description="Размер начисленного бонуса."),
                    'totalPoints': openapi.Schema(type=openapi.TYPE_INTEGER, description="Общее количество очков пользователя."),
                },
            ),
        ),
        400: openapi.Response(description="Бонус уже был начислен сегодня."),
        500: openapi.Response(description="Ошибка сервера."),
    }
)
@api_view(['POST'])
def claim_daily_bonus(request, telegram_id):
    """
    Пользователь получает ежедневный бонус за текущий день.
    """
    user = get_object_or_404(User, telegram_id=telegram_id)
    daily_bonus = user.daily_bonus

    today = now().date()
    if str(today) in daily_bonus.claimed_days:
        return Response({'error': 'Бонус уже получен за сегодня'}, status=status.HTTP_400_BAD_REQUEST)

    bonus = 10
    user.points += bonus
    daily_bonus.claimed_days[str(today)] = bonus
    daily_bonus.update_streak()

    user.save()
    daily_bonus.save()

    return Response({'message': 'Бонус успешно получен', 'bonus': bonus, 'totalPoints': user.points})


@api_view(['GET'])
def get_current_energy(request, telegram_id):
    """
    Возвращает текущую энергию пользователя, обновленную на основе времени.
    """
    user = get_object_or_404(User, telegram_id=telegram_id)

    user.update_energy()

    return Response({
        'currentEnergy': user.energy,
        'maxEnergy': 100,
        'lastUpdated': user.last_energy_update
    })


@api_view(['GET'])
def get_streak_status(request, telegram_id):
    user = get_object_or_404(User, telegram_id=telegram_id)
    daily_bonus = user.daily_bonus

    return Response({
        'current_streak': daily_bonus.streak,
        'max_streak': daily_bonus.max_streak,
        'claimed_days': daily_bonus.claimed_days,
        'streak_rewards': daily_bonus.streak_rewards,
    })


@swagger_auto_schema(
    methods=['get'],
    operation_description="Проверяет наличие незавершённых прогулок.",
    responses={
        200: openapi.Response(
            description="Данные о незавершённой прогулке.",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'steps': openapi.Schema(type=openapi.TYPE_INTEGER, description="Количество шагов."),
                    'distance': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT, description="Пройденное расстояние."),
                    'coins_earned': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT, description="Количество заработанных монет."),
                    'is_lucky_walk': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Была ли прогулка удачной."),
                    'is_unfinished': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Есть ли незавершённая прогулка."),
                },
            ),
        ),
        404: openapi.Response(description="Незавершённой прогулки не найдено."),
        500: openapi.Response(description="Ошибка сервера."),
    }
)
@api_view(['GET'])
def check_unfinished(request):
    telegram_id = request.query_params.get('telegram_id')
    if not telegram_id:
        return Response({"error": "telegram_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    user = get_object_or_404(User, telegram_id=telegram_id)

    walk = Walk.objects.filter(user=user, is_interrupted=True).first()

    if not walk:
        return Response({"is_unfinished": False})

    reward = calculate_reward(walk.distance, walk.steps, walk.avg_speed, user)

    walk.delete()

    return Response({
        "steps": walk.steps,
        "distance": walk.distance,
        "coins_earned": reward,
        "is_lucky_walk": walk.is_lucky_walk,
    })


@csrf_exempt
def lucky_throw(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            walk_id = data.get('walk_id')
            telegram_id = data.get('telegram_id')

            user = get_object_or_404(User, telegram_id=telegram_id)
            walk = get_object_or_404(Walk, id=walk_id, user=user)

            multiplier = 2.0 if np.random.random() < 0.5 else 1.0
            coins_earned = walk.reward * multiplier
            user.points += coins_earned - walk.reward
            user.save()

            return JsonResponse({
                "bonus_multiplier": multiplier,
                "coins_earned": coins_earned,
                "total_coins": user.points
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


@swagger_auto_schema(
    methods=['get'],
    operation_description="Возвращает текущие данные шагомера пользователя.",
    responses={
        200: openapi.Response(
            description="Данные шагомера.",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'coins': openapi.Schema(type=openapi.TYPE_INTEGER, description="Количество коинов пользователя."),
                    'max_energy': openapi.Schema(type=openapi.TYPE_INTEGER, description="Максимальная энергия пользователя."),
                    'current_energy': openapi.Schema(type=openapi.TYPE_INTEGER, description="Текущая энергия пользователя."),
                    'is_walk_running': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Идёт ли прогулка."),
                    'walk_duration': openapi.Schema(type=openapi.TYPE_INTEGER, description="Длительность текущей прогулки в секундах."),
                    'has_unclaimed_bonus': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Есть ли не полученные бонусы."),
                },
            ),
        ),
        404: openapi.Response(description="Пользователь не найден."),
        500: openapi.Response(description="Ошибка сервера."),
    }
)
@api_view(['GET'])
def stepometer(request):
    telegram_id = request.query_params.get('telegram_id')
    if not telegram_id:
        return Response({"error": "telegram_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    user = get_object_or_404(User, telegram_id=telegram_id)
    user.update_energy()

    walk_session = WalkSession.objects.filter(user=user).first()
    is_walk_running = walk_session is not None
    walk_duration = None

    if is_walk_running:
        walk_duration = (now() - walk_session.start_time).total_seconds()

    daily_bonus = user.daily_bonus
    has_unclaimed_bonus = daily_bonus and str(now().date()) not in daily_bonus.claimed_days

    return Response({
        "coins": user.points,
        "max_energy": 100,
        "current_energy": user.energy,
        "is_walk_running": is_walk_running,
        "walk_duration": int(walk_duration) if walk_duration else None,
        "has_unclaimed_bonus": has_unclaimed_bonus
    })


def main_page(request):
    """
    Обработка главной страницы с проверкой refid и данных пользователя.
    """
    user_data = request.GET.get('user_data')
    if not user_data:
        return JsonResponse({"error": "User data is required"}, status=400)

    try:
        user_data = json.loads(user_data)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid user data format"}, status=400)

    telegram_id = user_data.get('id')
    if not telegram_id:
        return JsonResponse({"error": "Telegram ID is required"}, status=400)

    user, created = User.objects.get_or_create(
        telegram_id=telegram_id,
        defaults={
            "username": user_data.get('username'),
            "first_name": user_data.get('first_name'),
            "last_name": user_data.get('last_name'),
        }
    )

    refid = request.GET.get('refid')
    if created and refid:
        referrer = User.objects.filter(referral_uuid=refid).first()
        if referrer and referrer != user:
            Referral.objects.create(user=user, invited_by=referrer)
            referrer.referral.total_invited += 1
            referrer.save()
        elif referrer == user:
            return JsonResponse({"error": "You cannot refer yourself"}, status=400)
        else:
            return JsonResponse({"error": "Invalid referral link"}, status=400)

    return JsonResponse({
        "message": "User processed successfully",
        "is_new_user": created,
        "referral_set": bool(refid and created)
    })


@swagger_auto_schema(
    methods=['get'],
    operation_description="Возвращает список всех активных заданий с возможностью фильтрации по типу задачи.",
    manual_parameters=[
        openapi.Parameter(
            'task_type',
            openapi.IN_QUERY,
            description="Тип задачи для фильтрации. Опционально.",
            type=openapi.TYPE_STRING
        )
    ],
    responses={
        200: openapi.Response(
            description="Список активных заданий.",
            schema=openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID задачи."),
                        'name': openapi.Schema(type=openapi.TYPE_STRING, description="Название задачи."),
                        'description': openapi.Schema(type=openapi.TYPE_STRING, description="Описание задачи."),
                        'reward': openapi.Schema(type=openapi.TYPE_INTEGER, description="Награда за выполнение задачи."),
                        'difficulty': openapi.Schema(type=openapi.TYPE_STRING, description="Сложность задачи."),
                        'task_type': openapi.Schema(type=openapi.TYPE_STRING, description="Тип задачи."),
                        'start_date': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE, description="Дата начала активности задачи."),
                        'end_date': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE, description="Дата окончания активности задачи."),
                        'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Статус активности задачи."),
                    }
                ),
            ),
        ),
        500: openapi.Response(description="Ошибка сервера."),
    }
)
@api_view(['GET'])
def get_tasks(request):
    """
    Возвращает список всех активных заданий.
    """
    task_type = request.query_params.get('task_type', None)
    active_tasks = Task.objects.filter(is_active=True)

    if task_type:
        active_tasks = active_tasks.filter(task_type=task_type)

    serializer = TaskSerializer(active_tasks, many=True)
    return Response(serializer.data)


@swagger_auto_schema(
    methods=['get'],
    operation_description="Возвращает глобальную статистику пользователей, включая топ-100 и позицию текущего пользователя.",
    manual_parameters=[
        openapi.Parameter(
            'telegram_id',
            openapi.IN_PATH,
            description="Telegram ID пользователя для определения позиции.",
            type=openapi.TYPE_INTEGER
        )
    ],
    responses={
        200: openapi.Response(
            description="Глобальная статистика пользователей.",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'top_users': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'rank': openapi.Schema(type=openapi.TYPE_INTEGER, description="Место пользователя в рейтинге."),
                                'username': openapi.Schema(type=openapi.TYPE_STRING, description="Имя пользователя."),
                                'points': openapi.Schema(type=openapi.TYPE_INTEGER, description="Количество очков пользователя."),
                            }
                        )
                    ),
                    'current_user_position': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'rank': openapi.Schema(type=openapi.TYPE_INTEGER, description="Место текущего пользователя."),
                            'username': openapi.Schema(type=openapi.TYPE_STRING, description="Имя текущего пользователя."),
                            'points': openapi.Schema(type=openapi.TYPE_INTEGER, description="Количество очков текущего пользователя."),
                        }
                    ),
                }
            )
        ),
        404: openapi.Response(description="Пользователь не найден."),
        500: openapi.Response(description="Ошибка сервера.")
    }
)
@api_view(['GET'])
def global_statistics(request, telegram_id):
    user = get_object_or_404(User, telegram_id=telegram_id)

    ranked_users = User.objects.annotate(
        rank=Window(
            expression=Rank(),
            order_by=F('points').desc()
        )
    )
    top_users = ranked_users.order_by('rank')[:100].values('rank', 'username', 'points')
    current_user = ranked_users.filter(telegram_id=telegram_id).values('rank', 'username', 'points').first()

    return Response({
        "top_users": list(top_users),
        "current_user_position": current_user
    })


@swagger_auto_schema(
    methods=['get'],
    operation_description="Возвращает топ рефералов текущего пользователя, отсортированных по очкам.",
    responses={
        200: openapi.Response(
            description="Топ рефералов текущего пользователя.",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'user_referrals': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        description="Топ рефералов текущего пользователя.",
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'username': openapi.Schema(type=openapi.TYPE_STRING, description="Имя пользователя."),
                                'points': openapi.Schema(type=openapi.TYPE_INTEGER, description="Очки реферала."),
                            }
                        )
                    ),
                    'referral_count': openapi.Schema(type=openapi.TYPE_INTEGER, description="Количество рефералов пользователя."),
                    'total_referral_points': openapi.Schema(type=openapi.TYPE_INTEGER, description="Сумма очков всех рефералов."),
                }
            )
        ),
        404: openapi.Response(description="Пользователь не найден."),
        500: openapi.Response(description="Ошибка сервера.")
    }
)
@api_view(['GET'])
def user_top_referrals(request, telegram_id):
    """
    Возвращает топ рефералов текущего пользователя, отсортированных по очкам.
    """
    user = get_object_or_404(User, telegram_id=telegram_id)
    user_referrals = user.referrals.all().order_by('-points')

    referral_stats = user_referrals.aggregate(
        referral_count=Count('id'),
        total_points=Sum('points')
    )

    return Response({
        "user_referrals": [
            {
                "username": referral.username,
                "points": referral.points
            }
            for referral in user_referrals
        ],
        "referral_count": referral_stats['referral_count'] or 0,
        "total_referral_points": referral_stats['total_points'] or 0,
    })
