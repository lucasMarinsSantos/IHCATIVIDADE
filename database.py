import os
import sqlite3
from config import DB_PATH


def conectar() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA cache_size=-32000")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA temp_store=MEMORY")
    return conn


def inicializar():
    conn = conectar()
    cur  = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS ofertas (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo       TEXT    NOT NULL,
            preco_atual  REAL    NOT NULL,
            preco_antigo REAL,
            desconto_pct INTEGER,
            link         TEXT    NOT NULL UNIQUE,
            categoria    TEXT    NOT NULL,
            origem       TEXT    NOT NULL,
            data_coleta  TEXT    NOT NULL
        )
    """)

    cur.execute("CREATE INDEX IF NOT EXISTS idx_categoria        ON ofertas(categoria)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_desconto         ON ofertas(desconto_pct)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_preco            ON ofertas(preco_atual)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_data_coleta      ON ofertas(data_coleta)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_cat_desc         ON ofertas(categoria, desconto_pct DESC)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_cat_preco        ON ofertas(categoria, preco_atual ASC)")

    cur.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS ofertas_fts
        USING fts5(
            titulo, categoria, origem,
            content='ofertas',
            content_rowid='id',
            tokenize='unicode61'
        )
    """)

    cur.execute("""
        CREATE TRIGGER IF NOT EXISTS ofertas_ai
        AFTER INSERT ON ofertas BEGIN
            INSERT INTO ofertas_fts(rowid, titulo, categoria, origem)
            VALUES (new.id, new.titulo, new.categoria, new.origem);
        END
    """)

    cur.execute("""
        CREATE TRIGGER IF NOT EXISTS ofertas_ad
        AFTER DELETE ON ofertas BEGIN
            INSERT INTO ofertas_fts(ofertas_fts, rowid, titulo, categoria, origem)
            VALUES ('delete', old.id, old.titulo, old.categoria, old.origem);
        END
    """)

    cur.execute("""
        CREATE TRIGGER IF NOT EXISTS ofertas_au
        AFTER UPDATE ON ofertas BEGIN
            INSERT INTO ofertas_fts(ofertas_fts, rowid, titulo, categoria, origem)
            VALUES ('delete', old.id, old.titulo, old.categoria, old.origem);
            INSERT INTO ofertas_fts(rowid, titulo, categoria, origem)
            VALUES (new.id, new.titulo, new.categoria, new.origem);
        END
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS cache_coletas (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            site          TEXT    NOT NULL UNIQUE,
            ultima_coleta TEXT    NOT NULL,
            total_salvo   INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()


def tem_dados() -> bool:
    conn  = conectar()
    cur   = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM ofertas")
    total = cur.fetchone()[0]
    conn.close()
    return total > 0