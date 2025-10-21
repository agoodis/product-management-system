# Stage 1: Build
FROM node:18-alpine as build

WORKDIR /app

# Объявляем аргумент сборки, который будет передан из docker-compose.yml
ARG REACT_APP_API_URL

# Устанавливаем его как переменную окружения для этого этапа сборки
ENV REACT_APP_API_URL=$REACT_APP_API_URL

# Копируем package файлы
COPY package*.json ./

# Устанавливаем зависимости
# Используем npm install вместо npm ci, если нет package-lock.json
RUN npm install --silent

# Копируем весь код
COPY . .

# Собираем production build. Теперь react-scripts увидит REACT_APP_API_URL
RUN npm run build

# Stage 2: Production
FROM nginx:alpine

# Копируем собранное приложение из stage 1
COPY --from=build /app/build /usr/share/nginx/html

# Копируем конфигурацию nginx (опционально)
# COPY nginx.conf /etc/nginx/conf.d/default.conf

# Открываем порт
EXPOSE 80

# Запуск nginx
CMD ["nginx", "-g", "daemon off;"]