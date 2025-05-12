import logging
import os
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

# Ключи из окружения
TOKEN = os.getenv('TELEGRAM_TOKEN')
GIGA_API_KEY = os.getenv('GIGA_API_KEY')

# Настройка модели GigaChat
system_prompt = (
    "Ты должен ответить на вопрос пользователя, строго используя только предоставленный контекст из книги. "
    "Если информация явно отсутствует, ответь: 'данные не найдены'.\n"
    "Если данные в контексте присутствуют, дай максимально развернутый ответ.\n"
    "{context}"
)
prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{input}"),
])

giga = GigaChat(
    credentials=GIGA_API_KEY,
    model="GigaChat-2",
    verify_ssl_certs=False,
    timeout=1200,
)


def prepare_data(docs):
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = splitter.split_documents(docs)
    embeddings = GigaChatEmbeddings(credentials=GIGA_API_KEY, verify_ssl_certs=False)
    vect = Chroma.from_documents(documents=splits, embedding=embeddings)
    return vect.as_retriever()


def create_rag_chain(retriever):
    qa_chain = create_stuff_documents_chain(giga, prompt)
    return create_retrieval_chain(retriever, qa_chain)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Привет! Загрузи документ (PDF, CSV, DOCX или XLSX) и задавай вопросы.')

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.document.get_file()
    downloads_dir = 'downloads'
    os.makedirs(downloads_dir, exist_ok=True)
    file_path = os.path.join(downloads_dir, update.message.document.file_name)
    await file.download_to_drive(file_path)
    try:
        docs = load_document(file_path)
        retriever = prepare_data(docs)
        context.application.bot_data['rag_chain'] = create_rag_chain(retriever)
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
    application = Application.builder().token(TOKEN).build()
    application.bot_data['rag_chain'] = None
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.ALL & ~filters.COMMAND, handle_document))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    nest_asyncio.apply()
    application.run_polling()

if __name__ == '__main__':
    main()