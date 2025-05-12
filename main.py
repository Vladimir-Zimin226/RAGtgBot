import os
import nest_asyncio
from telegram.ext import Application
import config
from telegram_interface import register_handlers


def main():
    token = os.getenv('TELEGRAM_TOKEN')
    # Инициализация конфигурации (подгружаем ключ и модель)
    api_key = config.get_api_key()
    model = config.get_model()
    # Лог запуска
    print(f"Using API key: {api_key[:4]}... and model: {model}")

    app = Application.builder().token(token).build()
    app.bot_data['rag_chain'] = None
    app.bot_data['vectorstore'] = None
    register_handlers(app)
    nest_asyncio.apply()
    app.run_polling()

if __name__ == '__main__':
    main()