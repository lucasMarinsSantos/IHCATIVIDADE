import re
import sqlite3
import unicodedata
import difflib
from contextlib import closing
from typing import Optional
from database import conectar

def _sem_acento(texto: str) -> str:
    return unicodedata.normalize('NFD', texto).encode('ascii', 'ignore').decode('ascii').lower()

def _sanitizar_fts(termo: str) -> str:
    return re.sub('[^\\w\\s]', '', termo, flags=re.UNICODE).strip()

def buscar(query: Optional[str]=None, categoria: Optional[str]=None, preco_min: Optional[float]=None, preco_max: Optional[float]=None, desconto_min: Optional[int]=None, ordem: str='desconto', limite: int=10, _usar_fts: bool=True) -> list[dict]:
    rows = []
    use_fts = False
    with closing(conectar()) as conn:
        cur = conn.cursor()
        params: list = []
        prefix = ''
        if _usar_fts and query and query.strip():
            termos_limpos = _sanitizar_fts(query.strip())
            if termos_limpos:
                termos_fts = ' '.join((f'"{t}"*' for t in termos_limpos.split() if t))
                sql = 'SELECT o.* FROM ofertas o JOIN ofertas_fts f ON o.id = f.rowid WHERE ofertas_fts MATCH ?'
                params = [termos_fts]
                prefix = 'o.'
                use_fts = True
        if not use_fts:
            sql = 'SELECT * FROM ofertas WHERE 1=1'
            params = []
            prefix = ''
            if query and query.strip():
                for t in query.strip().split():
                    sql += ' AND titulo LIKE ?'
                    params.append(f'%{t}%')
        if categoria:
            sql += f' AND {prefix}categoria LIKE ?'
            params.append(f'%{categoria}%')
        if preco_min is not None:
            sql += f' AND {prefix}preco_atual >= ?'
            params.append(preco_min)
        if preco_max is not None:
            sql += f' AND {prefix}preco_atual <= ?'
            params.append(preco_max)
        if desconto_min is not None:
            sql += f' AND {prefix}desconto_pct >= ?'
            params.append(desconto_min)
        ordens_validas = {'desconto': f'COALESCE({prefix}desconto_pct, 0) DESC, {prefix}preco_atual ASC', 'preco': f'{prefix}preco_atual ASC', 'preco_desc': f'{prefix}preco_atual DESC', 'recente': f'{prefix}data_coleta DESC', 'nome': f'{prefix}titulo ASC'}
        order_clause = ordens_validas.get(ordem, ordens_validas['desconto'])
        if use_fts:
            sql += f' ORDER BY rank, {order_clause}'
        else:
            sql += f' ORDER BY {order_clause}'
        if int(limite) > 0:
            sql += ' LIMIT ?'
            params.append(int(limite))
        try:
            cur.execute(sql, params)
            rows = cur.fetchall()
            rows = [dict(r) for r in rows]
        except sqlite3.OperationalError:
            pass
    if _usar_fts and query and (not rows):
        try:
            return buscar(query=query, categoria=categoria, preco_min=preco_min, preco_max=preco_max, desconto_min=desconto_min, ordem=ordem, limite=limite, _usar_fts=False)
        except Exception:
            pass
    if not rows and query:
        with closing(conectar()) as conn:
            cur = conn.cursor()
            fuzzy_params: list = []
            fuzzy_sql = 'SELECT * FROM ofertas WHERE 1=1'
            if categoria:
                fuzzy_sql += ' AND categoria LIKE ?'
                fuzzy_params.append(f'%{categoria}%')
            if preco_min is not None:
                fuzzy_sql += ' AND preco_atual >= ?'
                fuzzy_params.append(preco_min)
            if preco_max is not None:
                fuzzy_sql += ' AND preco_atual <= ?'
                fuzzy_params.append(preco_max)
            if desconto_min is not None:
                fuzzy_sql += ' AND desconto_pct >= ?'
                fuzzy_params.append(desconto_min)
            fuzzy_sql += ' ORDER BY COALESCE(desconto_pct, 0) DESC LIMIT 500'
            cur.execute(fuzzy_sql, fuzzy_params)
            todas_ofertas = [dict(r) for r in cur.fetchall()]
        termos_busca = query.lower()
        palavras = termos_busca.split()

        def score_melhorado(titulo):
            titulo_lower = titulo.lower()
            if termos_busca in titulo_lower:
                return 3.0
            match_count = sum((1 for p in palavras if p in titulo_lower))
            bonus = match_count / len(palavras) if palavras else 0
            titulo_palavras = titulo_lower.split()
            total_word_ratio = 0
            for p in palavras:
                best_for_p = 0
                for pt in titulo_palavras:
                    if pt.startswith(p):
                        best_for_p = max(best_for_p, 0.9)
                    else:
                        best_for_p = max(best_for_p, difflib.SequenceMatcher(None, p, pt).ratio())
                total_word_ratio += best_for_p
            avg_word_ratio = total_word_ratio / len(palavras) if palavras else 0
            ratio = difflib.SequenceMatcher(None, termos_busca, titulo_lower).ratio()
            return ratio * 0.2 + avg_word_ratio * 0.5 + bonus * 0.5
        for r in todas_ofertas:
            r['_score'] = score_melhorado(r['titulo'])
            r['_fuzzy'] = True
        todas_ofertas.sort(key=lambda x: x['_score'], reverse=True)
        rows = [r for r in todas_ofertas if r['_score'] > 0.35]
        if rows:
            rows = rows[:limite]
    if not rows and categoria:
        return buscar(query=query, categoria=None, preco_min=preco_min, preco_max=preco_max, desconto_min=desconto_min, ordem=ordem, limite=limite)
    return rows

def categorias() -> list[str]:
    with closing(conectar()) as conn:
        cur = conn.cursor()
        cur.execute('SELECT DISTINCT categoria FROM ofertas ORDER BY categoria')
        result = [row[0] for row in cur.fetchall()]
        return result

def estatisticas() -> dict:
    with closing(conectar()) as conn:
        cur = conn.cursor()
        cur.execute('\n            SELECT\n                COUNT(*)                          AS total,\n                ROUND(COALESCE(AVG(desconto_pct), 0), 1) AS desconto_medio,\n                COALESCE(MAX(desconto_pct), 0)    AS maior_desconto,\n                ROUND(MIN(preco_atual), 2)        AS menor_preco,\n                ROUND(MAX(preco_atual), 2)        AS maior_preco,\n                ROUND(AVG(preco_atual), 2)        AS preco_medio\n            FROM ofertas\n        ')
        row = cur.fetchone()
        cur.execute('SELECT categoria, COUNT(*) as qtd FROM ofertas GROUP BY categoria ORDER BY qtd DESC')
        por_categoria = {r[0]: r[1] for r in cur.fetchall()}
        return {**dict(row), 'por_categoria': por_categoria}