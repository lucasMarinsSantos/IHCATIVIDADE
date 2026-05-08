from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Oferta:
    titulo:       str
    preco_atual:  float
    link:         str
    categoria:    str
    origem:       str
    preco_antigo: Optional[float] = None
    desconto_pct: Optional[int]   = None
    data_coleta:  str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def __post_init__(self):
        if self.desconto_pct is None and self.preco_antigo and self.preco_antigo > 0:
            self.desconto_pct = int(round(((self.preco_antigo - self.preco_atual) / self.preco_antigo) * 100))
