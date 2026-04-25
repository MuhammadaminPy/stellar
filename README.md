# $DF Token TMA Bot

## Структура

```
df-token-bot/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI роуты
│   │   ├── bot/          # Aiogram бот
│   │   ├── core/         # Конфиг, авторизация
│   │   ├── db/           # БД сессия, Redis
│   │   ├── models/       # SQLAlchemy модели
│   │   ├── services/     # Бизнес-логика
│   │   └── tasks/        # Celery задачи
│   ├── alembic/          # Миграции
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── Info/     # Страница инфо
│       │   ├── Game/     # Игра "Мой уютный дом"
│       │   └── Profile/  # Профиль и кошелёк
│       ├── store/        # Zustand state
│       └── utils/        # API клиент
├── nginx/
└── docker-compose.yml
```

## Быстрый старт

### 1. Настрой окружение
```bash
cp .env.example .env
```
Заполни `.env`:
- `BOT_TOKEN` — токен бота от @BotFather
- `ADMIN_IDS` — твои Telegram ID через запятую
- `TON_API_KEY` — ключ от tonapi.io
- `TON_WALLET_ADDRESS` — кошелёк для приёма депозитов
- `WEBAPP_URL` — HTTPS URL где будет хоститься TMA
- `SECRET_KEY` — случайная строка 64+ символа

### 2. Запусти
```bash
docker-compose up -d --build
```

### 3. Примени миграции
```bash
docker-compose exec backend alembic upgrade head
```

### 4. Зарегистрируй WebApp в боте
В @BotFather:
- `/newapp` или `/editapp`
- Web App URL: `https://твой-домен.com`

## API

### Публичные
- `GET /api/info/stats` — статистика токена
- `GET /api/info/holders` — топ холдеры
- `GET /api/shop/items` — товары (с фильтрами)
- `GET /api/neighbors` — соседи

### Авторизованные (требуют `X-Init-Data` header)
- `GET /api/wallet/profile`
- `POST /api/wallet/deposit/check`
- `GET /api/wallet/deposit/info`
- `POST /api/wallet/withdraw`
- `POST /api/shop/buy`
- `GET /api/shop/inventory`
- `POST /api/shop/inventory/toggle`
- `POST /api/neighbors/like`

### Админские (требуют быть в ADMIN_IDS)
- `GET /api/admin/stats`
- `GET/POST /api/admin/user/*`
- `POST /api/admin/items`
- `GET /api/admin/withdrawals/pending`
- `POST /api/admin/withdrawals/approve`
- `GET /api/admin/top-referrals`
- `POST /api/admin/bonus`

## Команды бота
- `/start` — запуск, открытие TMA
- `/start <ref_id>` — запуск по реферальной ссылке
- `/admin` — панель администратора (только для admin_ids)

## Celery задачи (автоматические)
- Каждые 30 сек — кэш DEX статистики
- Каждые 60 сек — проверка ожидающих депозитов

## Добавление товаров
Через `/admin` в боте → "Добавить товар"
Или через API: `POST /api/admin/items`

## TON API
Получи ключ на https://tonapi.io
Бесплатный tier: 10 req/sec — достаточно для старта

## Деплой на VPS
1. Поставь Docker + Docker Compose
2. Склонируй проект
3. Заполни .env
4. `docker-compose up -d --build`
5. Настрой SSL через Let's Encrypt (certbot)
6. Укажи WEBAPP_URL с https://

Рекомендуемые VPS: Hetzner CX21 (2vCPU/4GB — $6/мес)
# stellar
