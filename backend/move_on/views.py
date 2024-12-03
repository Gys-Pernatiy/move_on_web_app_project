import json
from datetime import datetime, timedelta
from math import radians, sin, cos, sqrt, atan2
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.pagination import PageNumberPagination

from .models import User, Walk, Task, WalkSession
from .serializers import UserSerializer, WalkSerializer, TaskSerializer
from django.utils.timezone import now
from scipy.signal import butter, filtfilt, find_peaks
import numpy as np
from haversine import haversine, Unit

from .utils import calculate_reward


def calculate_distance(lat1, lon1, lat2, lon2):
    return haversine((lat1, lon1), (lat2, lon2), unit=Unit.METERS)

# Фильтр скользящего среднего нашёл на аутсорсе
def moving_average(data, window_size=5):
    if len(data) < window_size:
        return []
    return [sum(data[i:i+window_size]) / window_size for i in range(len(data) - window_size + 1)]


def butter_lowpass_filter(data, cutoff=3.0, fs=50.0, order=4):
    nyquist = 0.5 * fs
    normal_cutoff = cutoff / nyquist
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return filtfilt(b, a, data)


def detect_steps(data, min_freq=0.5, max_freq=3.0, sampling_rate=50):
    threshold = np.std(data) * 1.5
    min_distance = int(sampling_rate / max_freq)
    peaks, _ = find_peaks(data, height=threshold, distance=min_distance)
    return len(peaks)




@csrf_exempt
def update_walk_session(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            walk_id = data.get("walk_id")
            acc_x = data.get("accX", 0)
            acc_y = data.get("accY", 0)
            acc_z = data.get("accZ", 0)
            latitude = data.get("latitude")
            longitude = data.get("longitude")
            speed = data.get("speed", 0)

            print(f"Запрос: {data}")

            if not walk_id:
                return JsonResponse({"error": "walk_id is required"}, status=400)

            walk_session = WalkSession.objects.get(id=walk_id)

            magnitude = sqrt(acc_x**2 + acc_y**2 + acc_z**2)
            print(f"Магнитуда: {magnitude}")

            if not hasattr(update_walk_session, "data_window"):
                update_walk_session.data_window = []

            update_walk_session.data_window.append(magnitude)
            if len(update_walk_session.data_window) > 100:
                update_walk_session.data_window.pop(0)

            smoothed_data = butter_lowpass_filter(update_walk_session.data_window)
            step_count = detect_steps(smoothed_data)
            print(f"Обнаруженные шаги: {step_count}")
            walk_session.steps = max(walk_session.steps, step_count)

            if latitude is not None and longitude is not None:
                if walk_session.last_latitude and walk_session.last_longitude:
                    distance = calculate_distance(
                        walk_session.last_latitude,
                        walk_session.last_longitude,
                        latitude,
                        longitude,
                    )
                    print(f"Расстояние: {distance}")
                    if 2 < distance < 50 and speed < 20:
                        walk_session.distance += distance

                walk_session.last_latitude = latitude
                walk_session.last_longitude = longitude

            elapsed_time = (now() - walk_session.start_time).total_seconds()
            walk_session.avg_speed = (
                walk_session.distance / elapsed_time if elapsed_time > 0 else 0
            )

            if speed < 0:
                speed = walk_session.distance / elapsed_time if elapsed_time > 0 else 0

            walk_session.save()

            response_data = {
                "steps": walk_session.steps,
                "distance": round(walk_session.distance, 2),
                "current_speed": round(speed, 2),
                "average_speed": round(walk_session.avg_speed, 2),
            }
            print(f"Ответ: {response_data}")
            return JsonResponse(response_data)

        except WalkSession.DoesNotExist:
            print("Ошибка: Сессия прогулки не найдена")
            return JsonResponse({"error": "Walk session not found"}, status=404)
        except Exception as e:
            print(f"Ошибка сервера: {e}")
            return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def log_js_errors(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            log_message = data.get('message', 'No message provided')
            print(f"JS LOG: {log_message}")
            with open("js_errors.log", "a", encoding="utf-8") as f:
                f.write(f"{log_message}\n")
            return JsonResponse({"status": "success", "message": "Log received"})
        except Exception as e:
            print(f"Error logging JS messages: {e}")
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)



# @csrf_exempt
# def track_data(request):
#     if request.method == 'POST':
#         try:
#             data = json.loads(request.body)
#             return JsonResponse({'status': 'success', 'received_data': data})
#         except json.JSONDecodeError:
#             return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
#     return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


@csrf_exempt
def start_walk(request):
    print("start_walk invoked")

    if request.method == "POST":
        try:
            data = json.loads(request.body)
            print("Data received:", data)
            telegram_id = data.get("telegram_id")
            print("Telegram ID:", telegram_id)

            user, created = User.objects.get_or_create(telegram_id=telegram_id, defaults={
                "username": data.get("username", ""),
                "first_name": data.get("first_name", ""),
                "last_name": data.get("last_name", ""),
            })
            if created:
                print(f"New user created: {user}")

            WalkSession.objects.filter(user=user).delete()

            walk_session = WalkSession.objects.create(user=user)
            print("Walk session created:", walk_session)

            return JsonResponse({"walk_id": walk_session.id, "message": "Прогулка начата"})
        except Exception as e:
            print("Error:", str(e))
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid method"}, status=405)


@csrf_exempt
def stop_walk(request):
    if request.method == "POST":
        walk_id = request.POST.get('walk_id')
        walk = get_object_or_404(Walk, id=walk_id)
        walk.end_time = now()
        walk.is_valid = False
        walk.save()
        return JsonResponse({"status": "paused", "walk_id": walk_id})
    return JsonResponse({"error": "Invalid request method"}, status=405)



@csrf_exempt
def end_walk(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            walk_id = data.get("walk_id")

            walk_session = WalkSession.objects.get(id=walk_id)
            Walk.objects.create(
                user=walk_session.user,
                start_time=walk_session.start_time,
                end_time=now(),
                steps=walk_session.steps,
                distance=walk_session.distance,
                avg_speed=walk_session.avg_speed,
            )
            walk_session.delete()

            return JsonResponse({"message": "Прогулка завершена"})
        except WalkSession.DoesNotExist:
            return JsonResponse({"error": "Walk session not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid method"}, status=405)


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


@csrf_exempt
def update_walk(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            walk_id = data.get('walk_id')
            steps = data.get('steps', 0)
            avg_speed = data.get('avg_speed', 0)
            user = get_object_or_404(User, telegram_id=data.get('telegram_id'))

            walk = get_object_or_404(Walk, id=walk_id, user=user)

            if 1 <= avg_speed <= 20:
                walk.steps += max(0, steps)
                walk.avg_speed = avg_speed
            else:
                walk.is_valid = False

            user.energy = max(0, user.energy - 1)

            walk.save()
            user.save()

            return JsonResponse({
                'remaining_energy': user.energy,
                'walk_steps': walk.steps,
                'walk_avg_speed': walk.avg_speed,
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Invalid request method"}, status=405)


@csrf_exempt
def finish_walk(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            walk_id = data.get('walk_id')
            user = get_object_or_404(User, telegram_id=data.get('telegram_id'))
            walk = get_object_or_404(Walk, id=walk_id, user=user)

            if walk.end_time:
                return JsonResponse({'error': 'Прогулка уже завершена'}, status=400)

            if walk.is_valid:
                reward = calculate_reward(walk.distance, walk.steps, walk.avg_speed, user)
                walk.reward = reward
                user.points += reward

            walk.end_time = now()
            walk.save()
            user.save()

            return JsonResponse({
                'walk_id': walk.id,
                'total_reward': walk.reward,
                'points': user.points,
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Invalid request method"}, status=405)


@api_view(['GET'])
def get_energy(request, telegram_id):
    """
    Возвращает текущую энергию пользователя по его Telegram ID.
    """
    try:
        user = get_object_or_404(User, telegram_id=telegram_id)
        serializer = UserSerializer(user)
        return JsonResponse({'energy': serializer.data['energy']}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


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


@csrf_exempt
def tasks_complete(request):
    """
    Отмечает задачу как выполненную и начисляет награду.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            task_id = data.get('task_id')
            user = get_object_or_404(User, telegram_id=data.get('telegram_id'))
            task = get_object_or_404(Task, id=task_id, user=user)
            if task.is_completed:
                return JsonResponse({'error': 'Task already completed'}, status=400)

            task.is_completed = True
            user.points += task.reward
            task.save()
            user.save()

            return JsonResponse({'task_id': task.id, 'new_points': user.points})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Invalid request method"}, status=405)



def get_statistics(request, telegram_id):
    user = get_object_or_404(User, telegram_id=telegram_id)
    statistics = user.statistics

    return JsonResponse({
        'total_steps': statistics.total_steps,
        'total_distance': statistics.total_distance,
        'total_rewards': statistics.total_rewards,
    })
