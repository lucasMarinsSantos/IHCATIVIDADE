import os
import sqlite3
from contextlib import closing
from config import DB_PATH

def conectar() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA foreign_keys=ON')
    conn.execute('PRAGMA cache_size=-32000')
    conn.execute('PRAGMA synchronous=NORMAL')
    conn.execute('PRAGMA temp_store=MEMORY')
    return conn

def inicializar(tentar_recuperar: bool=True):
    try:
        with closing(conectar()) as conn:
            cur = conn.cursor()
            cur.execute('\n                CREATE TABLE IF NOT EXISTS ofertas (\n                    id           INTEGER PRIMARY KEY AUTOINCREMENT,\n                    titulo       TEXT    NOT NULL,\n                    preco_atual  REAL    NOT NULL,\n                    preco_antigo REAL,\n                    desconto_pct INTEGER,\n                    link         TEXT    NOT NULL UNIQUE,\n                    categoria    TEXT    NOT NULL,\n                    origem       TEXT    NOT NULL,\n                    data_coleta  TEXT    NOT NULL\n                )\n            ')
            cur.execute('CREATE INDEX IF NOT EXISTS idx_categoria        ON ofertas(categoria)')
            cur.execute('CREATE INDEX IF NOT EXISTS idx_desconto         ON ofertas(desconto_pct)')
            cur.execute('CREATE INDEX IF NOT EXISTS idx_preco            ON ofertas(preco_atual)')
            cur.execute('CREATE INDEX IF NOT EXISTS idx_data_coleta      ON ofertas(data_coleta)')
            cur.execute('CREATE INDEX IF NOT EXISTS idx_cat_desc         ON ofertas(categoria, desconto_pct DESC)')
            cur.execute('CREATE INDEX IF NOT EXISTS idx_cat_preco        ON ofertas(categoria, preco_atual ASC)')
            cur.execute("\n                CREATE VIRTUAL TABLE IF NOT EXISTS ofertas_fts\n                USING fts5(\n                    titulo, categoria, origem,\n                    content='ofertas',\n                    content_rowid='id',\n                    tokenize='unicode61 remove_diacritics 1'\n                )\n            ")
            cur.execute('\n                CREATE TRIGGER IF NOT EXISTS ofertas_ai\n                AFTER INSERT ON ofertas BEGIN\n                    INSERT INTO ofertas_fts(rowid, titulo, categoria, origem)\n                    VALUES (new.id, new.titulo, new.categoria, new.origem);\n                END\n            ')
            cur.execute("\n                CREATE TRIGGER IF NOT EXISTS ofertas_ad\n                AFTER DELETE ON ofertas BEGIN\n                    INSERT INTO ofertas_fts(ofertas_fts, rowid, titulo, categoria, origem)\n                    VALUES ('delete', old.id, old.titulo, old.categoria, old.origem);\n                END\n            ")
            cur.execute("\n                CREATE TRIGGER IF NOT EXISTS ofertas_au\n                AFTER UPDATE ON ofertas BEGIN\n                    INSERT INTO ofertas_fts(ofertas_fts, rowid, titulo, categoria, origem)\n                    VALUES ('delete', old.id, old.titulo, old.categoria, old.origem);\n                    INSERT INTO ofertas_fts(rowid, titulo, categoria, origem)\n                    VALUES (new.id, new.titulo, new.categoria, new.origem);\n                END\n            ")
            cur.execute('\n                CREATE TABLE IF NOT EXISTS cache_coletas (\n                    id            INTEGER PRIMARY KEY AUTOINCREMENT,\n                    site          TEXT    NOT NULL UNIQUE,\n                    ultima_coleta TEXT    NOT NULL,\n                    total_salvo   INTEGER DEFAULT 0\n                )\n            ')
            conn.commit()
    except sqlite3.Error as e:
        print(f'Erro ao inicializar banco de dados: {e}')
        if tentar_recuperar and os.path.exists(DB_PATH):
            backup = DB_PATH + '.bak'
            print(f'Tentando recriar banco... (backup em {backup})')
            try:
                os.rename(DB_PATH, backup)
                inicializar(tentar_recuperar=False)
            except Exception as e2:
                print(f'Falha ao recriar banco: {e2}')
                raise
        else:
            raise

def tem_dados() -> bool:
    try:
        with closing(conectar()) as conn:
            cur = conn.cursor()
            cur.execute('SELECT COUNT(*) FROM ofertas')
            total = cur.fetchone()[0]
            return total > 0
    except sqlite3.Error:
        return False