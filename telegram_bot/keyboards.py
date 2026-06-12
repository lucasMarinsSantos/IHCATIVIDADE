from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    btn_search = InlineKeyboardButton('[+] Buscar Hardware', callback_data='action_search')
    btn_stats = InlineKeyboardButton('[i] Estatísticas', callback_data='action_stats')
    btn_update = InlineKeyboardButton('[~] Atualizar Ofertas', callback_data='action_update')
    markup.add(btn_search, btn_stats)
    markup.add(btn_update)
    return markup

def pagination_keyboard(current_page: int, total_pages: int, query_id: str):
    markup = InlineKeyboardMarkup(row_width=3)
    buttons = []
    if current_page > 1:
        buttons.append(InlineKeyboardButton('[<] Anterior', callback_data=f'page_{query_id}_{current_page - 1}'))
    else:
        buttons.append(InlineKeyboardButton(' ', callback_data='ignore'))
    buttons.append(InlineKeyboardButton(f'{current_page}/{total_pages}', callback_data='ignore'))
    if current_page < total_pages:
        buttons.append(InlineKeyboardButton('Próxima [>]', callback_data=f'page_{query_id}_{current_page + 1}'))
    else:
        buttons.append(InlineKeyboardButton(' ', callback_data='ignore'))
    markup.row(*buttons)
    btn_menu = InlineKeyboardButton('[=] Menu Principal', callback_data='action_menu')
    markup.row(btn_menu)
    return markup

def cancel_keyboard():
    markup = InlineKeyboardMarkup()
    btn_cancel = InlineKeyboardButton('[X] Cancelar', callback_data='action_cancel')
    markup.add(btn_cancel)
    return markup