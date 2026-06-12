import os
import re
import unicodedata
import json
import difflib
from typing import Optional
from config import MODELO_REPO, MODELO_ARQUIVO, MODELO_DIR
MODELO_PATH = os.path.join(MODELO_DIR, MODELO_ARQUIVO)
CATEGORIAS_VALIDAS = {'Placa de Video', 'Processador', 'Memoria RAM', 'SSD', 'Placa-Mae', 'Promocoes'}
MAPA_CATEGORIA = {'placa de video': 'Placa de Video', 'placa video': 'Placa de Video', 'placa mae': 'Placa-Mae', 'placa-mae': 'Placa-Mae', 'memoria ram': 'Memoria RAM', 'intel core': 'Processador', 'motherboard': 'Placa-Mae', 'mainboard': 'Placa-Mae', 'geforce': 'Placa de Video', 'radeon': 'Placa de Video', 'processador': 'Processador', 'core i': 'Processador', 'promocao': 'Promocoes', 'promocoes': 'Promocoes', 'oferta': 'Promocoes', 'ofertas': 'Promocoes', 'desconto': 'Promocoes', 'ryzen': 'Processador', 'athlon': 'Processador', 'threadripper': 'Processador', 'xeon': 'Processador', 'pentium': 'Processador', 'celeron': 'Processador', 'gpu': 'Placa de Video', 'rtx': 'Placa de Video', 'gtx': 'Placa de Video', 'rx 9': 'Placa de Video', 'rx 7': 'Placa de Video', 'rx 6': 'Placa de Video', 'arc a': 'Placa de Video', 'intel arc': 'Placa de Video', 'cpu': 'Processador', 'ddr5': 'Memoria RAM', 'ddr4': 'Memoria RAM', 'ddr3': 'Memoria RAM', 'dimm': 'Memoria RAM', 'sodimm': 'Memoria RAM', 'so-dimm': 'Memoria RAM', 'ram': 'Memoria RAM', 'nvme': 'SSD', 'm.2': 'SSD', 'pcie ssd': 'SSD', 'ssd': 'SSD', 'z890': 'Placa-Mae', 'z790': 'Placa-Mae', 'z690': 'Placa-Mae', 'b850': 'Placa-Mae', 'b840': 'Placa-Mae', 'b760': 'Placa-Mae', 'b650': 'Placa-Mae', 'b550': 'Placa-Mae', 'x870': 'Placa-Mae', 'x670': 'Placa-Mae', 'x570': 'Placa-Mae', 'am5': 'Placa-Mae', 'am4': 'Placa-Mae', 'lga 1700': 'Placa-Mae', 'lga1700': 'Placa-Mae', 'lga 1851': 'Placa-Mae', 'lga1851': 'Placa-Mae', 'pc gamer': 'Promocoes', 'computador': 'Promocoes'}
FORA_DO_ESCOPO = {'monitor', 'mouse', 'teclado', 'headset', 'headphone', 'fone', 'webcam', 'microfone', 'caixa de som', 'caixinha', 'nobreak', 'cabo', 'adaptador', 'hub', 'roteador', 'switch', 'impressora', 'cooler', 'water cooler', 'air cooler', 'pasta termica', 'suporte', 'rack', 'mesa', 'cadeira', 'mousepad', 'pad', 'notebook', 'laptop', 'gabinete', 'kit upgrade', 'pendrive', 'cartao de memoria', 'leitor de cartao', 'fonte de mesa', 'estabilizador', 'ups', 'carregador', 'bateria'}
ALIAS_QUERY = {'hd': 'SSD HD', 'armazenamento': 'SSD', 'memoria': 'memoria RAM', 'proc': 'processador', 'mobo': 'placa mae', 'board': 'placa mae', 'vga': 'placa de video', 'grafica': 'placa de video'}
ALIAS_REGEX = [(re.compile('\\b' + re.escape(alias) + '\\b', re.IGNORECASE), expansao) for alias, expansao in ALIAS_QUERY.items()]
REMOVIVEIS = [re.compile('(?:entre|de)\\s*r?\\$?\\s*[\\d.,]+\\s*(?:a|e|ate)\\s*r?\\$?\\s*[\\d.,]+\\s*(?:reais)?', re.IGNORECASE), re.compile('ate\\s+r?\\$?\\s*[\\d.,]+\\s*(?:reais)?', re.IGNORECASE), re.compile('abaixo de\\s+r?\\$?\\s*[\\d.,]+', re.IGNORECASE), re.compile('menos de\\s+r?\\$?\\s*[\\d.,]+', re.IGNORECASE), re.compile('por\\s+ate\\s+r?\\$?\\s*[\\d.,]+', re.IGNORECASE), re.compile('r?\\$?\\s*[\\d.,]+\\s*reais', re.IGNORECASE), re.compile('[\\d]+\\s*%\\s*(?:de\\s*)?(?:desconto|off)', re.IGNORECASE), re.compile('(?:desconto|off)\\s*(?:de|acima de)?\\s*[\\d]+\\s*%', re.IGNORECASE), re.compile('acima de\\s*[\\d]+\\s*%', re.IGNORECASE), re.compile('mais de\\s*[\\d]+\\s*%', re.IGNORECASE), re.compile('minimo\\s*[\\d]+\\s*%', re.IGNORECASE), re.compile('\\b(?:com|de|ate|por|em|e|mais|baratos?|barata|baratas|bom|boa|bons|boas|melhor|melhores|barato|quero|preciso|buscar|busco|encontrar|achar|ver|listar|mostrar|tem|ha|existe|disponivel|disponiveis|uma?|uns?|umas?)\\b', re.IGNORECASE)]
PADROES_PRECO_FAIXA = [re.compile('(?:entre|de)\\s*r?\\$?\\s*([\\d.,]+)\\s*(?:a|e|ate)\\s*r?\\$?\\s*([\\d.,]+)', re.IGNORECASE)]
PADROES_PRECO = [re.compile('(?:ate|abaixo de|menos de|por ate|maximo|max|custar?|custa)\\s*r?\\$?\\s*([\\d.,]+)', re.IGNORECASE), re.compile('r?\\$?\\s*([\\d.,]+)\\s*(?:reais|max|maximo)', re.IGNORECASE), re.compile('([\\d.,]+)\\s*(?:reais|r\\$)', re.IGNORECASE)]
PADROES_DESCONTO = [re.compile('([\\d]+)\\s*%\\s*(?:de\\s*)?(?:desconto|off)', re.IGNORECASE), re.compile('(?:desconto|off)\\s*(?:de|acima de|minimo|maior que|mais que)?\\s*([\\d]+)\\s*%', re.IGNORECASE), re.compile('acima de\\s*([\\d]+)\\s*%', re.IGNORECASE), re.compile('mais de\\s*([\\d]+)\\s*%', re.IGNORECASE), re.compile('minimo\\s*(?:de\\s*)?([\\d]+)\\s*%', re.IGNORECASE), re.compile('([\\d]+)\\s*porcento', re.IGNORECASE)]
PADROES_LIMITE = [re.compile('(?:top|melhores|primeiros?|mais baratos?)\\s*([\\d]+)', re.IGNORECASE), re.compile('([\\d]+)\\s*(?:resultados?|produtos?|opcoes?|itens?)', re.IGNORECASE), re.compile('mostre?\\s*([\\d]+)', re.IGNORECASE), re.compile('lista\\s*([\\d]+)', re.IGNORECASE)]
REGEX_ESPACOS = re.compile('\\s+')
REGEX_NUMEROS_SOLTOS = re.compile('[\\d\\s]+')
REGEX_LIMITES_TEXTO_1 = re.compile('\\b(?:top|melhores|primeiros?)\\s*\\d+\\b', re.IGNORECASE)
REGEX_LIMITES_TEXTO_2 = re.compile('\\b\\d+\\s*(?:resultados?|produtos?|opcoes?|itens?)\\b', re.IGNORECASE)
PADROES_ORDEM = {'preco_desc': re.compile('\\b(?:caros?|mais caros?)\\b', re.IGNORECASE), 'preco': re.compile('\\b(?:baratos?|mais baratos?|em conta)\\b', re.IGNORECASE), 'recente': re.compile('\\b(?:novos?|recentes?|lancamentos?)\\b', re.IGNORECASE), 'desconto': re.compile('\\b(?:descontos?|melhor desconto|maior desconto)\\b', re.IGNORECASE)}

def _sem_acento(texto: str) -> str:
    return unicodedata.normalize('NFD', texto).encode('ascii', 'ignore').decode('ascii').lower()

def _extrair_precos(texto: str) -> tuple[Optional[float], Optional[float]]:
    for p in PADROES_PRECO_FAIXA:
        m = p.search(texto)
        if m:
            try:
                v1 = float(m.group(1).replace('.', '').replace(',', '.'))
                v2 = float(m.group(2).replace('.', '').replace(',', '.'))
                return (min(v1, v2), max(v1, v2))
            except ValueError:
                pass
    for p in PADROES_PRECO:
        m = p.search(texto)
        if m:
            try:
                val = m.group(1).replace('.', '').replace(',', '.')
                resultado = float(val)
                if resultado > 0:
                    return (None, resultado)
            except ValueError:
                continue
    return (None, None)

def _extrair_desconto(texto: str) -> Optional[int]:
    for p in PADROES_DESCONTO:
        m = p.search(texto)
        if m:
            try:
                for idx in range(1, len(m.groups()) + 1):
                    val_str = m.group(idx)
                    if val_str is not None:
                        val = int(val_str)
                        if 1 <= val <= 99:
                            return val
            except ValueError:
                continue
    return None

def _extrair_limite(texto: str) -> int:
    for p in PADROES_LIMITE:
        m = p.search(texto)
        if m:
            try:
                val = int(m.group(1))
                if 1 <= val <= 50:
                    return val
            except ValueError:
                continue
    return 10

def _extrair_ordem(texto: str) -> str:
    for ordem, padrao in PADROES_ORDEM.items():
        if padrao.search(texto):
            return ordem
    return 'desconto'

def _extrair_categoria(texto_norm: str) -> Optional[str]:
    for termo in FORA_DO_ESCOPO:
        if termo in texto_norm:
            return None
    for chave, categoria in sorted(MAPA_CATEGORIA.items(), key=lambda x: -len(x[0])):
        if chave in texto_norm:
            return categoria
    palavras = texto_norm.split()
    chaves_validas = list(MAPA_CATEGORIA.keys())
    for i in range(len(palavras)):
        matches = difflib.get_close_matches(palavras[i], chaves_validas, n=1, cutoff=0.75)
        if matches:
            return MAPA_CATEGORIA[matches[0]]
        if i < len(palavras) - 1:
            par = f'{palavras[i]} {palavras[i + 1]}'
            matches = difflib.get_close_matches(par, chaves_validas, n=1, cutoff=0.75)
            if matches:
                return MAPA_CATEGORIA[matches[0]]
        if i < len(palavras) - 2:
            trio = f'{palavras[i]} {palavras[i + 1]} {palavras[i + 2]}'
            matches = difflib.get_close_matches(trio, chaves_validas, n=1, cutoff=0.75)
            if matches:
                return MAPA_CATEGORIA[matches[0]]
    return None

def _aplicar_alias(texto: str) -> str:
    norm = _sem_acento(texto)
    for padrao, expansao in ALIAS_REGEX:
        if padrao.search(norm):
            texto = padrao.sub(expansao, texto)
    return texto

def _limpar_query(texto: str) -> str:
    resultado = texto
    for p in REMOVIVEIS:
        resultado = p.sub(' ', resultado)
    resultado = REGEX_ESPACOS.sub(' ', resultado).strip()
    return resultado
_llm_instance = None

def _get_llm():
    global _llm_instance
    if _llm_instance is not None:
        return _llm_instance
    try:
        if os.path.exists(MODELO_PATH):
            from llama_cpp import Llama
            _llm_instance = Llama(model_path=MODELO_PATH, n_ctx=8192, n_gpu_layers=-4, verbose=False)
            return _llm_instance
    except ImportError:
        return None
    except Exception as e:
        print(f'Erro ao carregar LLM: {e}')
        return None
    return None

def _interpretar_com_ia(pergunta: str) -> Optional[dict]:
    llm = _get_llm()
    if not llm:
        return None
    prompt = f"""<|start_header_id|>system<|end_header_id|>\nVocê é um assistente especialista em hardware. Extraia os filtros de busca da pergunta do usuário e retorne APENAS um JSON válido e nada mais. Corrija a ortografia dos termos de busca (ex: rx -> rx, gforce -> geforce).\nFiltros possíveis:\n- query: termos de busca do produto corrigidos (ex: "rtx 4060", "1tb", "ddr5"). NUNCA inclua palavras sobre preço aqui (como "até", "mais", "menos", "reais", valores).\n- categoria: uma destas exatas: "Placa de Video", "Processador", "Memoria RAM", "SSD", "Placa-Mae", "Promocoes". Se não souber, null.\n- preco_min: float (valor mínimo). Ex: "a partir de 500", "mais de 500" = 500.0. "mais ou menos 400" = 350.0. Senão, null.\n- preco_max: float (valor máximo). Ex: "até 1000", "menos de 1000" = 1000.0. "mais ou menos 400" = 450.0. Senão, null.\n- desconto_min: inteiro (desconto mínimo em porcentagem) ou null.\n- limite: inteiro (padrão 10).\n- ordem: "desconto", "preco", "preco_desc", "recente". (Ex: "mais caro" = "preco_desc", "mais barato" = "preco", "lancamento" = "recente").\n\nDiretrizes extras:\n- Em "até X", defina preco_max=X e preco_min=null.\n- Em "a partir de X", defina preco_min=X e preco_max=null.\n- Em "mais ou menos X" ou "cerca de X", defina uma margem (ex: preco_min=X-50 e preco_max=X+50).\n- Infira a categoria (ex: "memoria" -> "Memoria RAM", "placa mae" -> "Placa-Mae").\n- Se a query for apenas a categoria (ex: "ssd"), deixe a query como null e use apenas a categoria.\n\nExemplos:\nUsuario: "quero uma placa d video rx 4060 entre 1500 e 2000 conto top 3 mais cara"\nRetorno: {{'query': \"rx 4060\", \"categoria\": \"Placa de Video\", \"preco_min\": 1500.0, \"preco_max\": 2000.0, \"desconto_min\": null, \"limite\": 3, \"ordem\": \"preco_desc\"}}\nUsuario: "ssd de mais ou menos 400"\nRetorno: {{'query': null, \"categoria\": \"SSD\", \"preco_min\": 350.0, \"preco_max\": 450.0, \"desconto_min\": null, \"limite\": 10, \"ordem\": null}}\nUsuario: "memoria ddr5 a partir de 300 reais mais barata"\nRetorno: {{'query': \"ddr5\", \"categoria\": \"Memoria RAM\", \"preco_min\": 300.0, \"preco_max\": null, \"desconto_min\": null, \"limite\": 10, \"ordem\": \"preco\"}}\n<|eot_id|><|start_header_id|>user<|end_header_id|>\n{pergunta}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n"""
    try:
        response = llm(prompt, max_tokens=150, temperature=0.0, stop=['<|eot_id|>'])
        text = response['choices'][0]['text'].strip()
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1:
            data = json.loads(text[start:end + 1])
            data['fonte'] = 'ia'
            if not isinstance(data.get('query'), str):
                data['query'] = None
            return data
    except Exception as e:
        print(f'Erro no parse da IA: {e}')
        return None
    return None

def interpretar(pergunta: str) -> dict:
    resultado_ia = _interpretar_com_ia(pergunta)
    pergunta_expandida = _aplicar_alias(pergunta)
    norm = _sem_acento(pergunta_expandida)
    categoria = _extrair_categoria(norm)
    preco_min, preco_max = _extrair_precos(norm)
    desconto = _extrair_desconto(norm)
    limite = _extrair_limite(norm)
    ordem = _extrair_ordem(norm)
    query = _limpar_query(pergunta_expandida)
    if categoria:
        for chave in sorted(MAPA_CATEGORIA.keys(), key=lambda x: -len(x)):
            if MAPA_CATEGORIA[chave] == categoria:
                query = re.sub('\\b' + re.escape(chave) + 'e?s?\\b', ' ', query, flags=re.IGNORECASE)
    query = REGEX_LIMITES_TEXTO_1.sub(' ', query)
    query = REGEX_LIMITES_TEXTO_2.sub(' ', query)
    query = REGEX_ESPACOS.sub(' ', query).strip()
    if query and REGEX_NUMEROS_SOLTOS.fullmatch(query):
        query = ''
    regras_dict = {'query': query if query else None, 'categoria': categoria, 'preco_min': preco_min, 'preco_max': preco_max, 'desconto_min': desconto, 'limite': limite, 'ordem': ordem, 'fonte': 'regras'}
    if resultado_ia:
        return {'query': resultado_ia.get('query') or regras_dict['query'], 'categoria': resultado_ia.get('categoria') or regras_dict['categoria'], 'preco_min': resultado_ia.get('preco_min') or regras_dict['preco_min'], 'preco_max': resultado_ia.get('preco_max') or regras_dict['preco_max'], 'desconto_min': resultado_ia.get('desconto_min') or regras_dict['desconto_min'], 'limite': resultado_ia.get('limite') or regras_dict['limite'], 'ordem': resultado_ia.get('ordem') or regras_dict['ordem'], 'fonte': 'ia_hibrido'}
    return regras_dict

def _baixar_modelo() -> bool:
    if os.path.exists(MODELO_PATH):
        return True
    try:
        from huggingface_hub import hf_hub_download
        print('Baixando modelo de IA (primeira execucao, ~700MB)...')
        print('Isso ocorre apenas uma vez.')
        os.makedirs(MODELO_DIR, exist_ok=True)
        hf_hub_download(repo_id=MODELO_REPO, filename=MODELO_ARQUIVO, local_dir=MODELO_DIR)
        print('Modelo baixado.')
        return True
    except Exception as e:
        print(f'Erro ao baixar modelo: {e}')
        return False

def ia_disponivel() -> bool:
    return os.path.exists(MODELO_PATH)

def ia_inicializar() -> bool:
    return _baixar_modelo()