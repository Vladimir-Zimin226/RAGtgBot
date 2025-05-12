from langchain_gigachat.chat_models import GigaChat
from langchain_gigachat.embeddings.gigachat import GigaChatEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain_core.prompts import ChatPromptTemplate
from config import get_api_key, get_model


# Общий системный промпт
SYSTEM_PROMPT = (
    "Ты должен ответить на вопрос пользователя, строго используя контекст. "
    "Если нет данных - ответь 'данные не найдены'.\n{context}"
)
PROMPT = ChatPromptTemplate.from_messages([
    ('system', SYSTEM_PROMPT),
    ('human', '{input}'),
])


def prepare_data(docs):
    """Создает векторы и возвращает Chroma и retriever"""
    api_key = get_api_key()
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = splitter.split_documents(docs)
    embeddings = GigaChatEmbeddings(credentials=api_key, verify_ssl_certs=False)
    vect = Chroma.from_documents(documents=splits, embedding=embeddings)
    retriever = vect.as_retriever()
    return vect, retriever


def create_rag_chain(retriever):
    """Конструирует RetrievalQA цепочку"""
    api_key = get_api_key()
    model = get_model()
    giga = GigaChat(credentials=api_key, model=model, verify_ssl_certs=False)
    qa_chain = create_stuff_documents_chain(giga, PROMPT)
    return create_retrieval_chain(retriever, qa_chain)


def clear_storage(vect=None):
    """
    Очищает в памяти векторное хранилище или на диске при необходимости.
    """
    if vect:
        try:
            vect._collection.reset()  # сброс Chroma
        except Exception:
            pass