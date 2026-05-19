# QUICKSTART

Эта инструкция запускает проект локально через Docker Compose, Nginx и ngrok.

## 1. Установите инструменты

Установите Docker Desktop и проверьте, что команда доступна:

```bash
docker --version
docker compose version
```

Установите ngrok и авторизуйте его по инструкции из личного кабинета ngrok.

## 2. Получите Telegram Bot Token

1. Откройте `@BotFather` в Telegram.
2. Выполните `/newbot`.
3. Задайте имя и username бота.
4. Скопируйте токен в переменную `BOT_TOKEN`.

Telegram ID администратора и владельца можно узнать через `@userinfobot`.

## 3. Создайте .env

```bash
cp .env.example .env
```

На Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Заполните обязательные переменные:

```env
BOT_TOKEN=replace_with_botfather_token
WEBHOOK_BASE_URL=https://example.ngrok-free.app
WEBHOOK_PATH=/telegram/webhook
WEBHOOK_SECRET=replace_with_random_webhook_secret
ADMIN_TELEGRAM_ID=123456789
OWNER_TELEGRAM_ID=123456789
OPERATOR_GROUP_ID=-1000000000000
POSTGRES_USER=botuser
POSTGRES_PASSWORD=replace_with_local_database_password
POSTGRES_DB=botdb
DATABASE_URL=postgresql+asyncpg://botuser:replace_with_local_database_password@db:5432/botdb
REDIS_URL=redis://redis:6379/0
```

Для демонстрационного режима оплаты оставьте `ROBOKASSA_LOGIN`, `ROBOKASSA_PASS1` и `ROBOKASSA_PASS2` пустыми.

## 4. Запустите проект

```bash
docker compose up --build
```

В составе запускаются PostgreSQL 16, Redis 7, контейнер приложения и Nginx на порту `80`. Приложение также доступно напрямую на `http://localhost:8010`.

## 5. Запустите ngrok

В отдельном терминале:

```bash
ngrok http 80
```

Скопируйте HTTPS-адрес вида `https://example.ngrok-free.app` в `WEBHOOK_BASE_URL` в `.env`.

Так как webhook устанавливается при старте приложения, после изменения `.env` перезапустите контейнер бота:

```bash
docker compose up -d --force-recreate bot
```

## 6. Проверьте health endpoint

```bash
curl http://localhost:8010/health
curl http://localhost/health
```

Ожидаемый ответ:

```json
{"status":"ok"}
```

## 7. Проверьте Telegram-бота

1. Откройте созданного бота в Telegram.
2. Отправьте `/start`.
3. Пользователь с `ADMIN_TELEGRAM_ID` получает права администратора.
4. Пользователь с `OWNER_TELEGRAM_ID` получает права владельца.
5. Владелец может пройти мастер настройки бизнес-параметров.

## 8. Запустите тесты

```bash
pip install -r requirements-dev.txt
python -m pytest tests/unit/ -q
python -m pytest tests/integration/ --collect-only -q
python -m pytest tests/integration/ -q
```

Интеграционные тесты требуют тестовую PostgreSQL БД. Если `TEST_DATABASE_URL` не задан или база недоступна, тесты будут пропущены через pytest.

## Типовые ошибки

`BOT_TOKEN is not set` - проверьте, что `.env` создан и токен скопирован без пробелов.

`WEBHOOK_BASE_URL looks like a placeholder` - замените примерный URL на HTTPS-адрес ngrok или домена.

Бот не отвечает в Telegram - проверьте, что ngrok запущен, `WEBHOOK_BASE_URL` обновлён, а контейнер `bot` перезапущен после изменения `.env`.

Порт `80` занят - остановите другой веб-сервер или измените порт Nginx в `docker-compose.yml` и используйте соответствующий порт в ngrok.

Ошибка подключения к БД - проверьте, что `POSTGRES_PASSWORD` совпадает с паролем внутри `DATABASE_URL`.

Интеграционные тесты пропущены - задайте `TEST_DATABASE_URL` и убедитесь, что тестовая база PostgreSQL доступна.
