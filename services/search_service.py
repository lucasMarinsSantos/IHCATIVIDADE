import unicodedata
from typing import Optional
from database import conectar


def _sem_acento(texto: str) -> str:
    return unicodedata.normalize("NFD", texto).encode("ascii", "ignore").decode("ascii").lower()


def buscar(
    query:        Optional[str]   = None,
    categoria:    Optional[str]   = None,
    preco_min:    Optional[float] = None,
    preco_max:    Optional[float] = None,
    desconto_min: Optional[int]   = None,
    ordem:        str = "desconto",
    limite:       int = 10,
) -> list[dict]:
    conn   = conectar()
    cur    = conn.cursor()
    params = []

    if query and query.strip():
        termos = " ".join(f'"{t}"*' for t in query.strip().split())
        sql    = "SELECT o.* FROM ofertas o JOIN ofertas_fts f ON o.id = f.rowid WHERE ofertas_fts MATCH ?"
        params = [termos]
        prefix = "o."
    else:
        sql    = "SELECT * FROM ofertas WHERE 1=1"
        params = []
        prefix = ""

    if categoria:
        sql += f" AND {prefix}categoria LIKE ?"
        params.append(f"%{categoria}%")

    if preco_min is not None:
        sql += f" AND {prefix}preco_atual >= ?"
        params.append(preco_min)

    if preco_max is not None:
        sql += f" AND {prefix}preco_atual <= ?"
        params.append(preco_max)

    if desconto_min is not None:
        sql += f" AND {prefix}desconto_pct >= ?"
        params.append(desconto_min)

    ordens_validas = {
        "desconto": f"{prefix}desconto_pct DESC NULLS LAST, {prefix}preco_atual ASC",
        "preco":    f"{prefix}preco_atual ASC",
        "preco_desc": f"{prefix}preco_atual DESC",
        "recente":  f"{prefix}data_coleta DESC",
        "nome":     f"{prefix}titulo ASC",
    }
    order_clause = ordens_validas.get(ordem, ordens_validas["desconto"])
    sql += f" ORDER BY {order_clause}"

    if int(limite) > 0:
        sql += " LIMIT ?"
        params.append(int(limite))

    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()

    if not rows and categoria:
        return buscar(
            query        = query,
            categoria    = None,
            preco_min    = preco_min,
            preco_max    = preco_max,
            desconto_min = desconto_min,
            ordem        = ordem,
            limite       = limite,
        )

    return [dict(r) for r in rows]


def categorias() -> list[str]:
    conn   = conectar()
    cur    = conn.cursor()
    cur.execute("SELECT DISTINCT categoria FROM ofertas ORDER BY categoria")
    result = [row[0] for row in cur.fetchall()]
    conn.close()
    return result


def estatisticas() -> dict:
    conn = conectar()
    cur  = conn.cursor()
    cur.execute("""
        SELECT
            COUNT(*)                          AS total,
            ROUND(AVG(desconto_pct), 1)       AS desconto_medio,
            MAX(desconto_pct)                 AS maior_desconto,
            ROUND(MIN(preco_atual), 2)        AS menor_preco,
            ROUND(MAX(preco_atual), 2)        AS maior_preco,
            ROUND(AVG(preco_atual), 2)        AS preco_medio
        FROM ofertas
    """)
    row = cur.fetchone()
    cur.execute("SELECT categoria, COUNT(*) as qtd FROM ofertas GROUP BY categoria ORDER BY qtd DESC")
    por_categoria = {r[0]: r[1] for r in cur.fetchall()}
    conn.close()
    return {**dict(row), "por_categoria": por_categoria}