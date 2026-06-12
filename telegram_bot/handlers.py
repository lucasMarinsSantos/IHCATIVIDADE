from telebot.types import Message
from telegram_bot.core import bot, checar_autorizacao
from telegram_bot.keyboards import main_menu_keyboard, pagination_keyboard
from telegram_bot.utils import salvar_no_cache, gerar_query_id, formatar_mensagem_resultados, formatar_preco
from services.search_service import buscar, estatisticas
from services.ia_service import interpretar
from scraper.terabyte import executar as executar_scraping
import math
import logging
logger = logging.getLogger(__name__)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message: Message):
    if not checar_autorizacao(message.from_user.id):
        return
    bot.delete_state(message.from_user.id, message.chat.id)
    texto = '<b>[ BIGONE BOT ]</b>\n<i>Buscador de Hardware Terabyte</i>\n\nSeja muito bem-vindo! Eu sou o seu assistente pessoal de ofertas.\n\nO que você está procurando hoje?\nVocê pode digitar diretamente (ex: <code>RTX 4060 até 2000 reais</code>) ou usar os botões abaixo:'
    bot.send_message(message.chat.id, texto, reply_markup=main_menu_keyboard(), parse_mode='HTML')

@bot.message_handler(commands=['stats'])
def send_stats(message: Message):
    if not checar_autorizacao(message.from_user.id):
        return
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        s = estatisticas()
        texto = f"[i] *Estatísticas do Banco de Dados*\n\nTotal de produtos: {s['total']}\nDesconto médio: {s['desconto_medio']}%\nMenor preço: {formatar_preco(s['menor_preco'])}\nPreço médio: {formatar_preco(s['preco_medio'])}\nMaior preço: {formatar_preco(s['maior_preco'])}\n\n<b>Por Categoria:</b>\n"
        for cat, qtd in s['por_categoria'].items():
            texto += f'- {cat}: {qtd}\n'
        bot.send_message(message.chat.id, texto, parse_mode='HTML')
    except Exception as e:
        logger.error(f'Erro ao gerar estatísticas: {e}', exc_info=True)
        bot.send_message(message.chat.id, '[!] *Erro ao processar estatísticas.*', parse_mode='Markdown')

@bot.message_handler(commands=['atualizar'])
def send_update(message: Message):
    if not checar_autorizacao(message.from_user.id):
        return
    msg = bot.send_message(message.chat.id, '[~] *Iniciando coleta...* Isso pode levar alguns segundos.', parse_mode='Markdown')
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        total = executar_scraping(forcar=True)
        bot.edit_message_text(f'[+] *Coleta finalizada!* {total} produtos salvos/atualizados.', chat_id=msg.chat.id, message_id=msg.message_id, parse_mode='Markdown')
    except Exception as e:
        logger.error(f'Erro na coleta de dados: {e}', exc_info=True)
        bot.edit_message_text('[!] *Erro na coleta:* Tente novamente mais tarde.', chat_id=msg.chat.id, message_id=msg.message_id, parse_mode='Markdown')

@bot.message_handler(content_types=['text'])
def search_hardware(message: Message):
    if not checar_autorizacao(message.from_user.id):
        return
    bot.delete_state(message.from_user.id, message.chat.id)
    query_text = message.text
    msg = bot.send_message(message.chat.id, '[~] *Analisando e buscando...*', parse_mode='Markdown')
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        filtros = interpretar(query_text)
        resultados = buscar(query=filtros.get('query'), categoria=filtros.get('categoria'), preco_max=filtros.get('preco_max'), desconto_min=filtros.get('desconto_min'), ordem=filtros.get('ordem', 'desconto'), limite=50)
        if not resultados:
            bot.edit_message_text('Nenhum produto encontrado com esses filtros.', chat_id=msg.chat.id, message_id=msg.message_id)
            return
        query_id = gerar_query_id()
        salvar_no_cache(query_id, resultados)
        is_fuzzy = any((r.get('_fuzzy') for r in resultados))
        items_per_page = 5
        total_pages = math.ceil(len(resultados) / items_per_page)
        page_results = resultados[0:items_per_page]
        res_text = formatar_mensagem_resultados(page_results, current_page=1, total_pages=total_pages, is_fuzzy=is_fuzzy)
        markup = pagination_keyboard(current_page=1, total_pages=total_pages, query_id=query_id) if total_pages > 1 else None
        bot.edit_message_text(res_text, chat_id=msg.chat.id, message_id=msg.message_id, parse_mode='HTML', disable_web_page_preview=True, reply_markup=markup)
    except Exception as e:
        logger.error(f'Erro Telegram na busca: {e}', exc_info=True)
        bot.edit_message_text('Ocorreu um erro ao realizar a busca. Tente novamente mais tarde.', chat_id=msg.chat.id, message_id=msg.message_id)