import os
from dotenv import load_dotenv


load_dotenv(dotenv_path=os.path.join(os.getcwd(), 'bot.env'))

DEFAULT_MODEL = 'GigaChat-2'

_TEMP_API_KEY = None
_TEMP_MODEL = None

def get_api_key() -> str:
    """Возвращает пользовательский ключ, если установлен, иначе из окружения"""
    return _TEMP_API_KEY or os.getenv('GIGA_API_KEY')

def set_api_key(key: str):
    """Устанавливает временный API-ключ"""
    global _TEMP_API_KEY
    _TEMP_API_KEY = key

def get_model() -> str:
    """Возвращает выбранную модель или дефолтную"""
    return _TEMP_MODEL or DEFAULT_MODEL

def set_model(model: str):
    """Устанавливает временную модель"""
    global _TEMP_MODEL
    _TEMP_MODEL = model