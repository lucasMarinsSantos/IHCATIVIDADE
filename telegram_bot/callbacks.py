from telebot.types import CallbackQuery
from telegram_bot.core import bot, BotStates, checar_autorizacao
from telegram_bot.keyboards import pagination_keyboard, cancel_keyboard
from telegram_bot.utils import buscar_no_cache, formatar_mensagem_resultados
from telegram_bot.handlers import send_stats, send_update
import math
import logging
logger = logging.getLogger(__name__)

@bot.callback_query_handler(func=lambda call: call.data.startswith('action_'))
def handle_main_actions(call: CallbackQuery):
    if not checar_autorizacao(call.from_user.id):
        bot.answer_callback_query(call.id, 'Não autorizado.', show_alert=True)
        return
    action = call.data.split('action_')[1]
    try:
        bot.answer_callback_query(call.id)
    except Exception as e:
        logger.warning(f'Ignorando erro ao responder callback: {e}')
    if action == 'search':
        bot.set_state(call.from_user.id, BotStates.aguardando_busca, call.message.chat.id)
        bot.send_message(call.message.chat.id, '[?] *O que você está procurando?*\n_Ex: RTX 4060, ssd nvme 1tb até 400 reais_', parse_mode='Markdown', reply_markup=cancel_keyboard())
    elif action == 'stats':
        send_stats(call.message)
    elif action == 'update':
        send_update(call.message)
    elif action == 'menu':
        bot.delete_state(call.from_user.id, call.message.chat.id)
        from telegram_bot.handlers import send_welcome
        send_welcome(call.message)
    elif action == 'cancel':
        bot.delete_state(call.from_user.id, call.message.chat.id)
        bot.edit_message_text('[X] *Operação cancelada.*', chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data.startswith('page_'))
def handle_pagination(call: CallbackQuery):
    if not checar_autorizacao(call.from_user.id):
        return
    parts = call.data.split('_')
    if len(parts) != 3:
        bot.answer_callback_query(call.id, 'Erro ao paginar.')
        return
    query_id = parts[1]
    page_num = int(parts[2])
    if not buscar_no_cache(query_id):
        bot.answer_callback_query(call.id, 'Resultados expirados. Faça uma nova busca.', show_alert=True)
        return
    resultados = buscar_no_cache(query_id)
    items_per_page = 5
    total_pages = math.ceil(len(resultados) / items_per_page)
    if page_num < 1 or page_num > total_pages:
        bot.answer_callback_query(call.id)
        return
    start_idx = (page_num - 1) * items_per_page
    end_idx = start_idx + items_per_page
    page_results = resultados[start_idx:end_idx]
    is_fuzzy = any((r.get('_fuzzy') for r in resultados))
    res_text = formatar_mensagem_resultados(page_results, current_page=page_num, total_pages=total_pages, is_fuzzy=is_fuzzy)
    markup = pagination_keyboard(current_page=page_num, total_pages=total_pages, query_id=query_id)
    try:
        bot.edit_message_text(res_text, chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode='HTML', disable_web_page_preview=True, reply_markup=markup)
        bot.answer_callback_query(call.id)
    except Exception as e:
        if 'message is not modified' not in str(e).lower():
            logger.error(f'Erro na paginação do Telegram: {e}', exc_info=True)
        bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == 'ignore')
def handle_ignore(call: CallbackQuery):
    bot.answer_callback_query(call.id)