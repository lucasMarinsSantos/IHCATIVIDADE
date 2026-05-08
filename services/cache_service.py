from database import conectar
from utils.date_utils import agora_str, horas_desde, formatar_data
from config import CACHE_HORAS


def cache_valido(site: str) -> bool:
    conn = conectar()
    cur  = conn.cursor()
    cur.execute("SELECT ultima_coleta FROM cache_coletas WHERE site = ?", (site,))
    row  = cur.fetchone()
    conn.close()
    if not row:
        return False
    return horas_desde(row["ultima_coleta"]) < CACHE_HORAS


def registrar_coleta(site: str, total: int):
    conn = conectar()
    conn.execute("""
        INSERT INTO cache_coletas (site, ultima_coleta, total_salvo)
        VALUES (?, ?, ?)
        ON CONFLICT(site) DO UPDATE SET
            ultima_coleta = excluded.ultima_coleta,
            total_salvo   = excluded.total_salvo
    """, (site, agora_str(), total))
    conn.commit()
    conn.close()


def info_cache(site: str) -> dict:
    conn = conectar()
    cur  = conn.cursor()
    cur.execute("SELECT ultima_coleta, total_salvo FROM cache_coletas WHERE site = ?", (site,))
    row  = cur.fetchone()
    conn.close()
    if not row:
        return {"coletado": False}
    horas = horas_desde(row["ultima_coleta"])
    return {
        "coletado":      True,
        "ultima_coleta": formatar_data(row["ultima_coleta"]),
        "total_salvo":   row["total_salvo"],
        "horas_desde":   round(horas, 1),
        "valido":        horas < CACHE_HORAS,
    }
