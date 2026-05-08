# BigONE

Sistema local em Python que coleta promoções de hardware da Terabyte Shop, salva em banco de dados SQLite e permite pesquisa em linguagem natural sem precisar acessar o site a cada consulta.

---

## O que o sistema faz

- Raspa as seções de promoções, placas de vídeo, processadores, memórias RAM, SSDs e placas-mãe da Terabyte Shop
- Salva tudo localmente em SQLite com busca textual via FTS5
- Atualiza os dados uma vez por dia (cache de 24 horas)
- Interpreta buscas em linguagem natural usando regras e, opcionalmente, um modelo de linguagem local (LLM)

---

## Instalação

### 1. Criar e ativar o ambiente virtual

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Se o PowerShell bloquear a execução de scripts:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 2. Instalar as dependências Python

```powershell
pip install -r requirements.txt
```

O `requirements.txt` deve conter:

```
requests
beautifulsoup4
urllib3
huggingface-hub
llama-cpp-python
```

### 3. Instalar o modelo de IA local (opcional)

O modelo é usado para interpretar buscas em linguagem natural de forma mais precisa. É opcional, sem ele o sistema usa um parser de regras.

**Tamanho do download: aproximadamente 700 MB. Ocorre somente uma vez.**

Ao rodar o sistema pela primeira vez, ele vai perguntar:

```
Modelo de IA nao encontrado.
Deseja baixar agora? (~700MB, ocorre so uma vez) [s/N]:
```

Digite `s` e aguarde. O modelo será salvo em `models/llama-3.2-1b-instruct-q4_k_m.gguf`.

Para baixar manualmente antes de rodar o sistema:

```powershell
python -c "
from huggingface_hub import hf_hub_download
hf_hub_download(
    repo_id='hugging-quants/Llama-3.2-1B-Instruct-Q4_K_M-GGUF',
    filename='llama-3.2-1b-instruct-q4_k_m.gguf',
    local_dir='models'
)
print('Modelo baixado.')
"
```

---

## Como usar

```powershell
python main.py
```

Na primeira execução:
1. O banco de dados é criado automaticamente em `data/ofertas.db`
2. O scraping é iniciado automaticamente (leva alguns minutos)
3. O sistema entra no modo de pesquisa

Nas execuções seguintes:
- Se os dados tiverem menos de 24 horas, entra direto na pesquisa
- Se passaram mais de 24 horas, atualiza os dados antes de continuar

---

## Pesquisando

O sistema aceita linguagem natural. Exemplos:

```
Pesquisar: rtx 4060
Pesquisar: memoria ddr5 32gb ate 600 reais
Pesquisar: ssd nvme 1tb 50% desconto
Pesquisar: processador ryzen ate 800
Pesquisar: top 5 placas de video
```

---
