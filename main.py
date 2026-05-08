import sys
import os
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def instalar_dependencias():
    req = os.path.join(os.path.dirname(os.path.abspath(__file__)), "requirements.txt")
    if not os.path.exists(req):
        print("requirements.txt nao encontrado.")
        sys.exit(1)
    print("Verificando dependencias...")
    r = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", req, "--quiet"],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        print("Erro ao instalar dependencias:")
        print(r.stderr)
        sys.exit(1)
    print("Dependencias OK.")


instalar_dependencias()


import database
from scraper.terabyte import executar as executar_scraping, SITE_NOME
from services.cache_service import info_cache
from services.search_service import buscar, categorias, estatisticas
from services.ia_service import interpretar, ia_disponivel, ia_inicializar


def preparar_dados():
    print("Inicializando banco de dados...")
    database.inicializar()

    if not database.tem_dados():
        print("Banco vazio. Coletando dados da Terabyte Shop...")
        print("Isso pode levar alguns minutos.")
        print()
        total = executar_scraping(forcar=True)
        print()
        if total > 0:
            print(f"{total} produto(s) salvos.")
        else:
            print("Falha na coleta. Verifique sua conexao com a internet.")
        print()
        return

    cache = info_cache(SITE_NOME)
    if cache.get("coletado") and not cache.get("valido"):
        print(f"Dados desatualizados ({cache['horas_desde']}h). Atualizando...")
        total = executar_scraping(forcar=True)
        if total > 0:
            print(f"{total} produto(s) atualizados.")
        print()
    elif cache.get("coletado"):
        print(f"Dados atualizados. Ultima coleta: {cache['ultima_coleta']} ({cache['total_salvo']} produtos)")
        print()
    else:
        print("Iniciando coleta...")
        total = executar_scraping(forcar=True)
        print(f"{total} produto(s) salvos.")
        print()


def preparar_ia() -> bool:
    if ia_disponivel():
        print("IA disponivel (modelo local).")
        print()
        return True
    print("Modelo de IA nao encontrado.")
    print("Deseja baixar agora? (~700MB, ocorre so uma vez) [s/N]: ", end="")
    resposta = input().strip().lower()
    if resposta == "s":
        ok = ia_inicializar()
        print()
        return ok
    print("Usando parser de regras para interpretar as buscas.")
    print()
    return False


def formatar_preco(valor) -> str:
    if valor is None:
        return "—"
    return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def exibir_resultado(oferta: dict, idx: int):
    titulo       = oferta.get("titulo", "")[:72]
    preco        = formatar_preco(oferta.get("preco_atual"))
    antigo       = formatar_preco(oferta.get("preco_antigo"))
    desc         = oferta.get("desconto_pct")
    cat          = oferta.get("categoria", "")
    link         = oferta.get("link", "")
    desconto_str = f"  [-{desc}%]" if desc else ""
    antigo_str   = f"  antes: {antigo}" if oferta.get("preco_antigo") else ""

    print(f"  {idx}. {titulo}")
    print(f"     {preco}{antigo_str}{desconto_str}")
    print(f"     {cat}  |  {link[:65]}")


def exibir_stats():
    s = estatisticas()
    print(f"\n  Total de produtos : {s['total']}")
    print(f"  Desconto medio    : {s['desconto_medio']}%")
    print(f"  Maior desconto    : {s['maior_desconto']}%")
    print(f"  Menor preco       : {formatar_preco(s['menor_preco'])}")
    print(f"  Preco medio       : {formatar_preco(s['preco_medio'])}")
    print(f"  Maior preco       : {formatar_preco(s['maior_preco'])}")
    print()
    print("  Por categoria:")
    for cat, qtd in s["por_categoria"].items():
        print(f"    {cat:<22} {qtd} produtos")
    print()


def exibir_ajuda():
    print()
    print("  Exemplos de busca:")
    print("    rtx 4060                        busca por termo livre")
    print("    memoria ram ddr5 16gb           detecta categoria automaticamente")
    print("    ssd nvme 1tb ate 400 reais      com filtro de preco")
    print("    placa de video 30% desconto     com filtro de desconto")
    print("    top 20 processadores ryzen      ajusta o limite de resultados")
    print("    vga ate 2000                    alias: vga = placa de video")
    print("    mobo am5                        alias: mobo = placa mae")
    print()
    print("  Comandos especiais:")
    print("    stats      exibe estatisticas do banco")
    print("    atualizar  forca novo scraping da Terabyte Shop")
    print("    ajuda      exibe esta tela")
    print("    sair       encerra o programa")
    print()


def loop_pesquisa():
    cats = categorias()
    print("Categorias disponiveis:", ", ".join(cats))
    print('Digite "ajuda" para ver exemplos de busca ou "sair" para encerrar.')
    print()

    while True:
        try:
            pergunta = input("Pesquisar: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            print("Encerrando.")
            break

        cmd = pergunta.lower()

        if cmd in ("sair", "exit", "quit", ""):
            print("Encerrando.")
            break

        if cmd == "stats":
            exibir_stats()
            continue

        if cmd == "ajuda":
            exibir_ajuda()
            continue

        if cmd == "atualizar":
            print("Forcando nova coleta da Terabyte Shop...")
            print("Isso pode levar alguns minutos.")
            print()
            total = executar_scraping(forcar=True)
            print()
            if total > 0:
                print(f"{total} produto(s) atualizados.")
            else:
                print("Falha na coleta. Verifique sua conexao.")
            print()
            continue

        filtros = interpretar(pergunta)

        partes = []
        if filtros.get("query") and filtros["query"].lower() != pergunta.lower():
            partes.append(f'"{filtros["query"]}"')
        if filtros.get("categoria"):
            partes.append(f"categoria: {filtros['categoria']}")
        if filtros.get("preco_max"):
            partes.append(f"preco max: {formatar_preco(filtros['preco_max'])}")
        if filtros.get("desconto_min"):
            partes.append(f"desconto min: {filtros['desconto_min']}%")
        if filtros.get("limite") and filtros["limite"] != 10:
            partes.append(f"limite: {filtros['limite']}")
        if partes:
            print(f"Filtros: {' | '.join(partes)}")

        resultados = buscar(
            query        = filtros.get("query"),
            categoria    = filtros.get("categoria"),
            preco_max    = filtros.get("preco_max"),
            desconto_min = filtros.get("desconto_min"),
            limite       = filtros.get("limite", 10),
        )

        if not resultados:
            print("Nenhum produto encontrado.")
            print()
            continue

        print(f"\n{len(resultados)} resultado(s):")
        print("-" * 65)
        for i, oferta in enumerate(resultados, 1):
            exibir_resultado(oferta, i)
        print()


def main():
    preparar_dados()
    preparar_ia()

    print("Sistema pronto. Pesquise em linguagem natural ou por palavras-chave.")
    print('Exemplos: "RTX 4060", "memoria ram ddr5 ate 300 reais", "top 5 ssd"')
    print()

    loop_pesquisa()


if __name__ == "__main__":
    main()