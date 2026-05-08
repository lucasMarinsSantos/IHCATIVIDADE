import os
import re
import unicodedata
from typing import Optional

from config import MODELO_REPO, MODELO_ARQUIVO, MODELO_DIR

MODELO_PATH = os.path.join(MODELO_DIR, MODELO_ARQUIVO)

CATEGORIAS_VALIDAS = {
    "Placa de Video", "Processador", "Memoria RAM",
    "SSD", "Placa-Mae", "Promocoes",
}

MAPA_CATEGORIA = {
    "placa de video":       "Placa de Video",
    "placa video":          "Placa de Video",
    "placa mae":            "Placa-Mae",
    "placa-mae":            "Placa-Mae",
    "memoria ram":          "Memoria RAM",
    "intel core":           "Processador",
    "motherboard":          "Placa-Mae",
    "mainboard":            "Placa-Mae",
    "geforce":              "Placa de Video",
    "radeon":               "Placa de Video",
    "processador":          "Processador",
    "core i":               "Processador",
    "promocao":             "Promocoes",
    "promocoes":            "Promocoes",
    "oferta":               "Promocoes",
    "ofertas":              "Promocoes",
    "desconto":             "Promocoes",
    "ryzen":                "Processador",
    "athlon":               "Processador",
    "threadripper":         "Processador",
    "xeon":                 "Processador",
    "pentium":              "Processador",
    "celeron":              "Processador",
    "gpu":                  "Placa de Video",
    "rtx":                  "Placa de Video",
    "gtx":                  "Placa de Video",
    "rx 9":                 "Placa de Video",
    "rx 7":                 "Placa de Video",
    "rx 6":                 "Placa de Video",
    "arc a":                "Placa de Video",
    "intel arc":            "Placa de Video",
    "cpu":                  "Processador",
    "ddr5":                 "Memoria RAM",
    "ddr4":                 "Memoria RAM",
    "ddr3":                 "Memoria RAM",
    "dimm":                 "Memoria RAM",
    "sodimm":               "Memoria RAM",
    "so-dimm":              "Memoria RAM",
    "ram":                  "Memoria RAM",
    "nvme":                 "SSD",
    "m.2":                  "SSD",
    "pcie ssd":             "SSD",
    "ssd":                  "SSD",
    "z890":                 "Placa-Mae",
    "z790":                 "Placa-Mae",
    "z690":                 "Placa-Mae",
    "b850":                 "Placa-Mae",
    "b840":                 "Placa-Mae",
    "b760":                 "Placa-Mae",
    "b650":                 "Placa-Mae",
    "b550":                 "Placa-Mae",
    "x870":                 "Placa-Mae",
    "x670":                 "Placa-Mae",
    "x570":                 "Placa-Mae",
    "am5":                  "Placa-Mae",
    "am4":                  "Placa-Mae",
    "lga 1700":             "Placa-Mae",
    "lga1700":              "Placa-Mae",
    "lga 1851":             "Placa-Mae",
    "lga1851":              "Placa-Mae",
}

FORA_DO_ESCOPO = {
    "monitor", "mouse", "teclado", "headset", "headphone", "fone",
    "webcam", "microfone", "caixa de som", "caixinha", "nobreak",
    "cabo", "adaptador", "hub", "roteador", "switch", "impressora",
    "cooler", "water cooler", "air cooler", "pasta termica",
    "suporte", "rack", "mesa", "cadeira", "mousepad", "pad",
    "notebook", "laptop", "gabinete", "kit upgrade", "pendrive",
    "cartao de memoria", "leitor de cartao", "fonte de mesa",
    "estabilizador", "ups", "carregador", "bateria",
}

ALIAS_QUERY = {
    "hd":           "SSD HD",
    "armazenamento":"SSD",
    "memoria":      "memoria RAM",
    "proc":         "processador",
    "mobo":         "placa mae",
    "board":        "placa mae",
    "vga":          "placa de video",
    "grafica":      "placa de video",
}

REMOVIVEIS = [
    r"ate\s+r?\$?\s*[\d.,]+\s*(?:reais)?",
    r"abaixo de\s+r?\$?\s*[\d.,]+",
    r"menos de\s+r?\$?\s*[\d.,]+",
    r"por\s+ate\s+r?\$?\s*[\d.,]+",
    r"r?\$?\s*[\d.,]+\s*reais",
    r"[\d]+\s*%\s*(?:de\s*)?(?:desconto|off)",
    r"(?:desconto|off)\s*(?:de|acima de)?\s*[\d]+\s*%",
    r"acima de\s*[\d]+\s*%",
    r"mais de\s*[\d]+\s*%",
    r"minimo\s*[\d]+\s*%",
    r"\b(?:com|de|ate|por|em|e|mais|baratos?|barata|baratas|bom|boa|bons"
    r"|boas|melhor|melhores|barato|quero|preciso|buscar|busco|encontrar"
    r"|achar|ver|listar|mostrar|tem|ha|existe|disponivel|disponiveis)\b",
]

PADROES_PRECO = [
    r"(?:ate|abaixo de|menos de|por ate|maximo|max|custar?|custa)\s*r?\$?\s*([\d.,]+)",
    r"r?\$?\s*([\d.,]+)\s*(?:reais|max|maximo)",
    r"([\d.,]+)\s*(?:reais|r\$)",
]

PADROES_DESCONTO = [
    r"([\d]+)\s*%\s*(?:de\s*)?(?:desconto|off)",
    r"(?:desconto|off)\s*(?:de|acima de|minimo|maior que|mais que)?\s*([\d]+)\s*%",
    r"acima de\s*([\d]+)\s*%",
    r"mais de\s*([\d]+)\s*%",
    r"minimo\s*(?:de\s*)?([\d]+)\s*%",
    r"([\d]+)\s*porcento",
]

PADROES_LIMITE = [
    r"(?:top|melhores|primeiros?|mais baratos?)\s*([\d]+)",
    r"([\d]+)\s*(?:resultados?|produtos?|opcoes?|itens?)",
    r"mostre?\s*([\d]+)",
    r"lista\s*([\d]+)",
]


def _sem_acento(texto: str) -> str:
    return unicodedata.normalize("NFD", texto).encode("ascii", "ignore").decode("ascii").lower()


def _extrair_preco(texto: str) -> Optional[float]:
    for p in PADROES_PRECO:
        m = re.search(p, texto, re.IGNORECASE)
        if m:
            try:
                val = m.group(1).replace(".", "").replace(",", ".")
                resultado = float(val)
                if resultado > 0:
                    return resultado
            except ValueError:
                continue
    return None


def _extrair_desconto(texto: str) -> Optional[int]:
    for p in PADROES_DESCONTO:
        m = re.search(p, texto, re.IGNORECASE)
        if m:
            try:
                val = int(m.group(1))
                if 1 <= val <= 99:
                    return val
            except ValueError:
                continue
    return None


def _extrair_limite(texto: str) -> int:
    for p in PADROES_LIMITE:
        m = re.search(p, texto, re.IGNORECASE)
        if m:
            try:
                val = int(m.group(1))
                if 1 <= val <= 50:
                    return val
            except ValueError:
                continue
    return 10


def _extrair_categoria(texto_norm: str) -> Optional[str]:
    for termo in FORA_DO_ESCOPO:
        if termo in texto_norm:
            return None
    for chave, categoria in sorted(MAPA_CATEGORIA.items(), key=lambda x: -len(x[0])):
        if chave in texto_norm:
            return categoria
    return None


def _aplicar_alias(texto: str) -> str:
    norm = _sem_acento(texto)
    for alias, expansao in ALIAS_QUERY.items():
        padrao = r"\b" + re.escape(alias) + r"\b"
        if re.search(padrao, norm, re.IGNORECASE):
            texto = re.sub(padrao, expansao, texto, flags=re.IGNORECASE)
    return texto


def _limpar_query(texto: str) -> str:
    resultado = texto
    for p in REMOVIVEIS:
        resultado = re.sub(p, " ", resultado, flags=re.IGNORECASE)
    resultado = re.sub(r"\s+", " ", resultado).strip()
    return resultado


def interpretar(pergunta: str) -> dict:
    pergunta_expandida = _aplicar_alias(pergunta)
    norm      = _sem_acento(pergunta_expandida)
    categoria = _extrair_categoria(norm)
    preco_max = _extrair_preco(norm)
    desconto  = _extrair_desconto(norm)
    limite    = _extrair_limite(norm)
    query     = _limpar_query(pergunta_expandida)
    return {
        "query":        query or pergunta,
        "categoria":    categoria,
        "preco_max":    preco_max,
        "desconto_min": desconto,
        "limite":       limite,
        "fonte":        "regras",
    }


def _baixar_modelo() -> bool:
    if os.path.exists(MODELO_PATH):
        return True
    try:
        from huggingface_hub import hf_hub_download
        print("Baixando modelo de IA (primeira execucao, ~700MB)...")
        print("Isso ocorre apenas uma vez.")
        os.makedirs(MODELO_DIR, exist_ok=True)
        hf_hub_download(
            repo_id   = MODELO_REPO,
            filename  = MODELO_ARQUIVO,
            local_dir = MODELO_DIR,
        )
        print("Modelo baixado.")
        return True
    except Exception as e:
        print(f"Erro ao baixar modelo: {e}")
        return False


def ia_disponivel() -> bool:
    return os.path.exists(MODELO_PATH)


def ia_inicializar() -> bool:
    return _baixar_modelo()