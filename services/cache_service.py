from contextlib import closing
from database import conectar
from utils.date_utils import agora_str, horas_desde, formatar_data
from config import CACHE_HORAS

def cache_valido(site: str) -> bool:
    with closing(conectar()) as conn:
        cur = conn.cursor()
        cur.execute('SELECT ultima_coleta FROM cache_coletas WHERE site = ?', (site,))
        row = cur.fetchone()
        if not row:
            return False
        return horas_desde(row['ultima_coleta']) < CACHE_HORAS

def registrar_coleta(site: str, total: int):
    with closing(conectar()) as conn:
        conn.execute('\n            INSERT INTO cache_coletas (site, ultima_coleta, total_salvo)\n            VALUES (?, ?, ?)\n            ON CONFLICT(site) DO UPDATE SET\n                ultima_coleta = excluded.ultima_coleta,\n                total_salvo   = excluded.total_salvo\n        ', (site, agora_str(), total))
        conn.commit()

def info_cache(site: str) -> dict:
    with closing(conectar()) as conn:
        cur = conn.cursor()
        cur.execute('SELECT ultima_coleta, total_salvo FROM cache_coletas WHERE site = ?', (site,))
        row = cur.fetchone()
        if not row:
            return {'coletado': False}
        horas = horas_desde(row['ultima_coleta'])
        return {'coletado': True, 'ultima_coleta': formatar_data(row['ultima_coleta']), 'total_salvo': row['total_salvo'], 'horas_desde': round(horas, 1), 'valido': horas < CACHE_HORAS}