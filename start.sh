#!/bin/bash

# --- Функция для корректного завершения ---
cleanup() {
    echo ""
    echo "🛑 Остановка сервисов..."
    # Останавливаем локальный frontend-сервер, если он был запущен
    if [ -n "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID
    fi
    # Останавливаем и удаляем Docker-контейнеры
    docker-compose down
    echo "✅ Все сервисы остановлены."
    exit 0
}

# Устанавливаем "ловушку" на сигнал завершения (Ctrl+C)
trap cleanup INT TERM

echo "🚀 Запуск Product Management System в режиме разработки..."

# --- 1. Проверка и подготовка ---
if ! command -v docker-compose &> /dev/null
then
    echo "❌ Ошибка: docker-compose не найден. Пожалуйста, установите Docker."
    exit 1
fi

if [ ! -f ".env" ]; then
    echo "📝 .env файл не найден, копируем из .env.example..."
    cp .env.example .env
fi

# --- 2. Запуск Docker-сервисов (только БД и Backend) ---
echo "🐘🔧 Запуск PostgreSQL и Backend в Docker..."
docker-compose up -d postgres backend

# --- 3. Ожидание готовности Backend ---
echo -n "⏳ Ожидание готовности Backend API..."
# Пытаемся подключиться к health-endpoint в течение 60 секунд
for i in {1..60}; do
    # curl молча (-s) проверяет HTTP код (-w '%{http_code}') и ничего не выводит (-o /dev/null)
    STATUS=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/health)
    if [ "$STATUS" = "200" ]; then
        echo " ✓ Готово!"
        break
    fi
    echo -n "."
    sleep 1
done

if [ "$STATUS" != "200" ]; then
    echo " ❌ Не удалось дождаться запуска Backend. Посмотрите логи: docker-compose logs backend"
    cleanup
fi

# --- 4. Запуск Frontend локально ---
echo "🎨 Запуск Frontend локально..."
cd frontend

if [ ! -d "node_modules" ]; then
    echo "📥 Установка зависимостей Frontend (npm install)..."
    npm install
fi

echo "▶️  Запуск Frontend dev-сервера (npm start)..."
# Запускаем в фоне и сохраняем его ID процесса (PID)
npm start &
FRONTEND_PID=$!

cd ..

# --- 5. Вывод информации и ожидание ---
echo ""
echo "✅ Система запущена!"
echo ""
echo "📍 Backend API: http://localhost:8000"
echo "📍 API Документация: http://localhost:8000/docs"
echo "📍 Frontend (dev): http://localhost:3000"
echo ""
echo "Для остановки всех сервисов нажмите Ctrl+C в этом окне..."
echo ""

# 'wait' заставляет скрипт ждать завершения фоновых процессов
# В нашем случае, он будет ждать, пока не сработает 'trap' по Ctrl+C
wait $FRONTEND_PID