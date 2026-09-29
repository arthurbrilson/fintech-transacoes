# 💳 Fintech — Monitoramento de Transações

Aplicação desenvolvida para o exercício de Ciência de Dados, com foco em ingestão, limpeza, transformação, agregação, detecção de anomalias e visualização de transações financeiras.

## 1. Estrutura do projeto

```text
fintech_transacoes_app/
├── app.py
├── criar_dados.py
├── requirements.txt
├── README.md
└── .gitignore
```

## 2. Como executar

### Pré-requisitos

- Python 3.10+
- Git

### Instalação

No terminal:

```bash
git clone https://github.com/SEU-USUARIO/fintech-transacoes.git
cd fintech-transacoes
python -m venv .venv
```

Ative o ambiente virtual:

**Windows**
```bash
.venv\Scripts\activate
```

**Linux/macOS**
```bash
source .venv/bin/activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

### Gerar os dados

O script fornecido pela Engenharia gera os dois arquivos utilizados pela aplicação:

```bash
python criar_dados.py
```

O script cria:

- `transacoes.csv`
- `cotacoes.csv`

O arquivo de transações é salvo em `latin1`, conforme especificação do exercício. O próprio script disponibilizado para o exercício confirma essa geração. 

### Iniciar a aplicação

```bash
streamlit run app.py
```

A aplicação será aberta no navegador.

## 3. Requisitos atendidos

### Ingestão e limpeza

- `transacoes.csv` é lido com `encoding="latin1"`.
- Valores ausentes de `valor` são preenchidos pela mediana do respectivo `estado_cliente`.
- A coluna `plataforma` recebe o valor estático `Mobile`.
- `data_transacao` é convertida para datetime e localizada em `America/Sao_Paulo`.
- São criadas as colunas `dia_semana` e `mes` com `.dt`.
- Duplicidades são removidas com `drop_duplicates(keep="first")`.

### Filtro vetorizado

O filtro de setembro utiliza os operadores bitwise:

```python
(df["mes"] == 9)
& ((df["estado_cliente"] == "SP") | (df["estado_cliente"] == "RJ"))
& (df["valor"] > 5000)
```

### Risco

O nível de risco é associado aos clientes utilizando:

```python
df["nivel_risco"] = df["id_cliente"].map(RISCO_DICT)
```

### Tabela dinâmica

A aplicação utiliza `pd.pivot_table()` com:

- mês nas linhas;
- `nivel_risco` nas colunas;
- soma de `valor`;
- `margins=True` para totais.

### Z-Score

O Z-Score é calculado de forma vetorizada por estado, sem laços `for`:

```python
medias = df.groupby("estado_cliente")["valor"].transform("mean")
desvios = df.groupby("estado_cliente")["valor"].transform("std")
df["z_score"] = (df["valor"] - medias) / desvios
```

As potenciais anomalias são aquelas com:

```python
df["z_score"] > 2.5
```

### Visualização

O gráfico foi construído usando a API orientada a objetos do Matplotlib:

```python
fig, ax = plt.subplots()
```

Ele apresenta:

- valor total diário;
- média móvel de 7 dias;
- eixo Y iniciando em zero com `ax.set_ylim(bottom=0)`;
- título e legendas.

## 4. Publicação no GitHub

Crie um repositório no GitHub e execute:

```bash
git init
git add .
git commit -m "Entrega: aplicação de análise de transações"
git branch -M main
git remote add origin https://github.com/SEU-USUARIO/fintech-transacoes.git
git push -u origin main
```

**Importante:** não é necessário versionar `.venv`, caches ou arquivos temporários. O `.gitignore` já está preparado para isso.

## 5. Observação sobre os dados

O `criar_dados.py` fornecido no exercício gera 1.000 transações e depois replica as primeiras 15 linhas, criando duplicidades propositalmente. Também gera o arquivo de cotações e insere dois valores ausentes em `cotacao_usd`.

Fonte do gerador utilizado no projeto: arquivo fornecido no exercício.
