import re
import unicodedata
from typing import Optional
REGEX_PRECO = re.compile('[^\\d,.]')
REGEX_ESPACOS = re.compile('\\s+')
REGEX_TITULO = re.compile('[^\\w\\s\\-.,/+°()%]')
REGEX_DESCONTO_PCT = re.compile('(\\d+)\\s*%')

def normalizar_preco(texto: str) -> Optional[float]:
    if not texto:
        return None
    limpo = REGEX_PRECO.sub('', texto.strip())
    if not limpo:
        return None
    last_comma = limpo.rfind(',')
    last_dot = limpo.rfind('.')
    if last_comma > last_dot:
        limpo = limpo.replace('.', '').replace(',', '.')
    elif last_dot > last_comma:
        limpo = limpo.replace(',', '')
    try:
        val = float(limpo)
        return val if val > 0 else None
    except ValueError:
        return None

def normalizar_titulo(texto: str) -> str:
    if not texto:
        return ''
    texto = unicodedata.normalize('NFC', texto)
    texto = REGEX_ESPACOS.sub(' ', texto).strip()
    texto = REGEX_TITULO.sub('', texto)
    return texto

def normalizar_link(href: str, base_url: str) -> str:
    if not href:
        return ''
    href = href.split('?')[0].split('#')[0]
    if href.startswith('http'):
        return href
    if href.startswith('/'):
        return base_url.rstrip('/') + href
    return base_url.rstrip('/') + '/' + href

def extrair_desconto_pct(texto: str) -> Optional[int]:
    if not texto:
        return None
    match = REGEX_DESCONTO_PCT.search(texto)
    if not match:
        return None
    val = int(match.group(1))
    return val if 1 <= val <= 99 else None

def calcular_desconto(preco_atual: float, preco_antigo: float) -> Optional[int]:
    if not preco_antigo or preco_antigo <= 0 or preco_atual >= preco_antigo:
        return None
    return int(round((preco_antigo - preco_atual) / preco_antigo * 100))