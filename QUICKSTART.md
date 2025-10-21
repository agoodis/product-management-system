# 🚀 Быстрый старт

## Минимальные требования

- Python 3.10+
- Node.js 16+
- Docker Desktop (для PostgreSQL)

## Запуск за 3 шага

### 1. Клонирование и настройка

```bash
# Клонируйте проект
git clone <repository-url>
cd product-management-system

# Скопируйте переменные окружения
cp .env.example .env
```

### 2. Автоматический запуск (Mac/Linux)

```bash
chmod +x start.sh
./start.sh
```

### 3. Готово! 🎉

Откройте в браузере:
- **Frontend**: http://localhost:3000
- **API документация**: http://localhost:8000/docs

## Ручной запуск (Windows или детальный контроль)

### База данных

```bash
docker-compose up -d
```

### Backend

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm start
```

## Первые шаги после запуска

### 1. Импорт данных из 1С

1. Откройте http://localhost:3000/import
2. В разделе "Данные из 1С" нажмите "Выбрать файл"
3. Выберите Excel файл с данными из 1С
4. Нажмите "Загрузить"
5. Дождитесь завершения импорта

### 2. Импорт данных маркетплейсов

После импорта основных данных из 1С:

1. Загрузите "ШК Wildberries" - таблицу с артикулами WB
2. Загрузите "Цены Wildberries"
3. Загрузите "ШК Ozon" - таблицу с артикулами Ozon
4. Загрузите "Цены Ozon"

### 3. Просмотр товаров

1. Перейдите на главную страницу: http://localhost:3000
2. Увидите таблицу со всеми товарами
3. Используйте фильтры для поиска
4. Кликните дважды на ячейку для редактирования

### 4. Расчет показателей

Откройте API документацию: http://localhost:8000/docs

Найдите раздел "calculations" и выполните:
- `/api/calculations/recalculate-all` - пересчитать все показатели
- `/api/calculations/analytics/abc-summary` - посмотреть ABC анализ

### 5. Экспорт данных

1. Откройте http://localhost:3000/export
2. Выберите нужный формат экспорта
3. Файл автоматически загрузится

## Структура проекта

```
product-management-system/
├── backend/              # FastAPI приложение
│   ├── app/
│   │   ├── api/         # API endpoints
│   │   ├── models/      # Модели базы данных
│   │   ├── schemas/     # Pydantic схемы
│   │   ├── services/    # Бизнес-логика
│   │   └── main.py      # Точка входа
│   └── requirements.txt
├── frontend/            # React приложение
│   ├── src/
│   │   ├── components/  # React компоненты
│   │   ├── pages/       # Страницы
│   │   └── services/    # API клиент
│   └── package.json
├── docker-compose.yml   # PostgreSQL
├── .env                 # Переменные окружения
└── README.md
```

## Полезные команды

### База данных

```bash
# Запустить PostgreSQL
docker-compose up -d

# Остановить PostgreSQL
docker-compose down

# Просмотр логов PostgreSQL
docker-compose logs -f postgres

# Подключиться к PostgreSQL
docker exec -it product_db psql -U product_user -d product_db
```

### Backend

```bash
# Запустить сервер разработки
uvicorn app.main:app --reload

# Запустить на другом порту
uvicorn app.main:app --reload --port 8001

# Создать миграцию (если используете Alembic)
alembic revision --autogenerate -m "описание изменений"

# Применить миграции
alembic upgrade head
```

### Frontend

```bash
# Запустить dev сервер
npm start

# Собрать production версию
npm run build

# Запустить тесты
npm test
```

## Тестовые данные

Для быстрого тестирования можете использовать следующие примеры файлов:

### Минимальный файл 1С (Excel)

| ШК | Артикул | Номенклатура | Бренд | Склад на Есенина | Закупочная цена |
|----|---------|--------------|-------|------------------|-----------------|
| 1234567890123 | ART001 | Тестовый товар 1 | TestBrand | 10 | 1000 |
| 1234567890124 | ART002 | Тестовый товар 2 | TestBrand | 5 | 1500 |

### Минимальный файл WB ШК (Excel)

| ШК | Артикул | Арт ВБ |
|----|---------|--------|
| 1234567890123 | ART001 | 12345 |
| 1234567890124 | ART002 | 12346 |

### Минимальный файл WB Цены (Excel)

| ШК | Текущая цена | Текущая скидка |
|----|--------------|----------------|
| 1234567890123 | 1500 | 10 |
| 1234567890124 | 2000 | 15 |

## Troubleshooting

### Порт 8000 уже занят

```bash
# Найти процесс использующий порт
lsof -i :8000

# Убить процесс
kill -9 <PID>

# Или запустите на другом порту
uvicorn app.main:app --reload --port 8001
```

### Ошибка подключения к PostgreSQL

```bash
# Проверьте что контейнер запущен
docker ps

# Если не запущен
docker-compose up -d

# Проверьте логи
docker-compose logs postgres

# Проверьте настройки в .env
cat .env
```

### Frontend не может подключиться к Backend

1. Убедитесь что Backend запущен: http://localhost:8000/health
2. Проверьте настройки CORS в `backend/app/main.py`
3. Проверьте URL в `frontend/src/services/api.js`

### Ошибка импорта Excel файла

**"Файл должен быть в формате Excel"**
- Убедитесь что файл имеет расширение .xlsx или .xls

**"Товар с таким штрихкодом уже существует"**
- При повторном импорте 1С данные обновляются, а не создаются заново
- Это нормальное поведение

**"Ошибка обработки строки"**
- Проверьте что все обязательные колонки присутствуют
- Убедитесь что штрихкоды заполнены
- Проверьте формат данных (числа должны быть числами, не текстом)

### NPM install зависает

```bash
# Очистите кеш npm
npm cache clean --force

# Удалите node_modules и package-lock.json
rm -rf node_modules package-lock.json

# Установите заново
npm install
```

## API Endpoints для тестирования

### Создать товар вручную

```bash
curl -X POST "http://localhost:8000/api/products/" \
  -H "Content-Type: application/json" \
  -d '{
    "barcode": "1234567890123",
    "name": "Тестовый товар",
    "brand": "TestBrand",
    "stock_total": 10,
    "purchase_price": 1000
  }'
```

### Получить список товаров

```bash
curl "http://localhost:8000/api/products/?page=1&page_size=10"
```

### Пересчитать наценку

```bash
curl -X POST "http://localhost:8000/api/calculations/margins/recalculate"
```

### Получить товары с низким остатком

```bash
curl "http://localhost:8000/api/calculations/analytics/low-stock?threshold=5"
```

## Следующие шаги

После успешного запуска рекомендую:

1. **Изучить API документацию**: http://localhost:8000/docs
2. **Настроить регулярные расчеты** показателей (наценка, ABC)
3. **Добавить свои поля** в базу данных
4. **Настроить правила ценообразования** для разных категорий
5. **Интегрировать с API маркетплейсов** для автоматического обновления

## Дополнительная информация

- 📚 Полная документация: README.md
- 🐛 Проблемы и вопросы: создайте issue в репозитории
- 💡 Идеи по улучшению: pull requests приветствуются!

## Контакты и поддержка

Если возникли сложности:
1. Проверьте логи Backend и Frontend
2. Убедитесь что все сервисы запущены
3. Проверьте формат входных файлов
4. Посмотрите примеры API запросов в документации

Удачи! 🚀