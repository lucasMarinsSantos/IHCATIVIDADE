import uuid
import time
search_cache: dict = {}
MAX_CACHE_ENTRIES = 50

def limpar_cache_antigo():
    if len(search_cache) > MAX_CACHE_ENTRIES:
        chaves_ordenadas = sorted(search_cache.keys(), key=lambda k: search_cache[k]['timestamp'])
        chaves_remover = chaves_ordenadas[:MAX_CACHE_ENTRIES // 2]
        for k in chaves_remover:
            del search_cache[k]

def salvar_no_cache(query_id: str, resultados: list):
    limpar_cache_antigo()
    search_cache[query_id] = {'timestamp': time.time(), 'data': resultados}

def buscar_no_cache(query_id: str):
    entrada = search_cache.get(query_id)
    return entrada['data'] if entrada else None

def formatar_preco(valor) -> str:
    if valor is None:
        return '--'
    return f'R$ {float(valor):,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')

def gerar_query_id() -> str:
    return uuid.uuid4().hex[:8]

def formatar_mensagem_resultados(resultados: list, current_page: int, total_pages: int, is_fuzzy: bool) -> str:
    res_text = ''
    if is_fuzzy and current_page == 1:
        res_text += '[!] <i>Não encontramos resultados exatos, mas veja estas opções:</i>\n\n'
    elif current_page == 1:
        res_text += f'[+] <b>{len(resultados)} resultado(s) encontrado(s):</b>\n\n'
    else:
        res_text += f'[+] <b>Página {current_page} de {total_pages}:</b>\n\n'
    for r in resultados:
        preco = formatar_preco(r.get('preco_atual'))
        desc_pct = r.get('desconto_pct')
        desc_str = f' (-{desc_pct}%)' if desc_pct else ''
        link = r.get('link')
        titulo = r.get('titulo')
        res_text += f'• <b>{titulo}</b>\n'
        res_text += f'$ {preco} {desc_str}\n'
        res_text += f"> <a href='{link}'>Link da Loja</a>\n\n"
    return res_text