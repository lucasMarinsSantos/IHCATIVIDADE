import re
import unicodedata
from typing import Optional


def normalizar_preco(texto: str) -> Optional[float]:
    if not texto:
        return None
    limpo = re.sub(r"[^\d,.]", "", texto.strip())
    if not limpo:
        return None
    if limpo.count(",") == 1 and limpo.count(".") == 0:
        limpo = limpo.replace(",", ".")
    elif limpo.count(".") >= 1 and limpo.count(",") == 1:
        limpo = limpo.replace(".", "").replace(",", ".")
    try:
        val = float(limpo)
        return val if val > 0 else None
    except ValueError:
        return None


def normalizar_titulo(texto: str) -> str:
    if not texto:
        return ""
    texto = unicodedata.normalize("NFC", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    texto = re.sub(r"[^\w\s\-.,/+°()%]", "", texto)
    return texto


def normalizar_link(href: str, base_url: str) -> str:
    if not href:
        return ""
    href = href.split("?")[0].split("#")[0]
    if href.startswith("http"):
        return href
    if href.startswith("/"):
        return base_url.rstrip("/") + href
    return href


def extrair_desconto_pct(texto: str) -> Optional[int]:
    if not texto:
        return None
    match = re.search(r"(\d+)\s*%", texto)
    if not match:
        return None
    val = int(match.group(1))
    return val if 1 <= val <= 99 else None


def calcular_desconto(preco_atual: float, preco_antigo: float) -> Optional[int]:
    if not preco_antigo or preco_antigo <= 0 or preco_atual >= preco_antigo:
        return None
    return int(round(((preco_antigo - preco_atual) / preco_antigo) * 100))