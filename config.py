import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "data", "ofertas.db")

CACHE_HORAS     = 24
REQUEST_TIMEOUT = 15
REQUEST_DELAY   = 0.8
MAX_PAGINAS     = 10

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

TERABYTE_BASE = "https://www.terabyteshop.com.br"

TERABYTE_SECOES = [
    {"nome": "Promocoes",       "url": f"{TERABYTE_BASE}/promocoes",                "categoria": "Promocoes",      "paginacao": True},
    {"nome": "Placas de Video", "url": f"{TERABYTE_BASE}/hardware/placas-de-video", "categoria": "Placa de Video", "paginacao": True},
    {"nome": "Processadores",   "url": f"{TERABYTE_BASE}/hardware/processadores",   "categoria": "Processador",    "paginacao": True},
    {"nome": "Memorias RAM",    "url": f"{TERABYTE_BASE}/hardware/memorias-ram",    "categoria": "Memoria RAM",    "paginacao": True},
    {"nome": "SSDs",            "url": f"{TERABYTE_BASE}/hardware/ssds",            "categoria": "SSD",            "paginacao": True},
    {"nome": "Placas-Mae",      "url": f"{TERABYTE_BASE}/hardware/placas-mae",      "categoria": "Placa-Mae",      "paginacao": True},
]

MODELO_REPO    = "hugging-quants/Llama-3.2-1B-Instruct-Q4_K_M-GGUF"
MODELO_ARQUIVO = "llama-3.2-1b-instruct-q4_k_m.gguf"
MODELO_DIR     = os.path.join(BASE_DIR, "models")