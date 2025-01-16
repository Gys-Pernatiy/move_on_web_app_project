#!/bin/bash


if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose не установлен. Установите Docker Compose и повторите попытку."
    exit 1
fi

echo "Перезапуск проекта..."

echo "Остановка и удаление контейнеров..."
docker-compose down || {
    echo "Ошибка при остановке контейнеров!"
    exit 1
}


echo "Очистка неиспользуемых данных Docker..."
docker system prune -af --volumes || {
    echo "Ошибка при очистке данных!"
    exit 1
}

echo "Перезапуск контейнеров..."
docker-compose up --build -d || {
    echo "Ошибка при запуске контейнеров!"
    exit 1
}

echo "Проверяем статус контейнеров..."
docker-compose ps

echo "Проект успешно перезапущен!"

