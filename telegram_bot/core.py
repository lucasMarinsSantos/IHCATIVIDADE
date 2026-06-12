import sys
from telebot import TeleBot, custom_filters
from telebot.storage import StateMemoryStorage
from telebot.handler_backends import State, StatesGroup
from config import TELEGRAM_TOKEN, ALLOWED_USER_ID
if not TELEGRAM_TOKEN or TELEGRAM_TOKEN == 'insira_seu_token_aqui':
    print('ERRO: TELEGRAM_TOKEN não configurado no .env.')
    sys.exit(1)
state_storage = StateMemoryStorage()
bot = TeleBot(TELEGRAM_TOKEN, state_storage=state_storage, num_threads=20)

class BotStates(StatesGroup):
    aguardando_busca = State()

def checar_autorizacao(user_id) -> bool:
    if not ALLOWED_USER_ID:
        return True
    return str(user_id) == str(ALLOWED_USER_ID)
bot.add_custom_filter(custom_filters.StateFilter(bot))
bot.add_custom_filter(custom_filters.IsDigitFilter())