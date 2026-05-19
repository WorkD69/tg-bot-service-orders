# DEPLOYMENT

Документ описывает локальный и демонстрационный запуск проекта через Docker Compose. Для публичного сервера нужны те же контейнеры и публичный HTTPS-адрес вместо ngrok.

## Состав сервисов

| Сервис | Назначение |
| --- | --- |
| `db` | PostgreSQL 16, основная база данных проекта. |
| `redis` | Redis 7 для FSM-состояний aiogram. |
| `bot` | FastAPI-приложение, Telegram webhook, aiogram-диспетчер, бизнес-логика и APScheduler. |
| `nginx` | Reverse-proxy на порту `80`, проксирует запросы в контейнер `bot:8000`. |
| `ngrok` | Внешний инструмент для локального HTTPS-туннеля к Nginx. |

Файл `docker-compose.yml` запускает миграции командой `alembic upgrade head` перед стартом `uvicorn`.

## Переменные окружения

Основные переменные задаются в `.env`, созданном из `.env.example`.

| Переменная | Обязательна | Назначение |
| --- | --- | --- |
| `BOT_TOKEN` | Да | Токен Telegram-бота от BotFather. |
| `WEBHOOK_BASE_URL` | Да | Публичный HTTPS URL, например ngrok URL. |
| `WEBHOOK_PATH` | Да | Путь webhook, по умолчанию `/telegram/webhook`. |
| `WEBHOOK_SECRET` | Да | Секретный токен webhook. |
| `ADMIN_TELEGRAM_ID` | Да | Telegram ID администратора. |
| `OWNER_TELEGRAM_ID` | Желательно | Telegram ID владельца сервиса. |
| `OPERATOR_GROUP_ID` | Да | ID группы операторов. |
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | Да | Настройки контейнера PostgreSQL. |
| `DATABASE_URL` | Да | Async DSN для SQLAlchemy. |
| `REDIS_URL` | Да | URL Redis. |
| `ROBOKASSA_*` | Нет | Опциональная интеграция Robokassa. |

## Запуск

```bash
docker compose up --build -d
```

Проверка:

```bash
docker compose ps
curl http://localhost:8010/health
curl http://localhost/health
```

## Локальный webhook через ngrok

```bash
ngrok http 80
```

Скопируйте HTTPS URL в `WEBHOOK_BASE_URL` и перезапустите контейнер приложения:

```bash
docker compose up -d --force-recreate bot
```

Webhook устанавливается автоматически при старте приложения.

## Оплата

Основной демонстрационный режим - ручное подтверждение оплаты администратором.

1. Оператор отправляет клиенту реквизиты.
2. Клиент нажимает кнопку `Я оплатил`.
3. Администратор проверяет поступление денег и выполняет команду `/confirmpayment {order_id}`.
4. Заявка переходит в работу.

Robokassa подключается только как дополнительная интеграция. Если `ROBOKASSA_LOGIN` пустой, callback Robokassa отклоняется и система работает в ручном режиме.

## Обновление контейнеров

```bash
docker compose pull
docker compose build --no-cache bot
docker compose up -d
```

После изменения `.env` перезапустите приложение:

```bash
docker compose up -d --force-recreate bot
```

## Логи

```bash
docker compose logs -f bot
docker compose logs -f nginx
docker compose logs -f db
docker compose logs -f redis
```

## Миграции Alembic

Обычно миграции применяются автоматически при старте `bot`. Если нужно выполнить их вручную:

```bash
docker compose exec bot alembic upgrade head
docker compose exec bot alembic current
```

Если миграции не применяются, проверьте `DATABASE_URL`, состояние контейнера `db` и логи `bot`.

## Backup PostgreSQL

Linux/macOS:

```bash
docker compose exec db sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' > backup.sql
```

Windows PowerShell:

```powershell
docker compose exec db sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' | Out-File -Encoding utf8 backup.sql
```

## Restore PostgreSQL

Linux/macOS:

```bash
cat backup.sql | docker compose exec -T db sh -c 'psql -U "$POSTGRES_USER" "$POSTGRES_DB"'
```

Windows PowerShell:

```powershell
Get-Content backup.sql | docker compose exec -T db sh -c 'psql -U "$POSTGRES_USER" "$POSTGRES_DB"'
```

## Типовые проблемы

Контейнер `bot` перезапускается - смотрите `docker compose logs bot`; чаще всего причина в неверном `.env`.

Webhook не работает - проверьте HTTPS URL ngrok, `WEBHOOK_BASE_URL`, запущенный Nginx и перезапуск `bot` после изменения URL.

Порт `80` занят - освободите порт или измените публикацию порта у сервиса `nginx`.

Ошибка авторизации PostgreSQL - синхронизируйте `POSTGRES_PASSWORD` и пароль в `DATABASE_URL`.

Интеграционные тесты пропускаются - это штатно без `TEST_DATABASE_URL`; для запуска нужна отдельная тестовая база PostgreSQL.
