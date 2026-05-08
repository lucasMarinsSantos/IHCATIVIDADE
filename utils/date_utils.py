from datetime import datetime


def agora_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def horas_desde(data_str: str) -> float:
    if not data_str:
        return float("inf")
    try:
        dt = datetime.strptime(data_str, "%Y-%m-%d %H:%M:%S")
        return (datetime.now() - dt).total_seconds() / 3600
    except ValueError:
        return float("inf")


def formatar_data(data_str: str) -> str:
    if not data_str:
        return "desconhecida"
    try:
        dt = datetime.strptime(data_str, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%d/%m/%Y %H:%M")
    except ValueError:
        return data_str
