# Используем официальный образ Node.js с поддержкой npm
FROM node:18 AS builder

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем package.json и package-lock.json и устанавливаем зависимости
COPY package.json . 
RUN npm install

# Копируем весь проект и собираем приложение
COPY . .

RUN npm run build

FROM nginx:latest
# Копируем собранные файлы фронтенда в Nginx
COPY --from=builder /app/dist /usr/share/nginx/html
