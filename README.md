# Система автоматизации закупок

REST API для автоматизации процессов закупок, разработанная на Django и Django REST Framework.

## Технологический стек

- **Backend**: Python 3.12, Django 6.0, Django REST Framework
- **База данных**: PostgreSQL 16
- **Очереди**: Redis 7
- **Асинхронные задачи**: Celery
- **Контейнеризация**: Docker, Docker Compose
- **Зависимости**: Управление через `uv`

## Функциональные возможности

- Управление магазинами и товарами
- Категоризация продукции
- Работа с заказами и корзиной
- Асинхронное обновление позиций товаров
- Подтверждение аккаунта по email
- Полноценная система аутентификации и авторизации

## Запуск проекта

### Предварительные требования

- Docker и Docker Compose
- Переменные окружения (создайте файл `.env` на основе `.env.example`)

### Запуск

```bash
# Создание .env файла
cp .env.example .env
# Настройка переменных в .env

# Запуск всех сервисов
docker-compose up --build
```

Приложение будет доступно по адресу `http://localhost:8000`.


## Структура проекта

```
procurement_automation/
├── accounts/          # Аутентификация и пользователи
├── backend/           # Основная бизнес-логика
├── procurement_automation/ # Настройки Django
├── docker-compose.yml # Оркестрация контейнеров
├── Dockerfile         # Сборка образа
├── pyproject.toml     # Зависимости
└── README.md          # Документация
```

## API Endpoints

### Пользователи
- `POST /api/v1/registry/` - Регистрация пользователя
- `POST /api/v1/confirm/` - Подтверждение email
- `POST /api/v1/login/` - Логин
### Закупки
- `POST /api/v1/shops/` - Регистрация магазина
- `PATCH /api/v1/shops/{pk}/positions/` - Асинхронное обновление позиций
- `GET /api/v1/products/` - Получение товаров
- `GET /api/v1/cart/` - Работа с корзиной заказов
- `POST /api/v1/contacts/` - Работа с контактами пользователя
- `GET /api/v1/orders/` - Получение заказов магазина

## Переменные окружения

Создайте файл `.env` на основе следующих переменных:

```env
POSTGRES_DB=procurement_db
POSTGRES_USER=procurement_user
POSTGRES_PASSWORD=your_secure_password
POSTGRES_PORT=5432

SECRET_KEY=your_django_secret_key
DEBUG=False

EMAIL_HOST_USER=noreply@example.com
EMAIL_HOST_PASSWORD=emailhostpassword
EMAIL_HOST=smtp.exmaple.com

DATABASE_URL=postgresql://procurement_user:your_secure_password@postgres:5432/procurement_db
REDIS_URL=redis://redis:6379/0
```