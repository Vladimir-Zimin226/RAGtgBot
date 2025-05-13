   # Telegram RAG Bot

Телеграм-бот, использующий GigaChat для ответов на вопросы по загруженным документам (PDF, CSV, DOCX, XLSX), индексируя их в векторную базу с помощью Chroma.

## Функционал

- Загрузка документов форматов PDF, CSV, DOCX и Excel (XLSX, XLS)  
- Индексация текста в векторном хранилище Chroma  
- Использование моделей GigaChat:  
  - Lite (`GigaChat-2`) — по умолчанию  
  - Max (`GigaChat-2-Max`)  
  - Pro (`GigaChat-2-Pro`)  
- Автоматическая генерация ответов на вопросы по контексту документов  
- Управление API-ключом и выбор модели через команды  
- Очистка загруженных документов и индексов  
- Удобное меню в виде клавиатуры Telegram  

## Структура проекта

```txt
my-telegram-bot-project/
├── bot.env                 # Переменные окружения (токены)
├── config.py               # Настройки (ключ, модель)
├── document_loader.py      # Логика загрузки документов
├── rag_logic.py            # Подготовка векторов и RAG-цепочка
├── telegram_interface.py   # Обработчики Telegram (кнопки, команды)
├── main.py                 # Точка входа, регистрация хендлеров
├── downloads/              # Загруженные документы (auto)
└── requirements.txt        # Python-зависимости
```

## Установка

1. Клонируйте репозиторий:

```bash
git clone https://github.com/Vladimir-Zimin226/RAGtgBot.git
cd RAGtgBot
```
2. Создайте и активируйте виртуальное окружение:

```bash
python -m venv .venv
source .venv/bin/activate    # Linux/macOS
.\.venv\Scripts\activate     # Windows
```
3. Установите зависимости:

```bash
pip install -r requirements.txt
```

4. Добавьте в bot.env ваши данные:

```ini
TELEGRAM_TOKEN=ваш_токен_бота
GIGA_API_KEY=ваш_API_ключ_для_GigaChat
```
Примечание: API-ключ GigaChat можно будет добавить потом в самом боте.

## Использование

1. Запустите бота:

```bash
python main.py
```

2. Откройте чат с ботом в Telegram и введите `/start`.

3. Выберите одну из кнопок:

• **Начать работу** — загрузите документ.

• **Установить API-ключ** — используйте команду `/set_key <ключ>`.

• **Выбрать модель** — `/set_model <Lite|Max|Pro>`.

• **Очистить базу** — удаляет файлы и очищает индексы.

4. После индексации отправляйте вопросы — бот ответит на основе содержимого документа.

## Примеры команд

```txt
/set_key eyJhbGciOiJIUzI1...   # Установить base64-ключ GigaChat
/set_model Max                # Выбрать модель GigaChat-2-Max
```
