# BigONE

Buscador de ofertas de hardware focado na Terabyte Shop.

## Sobre o Projeto

BigONE é um sistema local em Python desenvolvido para coletar promoções e ofertas de hardware da Terabyte Shop, armazenando os dados em um banco de dados SQLite otimizado. O sistema permite buscas textuais utilizando FTS5 (Full-Text Search), processando consultas em linguagem natural. O sistema mantém os dados atualizados com uma rotina de cache diário, evitando acessos redundantes ao site original.

### Funcionalidades

- Busca textual em linguagem natural.
- Web scraping de múltiplas categorias de hardware.
- Armazenamento em banco de dados SQLite local.
- Controle de cache com expiração de 24 horas.
- Suporte opcional a modelo LLM local para interpretação de consultas.
- Geração de estatísticas agregadas (preços médios, descontos, volumes por categoria).

### Categorias Suportadas

- Promoções
- Placas de Vídeo
- Processadores
- Memórias RAM
- SSDs
- Placas-Mãe

---

## Arquitetura

O sistema é dividido nos seguintes componentes:

- main.py: Ponto de entrada e interface CLI.
- config.py: Definição de parâmetros e constantes globais.
- database.py: Camada de persistência (SQLite).
- scraper/: Módulo de coleta de dados web.
- services/: Serviços de busca, controle de cache e integração de IA.
- utils/: Funções utilitárias.

---

## Requisitos de Sistema

- Python 3.10 ou superior.
- Conexão com a internet para scraping inicial e (opcionalmente) download do modelo de IA.

---

## Instalação

1. Clone o repositório:
```powershell
git clone https://github.com/seu-usuario/IHCATIVIDADE.git
cd IHCATIVIDADE
```

2. Crie e ative um ambiente virtual:
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

3. Execute a aplicação (as dependências principais serão instaladas automaticamente):
```powershell
python main.py
```

### Instalação de Suporte a IA Local (Opcional)

Para habilitar a interpretação avançada de busca utilizando um modelo de linguagem local:

```powershell
pip install -r requirements-ia.txt
```
Requisito adicional: Compilador C++ (ex: Visual Studio Build Tools). O download inicial do modelo (~700MB) ocorrerá na primeira execução.

---

## Uso

A interface CLI opera de forma interativa. Insira os termos de busca para recuperar resultados da base local. 

Exemplos de consultas suportadas:
- rtx 4060
- memoria ddr5 32gb ate 600 reais
- ssd nvme 1tb 50% desconto
- top 5 placas de video

O interpretador de linguagem natural extrai automaticamente métricas como limite de resultados, faixa de preços e descontos mínimos.

### Comandos Internos

- stats: Exibe estatísticas consolidadas do banco de dados.
- atualizar: Executa a rotina de scraping para renovar o banco de dados antes da expiração do cache.
- ajuda: Exibe informações de uso.
- sair: Finaliza o programa.

---

## Configuração

Parâmetros operacionais podem ser modificados no arquivo config.py. Variáveis principais:

- CACHE_HORAS: Período de validade do banco de dados (padrão: 24).
- REQUEST_TIMEOUT: Tempo limite de resposta HTTP (padrão: 15).
- REQUEST_DELAY: Intervalo entre requisições subsequentes (padrão: 0.8).

---

## Solução de Problemas

Falha de Conexão: Caso a coleta falhe, verifique a conexão com a rede e execute o comando atualizar no CLI.
Erros de Instalação (IA): A instalação do módulo llama-cpp-python pode falhar sem os pacotes de desenvolvimento C++. A base do sistema funcionará normalmente sem este módulo.

---

## Licença

Projeto desenvolvido para fins acadêmicos e educacionais.
