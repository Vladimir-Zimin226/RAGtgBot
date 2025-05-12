import os
import shutil
from telegram import ReplyKeyboardMarkup, KeyboardButton, Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
import config
from document_loader import load_document
from rag_logic import prepare_data, create_rag_chain, clear_storage

# Определяем кнопки главного меню
MENU_BUTTONS = [
    [KeyboardButton('Начать работу')],
    [KeyboardButton('Установить API-ключ')],
    [KeyboardButton('Выбрать модель')],
    [KeyboardButton('Очистить базу')]
]
REPLY_MARKUP = ReplyKeyboardMarkup(MENU_BUTTONS, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда /start — показывает главное меню без лишнего текста
    """
    await update.message.reply_text(
        'Выберите опцию:',
        reply_markup=REPLY_MARKUP
    )

async def cmd_set_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды /set_key для установки API-ключа
    """
    if context.args:
        key = context.args[0].strip()
        config.set_api_key(key)
        await update.message.reply_text(
            'API-ключ установлен.',
            reply_markup=REPLY_MARKUP
        )
    else:
        await update.message.reply_text(
            'Использование: /set_key <ваш_ключ>',
            reply_markup=REPLY_MARKUP
        )

async def cmd_set_model(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды /set_model для выбора модели
    """
    mapping = {'lite': 'GigaChat-2', 'max': 'GigaChat-2-Max', 'pro': 'GigaChat-2-Pro'}
    if context.args:
        choice = context.args[0].lower()
        if choice in mapping:
            config.set_model(mapping[choice])
            await update.message.reply_text(
                f"Модель установлена: {config.get_model()}",
                reply_markup=REPLY_MARKUP
            )
        else:
            await update.message.reply_text(
                'Использование: /set_model <Lite|Max|Pro>',
                reply_markup=REPLY_MARKUP
            )
    else:
        await update.message.reply_text(
            'Использование: /set_model <Lite|Max|Pro>',
            reply_markup=REPLY_MARKUP
        )

async def handle_menu_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает нажатия на кнопки меню: не отвечает на остальные тексты
    """
    text = update.message.text

    if text == 'Начать работу':
        await update.message.reply_text(
            'Отправьте документ (PDF, CSV, DOCX, XLSX) для индексации.',
            reply_markup=REPLY_MARKUP
        )
        return

    if text == 'Установить API-ключ':
        await update.message.reply_text(
            'Нажмите /set_key <ваш_ключ> для установки API-ключа.',
            reply_markup=REPLY_MARKUP
        )
        return

    if text == 'Выбрать модель':
        await update.message.reply_text(
            f"Текущая модель: {config.get_model()}\n"
            'Используйте /set_model <Lite|Max|Pro> для выбора модели.',
            reply_markup=REPLY_MARKUP
        )
        return

    if text == 'Очистить базу':
        vect = context.bot_data.get('vectorstore')
        clear_storage(vect)
        shutil.rmtree('downloads', ignore_errors=True)
        context.application.bot_data['rag_chain'] = None
        context.application.bot_data['vectorstore'] = None
        await update.message.reply_text(
            'База очищена.',
            reply_markup=REPLY_MARKUP
        )
        return

    # Если текст не соответствует кнопкам меню — передаём дальше
    return

async def handle_plain_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает вопросы к боту
    """
    text = update.message.text
    # Игнорируем меню тексты
    if text in {'Начать работу', 'Установить API-ключ', 'Выбрать модель', 'Очистить базу'}:
        return

    # Если это вопрос к RAG
    rag_chain = context.application.bot_data.get('rag_chain')
    if rag_chain:
        answer = rag_chain.invoke({'input': text})['answer']
        await update.message.reply_text(
            answer,
            reply_markup=REPLY_MARKUP
        )
    else:
        # Если RAG не инициализирован, просим загрузить документ
        await update.message.reply_text(
            'Сначала загрузите документ через меню.',
            reply_markup=REPLY_MARKUP
        )

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает загрузку документа пользователем
    """
    api_key = config.get_api_key()
    if not api_key:
        await update.message.reply_text(
            'Сначала установите API-ключ с помощью /set_key.',
            reply_markup=REPLY_MARKUP
        )
        return

    os.makedirs('downloads', exist_ok=True)
    doc_file = await update.message.document.get_file()
    path = os.path.join('downloads', update.message.document.file_name)
    await doc_file.download_to_drive(path)

    try:
        docs = load_document(path)
        vect, retriever = prepare_data(docs)
    except Exception as e:
        await update.message.reply_text(
            f'❗ Ошибка при подготовке эмбеддингов: {e}\n'
            'Проверьте правильность API-ключа.',
            reply_markup=REPLY_MARKUP
        )
        return

    chain = create_rag_chain(retriever)
    context.application.bot_data['vectorstore'] = vect
    context.application.bot_data['rag_chain'] = chain

    await update.message.reply_text(
        'Документ проиндексирован. Теперь вы можете задавать вопросы.',
        reply_markup=REPLY_MARKUP
    )

# Регистрация хендлеров

def register_handlers(application):
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('set_key', cmd_set_key))
    application.add_handler(CommandHandler('set_model', cmd_set_model))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu_selection), group=0)
    application.add_handler(MessageHandler(filters.Document.ALL & ~filters.COMMAND, handle_document), group=1)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_plain_text), group=2)