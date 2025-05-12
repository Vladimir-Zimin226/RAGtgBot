   # Telegram RAG Bot

Этот проект представляет собой телеграм-бота, использующего модель GigaChat для ответа на вопросы, основанные на контексте, извлеченном из документов.

## Описание

Бот отвечает на вопросы, основываясь на содержимом документов (PDF, DOCX, CSV), загруженных в векторную базу данных. Бот использует GigaChat для анализа контекста и поиска наиболее точных ответов.

## Установка

1. Клонируйте репозиторий:

```bash
git clone https://github.com/yourusername/my-telegram-bot-project.git
cd my-telegram-bot-project
```
2. Установите зависимости:

```bash
pip install -r requirements.txt
```

3. Добавьте в bot.env ваши данные:

```ini
TELEGRAM_TOKEN=ваш_токен_бота
GIGA_API_KEY=ваш_API_ключ_для_GigaChat
```

4. Запустите bot.py