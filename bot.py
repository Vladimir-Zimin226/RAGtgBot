import logging
import os
import shutil
from dotenv import load_dotenv
import nest_asyncio

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from langchain_gigachat.chat_models import GigaChat
from langchain_chroma import Chroma
from langchain_gigachat.embeddings.gigachat import GigaChatEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

# локальный импорт загрузчика
from document_loader import load_document

# Загрузка .env
load_dotenv(dotenv_path=os.path.join(os.getcwd(), 'bot.env'))

# Логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Дефолтные настройки из окружения
ENV_API_KEY = os.getenv('GIGA_API_KEY')
API_KEY = None
MODEL = "GigaChat-2"  # по умолчанию Lite

system_prompt = (
    "Ты должен ответить на вопрос пользователя, строго используя только предоставленный контекст из книги. "
    "Если информация явно отсутствует, ответь: 'данные не найдены'."
    "Если данные в контексте присутствуют, дай максимально развернутый ответ."
    "{context}"
)
prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{input}"),
])

def prepare_data(docs, api_key: str):
    """Создает Chroma в памяти и возвращает объект vectorstore и retriever."""
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = splitter.split_documents(docs)
    embeddings = GigaChatEmbeddings(credentials=api_key, verify_ssl_certs=False)
    # Используем in-memory базу без persist_directory, чтобы избежать блокировок файлов
    vect = Chroma.from_documents(
        documents=splits,
        embedding=embeddings
    )
    retriever = vect.as_retriever()
    return vect, retriever


def create_rag_chain(retriever, api_key: str, model: str):
    giga = GigaChat(
        credentials=api_key,
        model=model,
        verify_ssl_certs=False,
        timeout=1200,
    )
    qa_chain = create_stuff_documents_chain(giga, prompt)
    return create_retrieval_chain(retriever, qa_chain)

# Команды
async def set_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global API_KEY
    if not context.args:
        await update.message.reply_text("Использование: /set_key <ваш_API_ключ>")
        return
    API_KEY = context.args[0]
    await update.message.reply_text("API-ключ установлен.")

async def set_model(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global MODEL
    if not context.args:
        await update.message.reply_text(
            "Использование: /set_model <Lite|Max|Pro>" +
            "Lite -> GigaChat-2 (по умолчанию) Max -> GigaChat-2-Max Pro -> GigaChat-2-Pro"
        )
        return
    choice = context.args[0].lower()
    if choice in ('lite', '2'):
        MODEL = 'GigaChat-2'
    elif choice in ('max', '2-max'):
        MODEL = 'GigaChat-2-Max'
    elif choice in ('pro', '2-pro'):
        MODEL = 'GigaChat-2-Pro'
    else:
        await update.message.reply_text("Неверная модель. Доступно Lite, Max, Pro.")
        return
    await update.message.reply_text(f"Модель установлена: {MODEL}")

async def clear_db(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Удаляет persist_directory Chroma и сбрасывает RAG-цепочку.
    """
    # Останавливаем использование старой цепочки
    context.application.bot_data['rag_chain'] = None
    context.application.bot_data['vectorstore'] = None
    # Удаляем папку с БД векторов
    db_dir = 'chroma_db'
    if os.path.exists(db_dir):
        shutil.rmtree(db_dir)
        await update.message.reply_text('Embedding база очищена.')
    else:
        await update.message.reply_text('Embedding база уже пуста.')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        'Привет! Перед загрузкой документа можно установить /set_key и /set_model.'
        'После загрузки можно очистить базу через /clear_db.'
    )

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    key = API_KEY or ENV_API_KEY
    if not key:
        await update.message.reply_text('Сначала установите API-ключ через /set_key или в .env.')
        return
    file = await update.message.document.get_file()
    downloads_dir = 'downloads'
    os.makedirs(downloads_dir, exist_ok=True)
    file_path = os.path.join(downloads_dir, update.message.document.file_name)
    await file.download_to_drive(file_path)
    try:
        docs = load_document(file_path)
        vect, retriever = prepare_data(docs, key)
        rag_chain = create_rag_chain(retriever, key, MODEL)
        context.application.bot_data['vectorstore'] = vect
        context.application.bot_data['rag_chain'] = rag_chain
        await update.message.reply_text('Документ загружен и проиндексирован, можно задавать вопросы.')
    except Exception as e:
        await update.message.reply_text(f'Ошибка при загрузке документа: {e}')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rag_chain = context.application.bot_data.get('rag_chain')
    if not rag_chain:
        await update.message.reply_text('Сначала загрузите документ.')
        return
    question = update.message.text
    answer = rag_chain.invoke({"input": question})["answer"]
    await update.message.reply_text(f"Ответ: {answer}")


def main():
    application = Application.builder().token(os.getenv('TELEGRAM_TOKEN')).build()
    application.bot_data['rag_chain'] = None
    application.bot_data['vectorstore'] = None
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("set_key", set_key))
    application.add_handler(CommandHandler("set_model", set_model))
    application.add_handler(CommandHandler("clear_db", clear_db))
    application.add_handler(MessageHandler(filters.Document.ALL & ~filters.COMMAND, handle_document))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    nest_asyncio.apply()
    application.run_polling()

if __name__ == '__main__':
    main()