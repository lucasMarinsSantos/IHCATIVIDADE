import sys
import os
import subprocess
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
console = Console()
database = None
executar_scraping = None
SITE_NOME = ''
info_cache = None
buscar = None
categorias = None
estatisticas = None
interpretar = None

def ia_disponivel() -> bool:
    return False

def ia_inicializar() -> bool:
    return False

def instalar_dependencias():
    try:
        __import__('bs4')
        __import__('requests')
        __import__('urllib3')
        __import__('curl_cffi')
        __import__('lxml')
        return
    except ImportError:
        pass
    req = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'requirements.txt')
    if not os.path.exists(req):
        console.print('[red]requirements.txt não encontrado.[/red]')
        sys.exit(1)
    with console.status('[dim]Verificando dependencias...[/dim]', spinner='dots'):
        r = subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', req, '--quiet'], capture_output=True, text=True)
    if r.returncode != 0:
        console.print('[red]Erro ao instalar dependencias:[/red]')
        console.print(r.stderr)
        sys.exit(1)

def _importar_modulos():
    global database, executar_scraping, SITE_NOME
    global info_cache, buscar, categorias, estatisticas
    global interpretar, ia_disponivel, ia_inicializar
    import database as _database
    database = _database
    from scraper.terabyte import executar as _executar_scraping, SITE_NOME as _SITE_NOME
    executar_scraping = _executar_scraping
    SITE_NOME = _SITE_NOME
    from services.cache_service import info_cache as _info_cache
    info_cache = _info_cache
    from services.search_service import buscar as _buscar, categorias as _categorias, estatisticas as _estatisticas
    buscar = _buscar
    categorias = _categorias
    estatisticas = _estatisticas
    from services.ia_service import interpretar as _interpretar, ia_disponivel as _ia_disponivel, ia_inicializar as _ia_inicializar
    interpretar = _interpretar
    ia_disponivel = _ia_disponivel
    ia_inicializar = _ia_inicializar

def exibir_banner():
    banner = '\n                      ____  _        ___  _   _ _____ \n                     | __ )(_) __ _ / _ \\| \\ | | ____|\n                     |  _ \\| |/ _` | | | |  \\| |  _|  \n                     | |_) | | (_| | |_| | |\\  | |___ \n                     |____/|_|\\__, |\\___/|_| \\_|_____|\n                              |___/                   \n'
    panel = Panel(Text(banner, style='cyan bold'), title='[bold yellow]Buscador de Ofertas de Hardware[/bold yellow]', subtitle='[dim]Terabyte Shop[/dim]', border_style='cyan')
    console.print(panel)
    console.print()

def formatar_preco(valor) -> str:
    if valor is None:
        return '--'
    return f'R$ {float(valor):,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')

def executar_com_progresso(forcar=False):
    with Progress(SpinnerColumn(), TextColumn('[progress.description]{task.description}'), BarColumn(), TaskProgressColumn(), console=console) as progress:
        task = progress.add_task('[cyan]Coletando ofertas...', total=100)

        def callback(atual, total_max):
            pct = atual / total_max * 100
            progress.update(task, completed=pct)
        total = executar_scraping(forcar=forcar, callback_progresso=callback)
        progress.update(task, completed=100)
    return total

def preparar_dados():
    console.print('[bold]Inicializando banco de dados...[/bold]')
    database.inicializar()
    if not database.tem_dados():
        console.print('[yellow]Banco vazio. Coletando dados da Terabyte Shop...[/yellow]')
        console.print('Isso pode levar alguns minutos.\n')
        total = executar_com_progresso(forcar=True)
        if total > 0:
            console.print(f'\n[green]{total} produto(s) salvos com sucesso.[/green]\n')
        else:
            console.print('[red]\nFalha na coleta. Verifique sua conexao com a internet.[/red]\n')
        return
    cache = info_cache(SITE_NOME)
    if cache.get('coletado') and (not cache.get('valido')):
        console.print(f"[yellow]Dados desatualizados ({cache['horas_desde']}h). Atualizando...[/yellow]")
        total = executar_com_progresso(forcar=True)
        if total > 0:
            console.print(f'\n[green]{total} produto(s) atualizados.[/green]\n')
    elif cache.get('coletado'):
        console.print(f"[green]Dados atualizados.[/green] Ultima coleta: [dim]{cache['ultima_coleta']}[/dim] ([bold]{cache['total_salvo']}[/bold] produtos)\n")
    else:
        console.print('[yellow]Iniciando coleta...[/yellow]')
        total = executar_com_progresso(forcar=True)
        console.print(f'\n[green]{total} produto(s) salvos.[/green]\n')

def preparar_ia() -> bool:
    if ia_disponivel():
        console.print('[green]IA disponivel (modelo local).[/green]\n')
        return True
    console.print('[yellow]Modelo de IA nao encontrado.[/yellow]')
    resposta = console.input('Deseja baixar agora? (~700MB, ocorre so uma vez) [[bold]s[/bold]/N]: ').strip().lower()
    if resposta == 's':
        with console.status('[cyan]Baixando e inicializando o modelo de IA...[/cyan]', spinner='bouncingBar'):
            ok = ia_inicializar()
        console.print()
        return ok
    console.print('[dim]Usando parser de regras para interpretar as buscas.[/dim]\n')
    return False

def exibir_resultados_tabela(resultados):
    table = Table(show_header=True, header_style='bold magenta', expand=True)
    table.add_column('Produto', style='white', ratio=3)
    table.add_column('Preço', style='cyan', justify='right')
    table.add_column('Antigo', style='dim', justify='right')
    table.add_column('Desc.', justify='right')
    table.add_column('Link', style='blue', overflow='fold')
    for idx, r in enumerate(resultados, 1):
        titulo = f"[dim]{idx}.[/dim] {r.get('titulo', '')}"
        preco = formatar_preco(r.get('preco_atual'))
        antigo = formatar_preco(r.get('preco_antigo')) if r.get('preco_antigo') else ''
        desc_pct = r.get('desconto_pct')
        if desc_pct:
            if desc_pct >= 40:
                desc_str = f'[bold bright_green]-{desc_pct}%[/bold bright_green]'
            elif desc_pct >= 20:
                desc_str = f'[green]-{desc_pct}%[/green]'
            else:
                desc_str = f'[yellow]-{desc_pct}%[/yellow]'
        else:
            desc_str = ''
        link = f"[link={r.get('link')}]{r.get('link')[:50]}...[/link]"
        table.add_row(titulo, preco, antigo, desc_str, link)
    console.print(table)

def exibir_stats():
    s = estatisticas()
    table = Table(title='Estatísticas do Banco de Dados', box=None)
    table.add_column('Métrica', style='bold cyan')
    table.add_column('Valor')
    table.add_row('Total de produtos', str(s['total']))
    table.add_row('Desconto médio', f"{s['desconto_medio']}%")
    table.add_row('Maior desconto', f"{s['maior_desconto']}%")
    table.add_row('Menor preço', formatar_preco(s['menor_preco']))
    table.add_row('Preço médio', formatar_preco(s['preco_medio']))
    table.add_row('Maior preço', formatar_preco(s['maior_preco']))
    console.print(Panel(table, border_style='blue'))
    cat_table = Table(title='Por Categoria', box=None)
    cat_table.add_column('Categoria', style='magenta')
    cat_table.add_column('Quantidade', justify='right')
    for cat, qtd in s['por_categoria'].items():
        cat_table.add_row(cat, str(qtd))
    console.print(Panel(cat_table, border_style='blue'))

def exibir_ajuda():
    console.print(Panel('[bold cyan]rtx 4060[/bold cyan]                        busca por termo livre\n[bold cyan]memoria ram ddr5 16gb[/bold cyan]           detecta categoria automaticamente\n[bold cyan]ssd nvme 1tb ate 400 reais[/bold cyan]      com filtro de preco\n[bold cyan]placa de video 30% desconto[/bold cyan]     com filtro de desconto\n[bold cyan]ryzen entre 1000 e 1500 reais[/bold cyan]   com faixa de preco min e max\n[bold cyan]top 20 processadores ryzen[/bold cyan]      ajusta o limite de resultados\n[bold cyan]vga ate 2000[/bold cyan]                    alias: vga = placa de video\n[bold cyan]mobo am5[/bold cyan]                        alias: mobo = placa mae', title='Exemplos de busca', border_style='cyan'))
    console.print(Panel('[bold magenta]stats[/bold magenta]      exibe estatisticas do banco\n[bold magenta]atualizar[/bold magenta]  forca novo scraping da Terabyte Shop\n[bold magenta]limpar[/bold magenta]     limpa a tela do console\n[bold magenta]ajuda[/bold magenta]      exibe esta tela\n[bold magenta]sair[/bold magenta]       encerra o programa', title='Comandos especiais', border_style='magenta'))

def loop_pesquisa():
    try:
        cats = categorias()
        if cats:
            console.print(f"  [bold]Categorias:[/bold] {', '.join(cats)}")
        console.print('  Digite "[bold magenta]ajuda[/bold magenta]" para ver exemplos ou "[bold magenta]sair[/bold magenta]" para encerrar.\n')
    except Exception:
        console.print('  [dim]Sem dados de categorias disponiveis ainda.[/dim]\n')
    while True:
        try:
            pergunta = console.input('[bold cyan]Pesquisar:[/bold cyan] ').strip()
        except (EOFError, KeyboardInterrupt):
            console.print('\nEncerrando.')
            break
        cmd = pergunta.lower()
        if not cmd:
            continue
        if cmd in ('sair', 'exit', 'quit'):
            console.print('Encerrando.')
            break
        if cmd in ('limpar', 'cls', 'clear'):
            os.system('cls' if os.name == 'nt' else 'clear')
            continue
        if cmd == 'stats':
            exibir_stats()
            continue
        if cmd in ('ajuda', 'help'):
            exibir_ajuda()
            continue
        if cmd == 'atualizar':
            console.print('[yellow]Forcando nova coleta da Terabyte Shop...[/yellow]')
            console.print('Isso pode levar alguns segundos (Modo Assíncrono Ultra-Rápido).\n')
            total = executar_com_progresso(forcar=True)
            if total > 0:
                console.print(f'\n[green]{total} produto(s) atualizados.[/green]\n')
            else:
                console.print('[red]\nFalha na coleta. Verifique sua conexao.[/red]\n')
            continue
        filtros = interpretar(pergunta)
        partes = []
        if filtros.get('query') and filtros['query'].lower() != pergunta.lower():
            partes.append(f'''"{filtros['query']}"''')
        if filtros.get('categoria'):
            partes.append(f"categoria: {filtros['categoria']}")
        if filtros.get('preco_min') and filtros.get('preco_max'):
            partes.append(f"preco: {formatar_preco(filtros['preco_min'])} a {formatar_preco(filtros['preco_max'])}")
        elif filtros.get('preco_max'):
            partes.append(f"preco max: {formatar_preco(filtros['preco_max'])}")
        elif filtros.get('preco_min'):
            partes.append(f"preco min: {formatar_preco(filtros['preco_min'])}")
        if filtros.get('desconto_min'):
            partes.append(f"desconto min: {filtros['desconto_min']}%")
        if filtros.get('limite') and filtros['limite'] != 10:
            partes.append(f"limite: {filtros['limite']}")
        if filtros.get('ordem') and filtros['ordem'] != 'desconto':
            partes.append(f"ordem: {filtros['ordem']}")
        if partes:
            console.print(f"[dim]Filtros: {' | '.join(partes)}[/dim]")
        resultados = buscar(query=filtros.get('query'), categoria=filtros.get('categoria'), preco_min=filtros.get('preco_min'), preco_max=filtros.get('preco_max'), desconto_min=filtros.get('desconto_min'), ordem=filtros.get('ordem', 'desconto'), limite=filtros.get('limite', 10))
        if not resultados:
            console.print('[yellow]Nenhum produto encontrado.[/yellow]\n')
            continue
        is_fuzzy = any((r.get('_fuzzy') for r in resultados))
        if is_fuzzy:
            console.print('\n[yellow]Nao encontramos resultados exatos, mas encontramos estas opcoes aproximadas:[/yellow]')
        else:
            console.print(f'\n[bold]{len(resultados)} resultado(s):[/bold]')
        exibir_resultados_tabela(resultados)
        console.print()

def main():
    exibir_banner()
    preparar_dados()
    preparar_ia()
    console.print('[green bold]Sistema pronto.[/green bold] Pesquise em linguagem natural ou por palavras-chave.')
    console.print('[dim]Exemplos: "RTX 4060", "memoria ram ddr5 ate 300 reais", "top 5 ssd"[/dim]\n')
    loop_pesquisa()
if __name__ == '__main__':
    if sys.platform == 'win32':
        os.system('')
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    instalar_dependencias()
    _importar_modulos()
    main()