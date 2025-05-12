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
from langchain_gigachat import GigaChat
from langchain_community.document_loaders import PyPDFLoader, CSVLoader
from langchain_chroma import Chroma
from langchain_gigachat.embeddings.gigachat import GigaChatEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

# Принудительный путь к .env (тут bot.env, как у тебя)
load_dotenv(dotenv_path=os.path.join(os.getcwd(), 'bot.env'))

# Проверка, что загрузилось
print("GIGA_API_KEY:", os.getenv('GIGA_API_KEY'))
print("TELEGRAM_TOKEN:", os.getenv('TELEGRAM_TOKEN'))

# Логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Ключи из окружения
TOKEN = os.getenv('TELEGRAM_TOKEN')
GIGA_API_KEY = os.getenv('GIGA_API_KEY')

# Настройка GigaChat
giga = GigaChat(
    credentials=GIGA_API_KEY,
    model="GigaChat-2",
    verify_ssl_certs=False,
    timeout=1200,
)

system_prompt = (
    "Ты должен ответить на вопрос пользователя, строго используя только предоставленный контекст из книги. "
    "Если информация явно отсутствует, ответь: 'данные не найдены'.\n"
    "Если данные в контексте присутствуют, дай максимально развернутый и полный ответ.\n"
    "{context}"
)

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{input}"),
])

def load_document(file_path: str):
    if file_path.endswith('.pdf'):
        loader = PyPDFLoader(file_path)
    elif file_path.endswith('.csv'):
        loader = CSVLoader(file_path)
    else:
        raise ValueError("Не поддерживаемый формат файла")
    return loader.load()

def prepare_data(docs):
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = splitter.split_documents(docs)
    embeddings = GigaChatEmbeddings(credentials=GIGA_API_KEY, verify_ssl_certs=False)
    vect = Chroma.from_documents(documents=splits, embedding=embeddings)
    return vect.as_retriever()

def create_rag_chain(retriever):
    qa = create_stuff_documents_chain(giga, prompt)
    return create_retrieval_chain(retriever, qa)

# Хендлеры
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Привет! Задайте свой вопрос, и я постараюсь найти ответ.')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # достаём rag_chain из bot_data
    rag_chain = context.application.bot_data.get('rag_chain')
    if rag_chain is None:
        await update.message.reply_text("Извините, RAG-цепочка ещё не инициализирована.")
        return
    question = update.message.text
    answer = rag_chain.invoke({"input": question})["answer"]
    await update.message.reply_text(f"Ответ: {answer}")

def main():
    # загружаем документ и строим RAG
    file_path = "content/Neural Network Agent Implementation in Russia_ Str.pdf"
    docs = load_document(file_path)
    retriever = prepare_data(docs)
    rag_chain = create_rag_chain(retriever)

    # создаём бота
    application = Application.builder().token(TOKEN).build()

    # сохраняем rag_chain
    application.bot_data['rag_chain'] = rag_chain

    # регистрируем команды
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # включаем nest_asyncio для локальных сред (необязательно)
    nest_asyncio.apply()

    # старт long-polling
    application.run_polling()

if __name__ == '__main__':
    main()