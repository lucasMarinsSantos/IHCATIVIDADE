import logging
import database
from telegram_bot import bot
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', handlers=[logging.StreamHandler()])
logger = logging.getLogger(__name__)

def main():
    logger.info('Inicializando o banco de dados...')
    database.inicializar()
    logger.info('Bot do Telegram iniciado. Pressione Ctrl+C para encerrar.')
    try:
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        logger.error(f'Erro fatal no bot: {e}', exc_info=True)
if __name__ == '__main__':
    main()