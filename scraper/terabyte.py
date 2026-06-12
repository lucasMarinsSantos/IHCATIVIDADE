import asyncio
from curl_cffi.requests import AsyncSession
import sqlite3
from contextlib import closing
from bs4 import BeautifulSoup
from typing import Optional
from config import HEADERS, REQUEST_TIMEOUT, REQUEST_DELAY, MAX_PAGINAS, TERABYTE_BASE, TERABYTE_SECOES
from models.oferta import Oferta
from database import conectar
from utils.text_utils import normalizar_preco, normalizar_titulo, normalizar_link, extrair_desconto_pct
from utils.date_utils import agora_str
SITE_NOME = 'Terabyte Shop'
MAX_RETRIES = 2
MAX_CONCURRENCY = 20

async def _get_soup_async(session: AsyncSession, url: str) -> Optional[BeautifulSoup]:
    for tentativa in range(MAX_RETRIES + 1):
        try:
            resp = await session.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            text = resp.text
            return BeautifulSoup(text, 'lxml')
        except Exception:
            if tentativa < MAX_RETRIES:
                await asyncio.sleep(REQUEST_DELAY * (tentativa + 1))
    return None

def _parsear_card(card, categoria: str, origem: str) -> Optional[Oferta]:
    titulo_tag = card.select_one('h2.prod-name') or card.select_one('.prod-name') or card.select_one('h2') or card.select_one('a[title]')
    if not titulo_tag:
        return None
    titulo = normalizar_titulo(titulo_tag.get('title') or titulo_tag.get_text())
    if not titulo:
        return None
    link_tag = card.select_one('a[href]')
    if not link_tag:
        return None
    link = normalizar_link(link_tag.get('href', ''), TERABYTE_BASE)
    if not link:
        return None
    preco_tag = card.select_one('.prod-new-price span') or card.select_one('.prod-new-price') or card.select_one("[class*='new-price']") or card.select_one("[class*='price']")
    if not preco_tag:
        return None
    preco_atual = normalizar_preco(preco_tag.get_text())
    if not preco_atual:
        return None
    preco_antigo = None
    antigo_tag = card.select_one('.prod-old-price') or card.select_one("[class*='old-price']") or card.select_one('s') or card.select_one('del')
    if antigo_tag:
        preco_antigo = normalizar_preco(antigo_tag.get_text())
    desconto_pct = None
    badge = card.select_one('.prod-discount') or card.select_one("[class*='discount']") or card.select_one("[class*='off']")
    if badge:
        desconto_pct = extrair_desconto_pct(badge.get_text())
    return Oferta(titulo=titulo, preco_atual=preco_atual, preco_antigo=preco_antigo, desconto_pct=desconto_pct, link=link, categoria=categoria, origem=origem, data_coleta=agora_str())

def _salvar(conn: sqlite3.Connection, oferta: Oferta) -> bool:
    sql = 'INSERT INTO ofertas    (titulo, preco_atual, preco_antigo, desconto_pct, link, categoria, origem, data_coleta) VALUES (?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(link) DO UPDATE SET    titulo       = excluded.titulo,    preco_atual  = excluded.preco_atual,    preco_antigo = excluded.preco_antigo,    desconto_pct = excluded.desconto_pct,    categoria    = excluded.categoria,    origem       = excluded.origem,    data_coleta  = excluded.data_coleta'
    try:
        conn.execute(sql, (oferta.titulo, oferta.preco_atual, oferta.preco_antigo, oferta.desconto_pct, oferta.link, oferta.categoria, oferta.origem, oferta.data_coleta))
        return True
    except sqlite3.Error:
        return False

async def _scrape_pagina_async(session: AsyncSession, url_base: str, categoria: str, origem: str, pagina: int, paginacao: bool) -> list[Oferta]:
    url = f'{url_base}?pagina={pagina}' if paginacao else url_base
    soup = await _get_soup_async(session, url)
    if not soup:
        return []
    cards = soup.select('li.product-item') or soup.select('.product-item') or soup.select("div[class*='product-item']") or soup.select("li[class*='prod']") or soup.select("li:has(a[href*='/produto/'])")
    if not cards:
        return []
    novos = []
    for card in cards:
        oferta = _parsear_card(card, categoria, origem)
        if oferta:
            novos.append(oferta)
    return novos

async def _scrape_secao_async(session: AsyncSession, sem: asyncio.Semaphore, secao: dict) -> list[Oferta]:
    url_base = secao['url']
    categoria = secao['categoria']
    origem = secao['nome']
    paginacao = secao['paginacao']
    if not paginacao:
        async with sem:
            return await _scrape_pagina_async(session, url_base, categoria, origem, 1, False)
    ofertas = []
    tasks = []

    async def task_wrapper(pagina):
        await asyncio.sleep(REQUEST_DELAY * (pagina - 1))
        async with sem:
            return await _scrape_pagina_async(session, url_base, categoria, origem, pagina, True)
    for pagina in range(1, MAX_PAGINAS + 1):
        tasks.append(asyncio.create_task(task_wrapper(pagina)))
    for res in await asyncio.gather(*tasks, return_exceptions=True):
        if isinstance(res, list):
            ofertas.extend(res)
    return ofertas

async def _executar_scraping_async(todas: list, callback_progresso=None):
    total_secoes = len(TERABYTE_SECOES)
    sem = asyncio.Semaphore(MAX_CONCURRENCY)
    async with AsyncSession(impersonate='chrome') as session:
        concluidas = 0

        async def worker(secao, delay_secao):
            nonlocal concluidas
            await asyncio.sleep(delay_secao)
            try:
                parcial = await _scrape_secao_async(session, sem, secao)
                todas.extend(parcial)
            except Exception:
                pass
            finally:
                concluidas += 1
                if callback_progresso:
                    callback_progresso(concluidas, total_secoes)
        tasks = []
        for i, secao in enumerate(TERABYTE_SECOES):
            delay = i * (REQUEST_DELAY * 2)
            tasks.append(asyncio.create_task(worker(secao, delay)))
        await asyncio.gather(*tasks)

def executar_scraping(forcar: bool=False, callback_progresso=None) -> int:
    from services.cache_service import registrar_coleta, cache_valido
    if not forcar and cache_valido(SITE_NOME):
        return -1
    todas: list = []
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_executar_scraping_async(todas, callback_progresso))
        return 0
    except RuntimeError:
        asyncio.run(_executar_scraping_async(todas, callback_progresso))
    if not todas:
        return 0
    links_vistos = set()
    unicas = []
    for o in todas:
        if o.link not in links_vistos:
            links_vistos.add(o.link)
            unicas.append(o)
    with closing(conectar()) as conn:
        for o in unicas:
            _salvar(conn, o)
        conn.commit()
    salvo = len(unicas)
    registrar_coleta(SITE_NOME, salvo)
    return salvo

def executar(forcar: bool=False, callback_progresso=None) -> int:
    return executar_scraping(forcar, callback_progresso)