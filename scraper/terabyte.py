import time
import sqlite3
import requests
import urllib3
from bs4 import BeautifulSoup
from typing import Optional

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from config import HEADERS, REQUEST_TIMEOUT, REQUEST_DELAY, MAX_PAGINAS, TERABYTE_BASE, TERABYTE_SECOES
from models.oferta import Oferta
from database import conectar
from utils.text_utils import normalizar_preco, normalizar_titulo, normalizar_link, extrair_desconto_pct
from utils.date_utils import agora_str

SITE_NOME = "Terabyte Shop"


def _get_soup(url: str) -> Optional[BeautifulSoup]:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT, verify=False)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser")
    except requests.RequestException as e:
        print(f"Erro ao acessar {url}: {e}")
        return None


def _parsear_card(card, categoria: str, origem: str) -> Optional[Oferta]:
    titulo_tag = (
        card.select_one("h2.prod-name")
        or card.select_one(".prod-name")
        or card.select_one("h2")
        or card.select_one("a[title]")
    )
    if not titulo_tag:
        return None

    titulo = normalizar_titulo(titulo_tag.get("title") or titulo_tag.get_text())
    if not titulo:
        return None

    link_tag = card.select_one("a[href]")
    if not link_tag:
        return None
    link = normalizar_link(link_tag.get("href", ""), TERABYTE_BASE)
    if not link:
        return None

    preco_tag = (
        card.select_one(".prod-new-price span")
        or card.select_one(".prod-new-price")
        or card.select_one("[class*='new-price']")
        or card.select_one("[class*='price']")
    )
    if not preco_tag:
        return None
    preco_atual = normalizar_preco(preco_tag.get_text())
    if not preco_atual:
        return None

    preco_antigo = None
    antigo_tag = (
        card.select_one(".prod-old-price")
        or card.select_one("[class*='old-price']")
        or card.select_one("s")
        or card.select_one("del")
    )
    if antigo_tag:
        preco_antigo = normalizar_preco(antigo_tag.get_text())

    desconto_pct = None
    badge = (
        card.select_one(".prod-discount")
        or card.select_one("[class*='discount']")
        or card.select_one("[class*='off']")
    )
    if badge:
        desconto_pct = extrair_desconto_pct(badge.get_text())

    return Oferta(
        titulo=titulo,
        preco_atual=preco_atual,
        preco_antigo=preco_antigo,
        desconto_pct=desconto_pct,
        link=link,
        categoria=categoria,
        origem=origem,
        data_coleta=agora_str(),
    )


def _salvar(conn: sqlite3.Connection, oferta: Oferta) -> bool:
    sql = (
        "INSERT INTO ofertas"
        "    (titulo, preco_atual, preco_antigo, desconto_pct, link, categoria, origem, data_coleta)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
        " ON CONFLICT(link) DO UPDATE SET"
        "    titulo       = excluded.titulo,"
        "    preco_atual  = excluded.preco_atual,"
        "    preco_antigo = excluded.preco_antigo,"
        "    desconto_pct = excluded.desconto_pct,"
        "    categoria    = excluded.categoria,"
        "    origem       = excluded.origem,"
        "    data_coleta  = excluded.data_coleta"
    )
    try:
        conn.execute(sql, (
            oferta.titulo, oferta.preco_atual, oferta.preco_antigo,
            oferta.desconto_pct, oferta.link, oferta.categoria,
            oferta.origem, oferta.data_coleta,
        ))
        return True
    except sqlite3.Error:
        return False


def _scrape_secao(url_base: str, categoria: str, origem: str, paginacao: bool) -> list[Oferta]:
    ofertas = []
    pagina  = 1

    while pagina <= MAX_PAGINAS:
        url  = f"{url_base}?pagina={pagina}" if paginacao else url_base
        soup = _get_soup(url)
        if not soup:
            break

        cards = (
            soup.select("li.product-item")
            or soup.select(".product-item")
            or soup.select("div[class*='product-item']")
            or soup.select("li[class*='prod']")
            or soup.select("li:has(a[href*='/produto/'])")
        )

        if not cards:
            break

        novos = []
        for card in cards:
            oferta = _parsear_card(card, categoria, origem)
            if oferta:
                novos.append(oferta)

        ofertas.extend(novos)

        if not paginacao or len(novos) < 10:
            break

        pagina += 1
        time.sleep(REQUEST_DELAY)

    return ofertas


def executar(forcar: bool = False) -> int:
    from services.cache_service import cache_valido, registrar_coleta

    if not forcar and cache_valido(SITE_NOME):
        return -1

    todas = []
    for secao in TERABYTE_SECOES:
        print(f"Coletando {secao['nome']}...")
        parcial = _scrape_secao(
            url_base  = secao["url"],
            categoria = secao["categoria"],
            origem    = secao["nome"],
            paginacao = secao["paginacao"],
        )
        todas.extend(parcial)
        print(f"  {len(parcial)} produto(s)")
        time.sleep(REQUEST_DELAY)

    conn  = conectar()
    salvo = sum(_salvar(conn, o) for o in todas)
    conn.commit()
    conn.close()

    registrar_coleta(SITE_NOME, salvo)
    return salvo