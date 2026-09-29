import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="Fintech | Monitoramento de Transações",
    page_icon="💳",
    layout="wide",
)

BASE_DIR = Path(__file__).resolve().parent
TRANSACOES = BASE_DIR / "transacoes.csv"
COTACOES = BASE_DIR / "cotacoes.csv"

RISCO_DICT = {
    "C100": "Baixo",
    "C101": "Alto",
    "C102": "Médio",
    "C103": "Baixo",
    "C104": "Alto",
}


def carregar_dados():
    """Ingestão e limpeza das transações."""
    df = pd.read_csv(TRANSACOES, encoding="latin1")

    # Imputação da mediana do valor dentro de cada estado.
    medianas_estado = df.groupby("estado_cliente")["valor"].transform("median")
    df["valor"] = df["valor"].fillna(medianas_estado)

    # Rastreabilidade do pipeline.
    df["plataforma"] = "Mobile"

    # Conversão para datetime64[ns] e localização no fuso de São Paulo.
    df["data_transacao"] = pd.to_datetime(df["data_transacao"])
    df["data_transacao"] = df["data_transacao"].dt.tz_localize("America/Sao_Paulo")

    # Extração temporal com .dt.
    df["dia_semana"] = df["data_transacao"].dt.day_name()
    df["mes"] = df["data_transacao"].dt.month

    # Remove duplicidades mantendo a primeira ocorrência.
    df = df.drop_duplicates(keep="first").reset_index(drop=True)

    # Cruzamento por cliente com .map().
    df["nivel_risco"] = df["id_cliente"].map(RISCO_DICT)

    # Z-Score vetorizado por estado, sem laços for.
    medias = df.groupby("estado_cliente")["valor"].transform("mean")
    desvios = df.groupby("estado_cliente")["valor"].transform("std")
    df["z_score"] = (df["valor"] - medias) / desvios

    return df


def carregar_cotacoes():
    """Carrega o segundo arquivo disponibilizado pela Engenharia."""
    return pd.read_csv(COTACOES, encoding="utf-8")


def filtrar_setembro_sp_rj(df):
    """Filtro vetorizado usando exclusivamente & e | nas condições."""
    condicao = (
        (df["mes"] == 9)
        & ((df["estado_cliente"] == "SP") | (df["estado_cliente"] == "RJ"))
        & (df["valor"] > 5000)
    )
    return df.loc[condicao].copy()


def criar_pivot(df):
    """Tabela dinâmica mensal por nível de risco."""
    return pd.pivot_table(
        df,
        index="mes",
        columns="nivel_risco",
        values="valor",
        aggfunc="sum",
        margins=True,
        margins_name="Total",
        fill_value=0,
    )


def criar_anomalias(df):
    return df.loc[df["z_score"] > 2.5].copy()


def grafico_diario(df):
    diario = (
        df.assign(data=df["data_transacao"].dt.date)
        .groupby("data", as_index=True)["valor"]
        .sum()
        .sort_index()
    )
    media_movel = diario.rolling(7).mean()

    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(diario.index, diario.values, label="Valor total diário")
    ax.plot(
        media_movel.index,
        media_movel.values,
        label="Média móvel de 7 dias",
        linewidth=2,
    )
    ax.set_ylim(bottom=0)
    ax.set_title("Valor total de transações por dia")
    ax.set_xlabel("Data")
    ax.set_ylabel("Valor (R$)")
    ax.legend()
    ax.grid(alpha=0.25)
    fig.autofmt_xdate()
    fig.tight_layout()
    return fig


st.title("💳 Monitoramento de Transações — Fintech")
st.caption("Pipeline de ingestão, limpeza, transformação, agregação e detecção de anomalias.")

if not TRANSACOES.exists() or not COTACOES.exists():
    st.error(
        "Arquivos de dados não encontrados. Execute primeiro "
        "`python criar_dados.py` na pasta do projeto."
    )
    st.stop()

df = carregar_dados()
df_cotacoes = carregar_cotacoes()
filtro = filtrar_setembro_sp_rj(df)
pivot = criar_pivot(df)
anomalias = criar_anomalias(df)

# KPIs
c1, c2, c3, c4 = st.columns(4)
c1.metric("Transações após limpeza", f"{len(df):,}".replace(",", "."))
c2.metric("Volume total", f"R$ {df['valor'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
c3.metric("SP/RJ > R$ 5 mil", f"{len(filtro):,}".replace(",", "."))
c4.metric("Potenciais anomalias", f"{len(anomalias):,}".replace(",", "."))

st.divider()

aba1, aba2, aba3, aba4 = st.tabs(
    ["📊 Visão geral", "🔎 Filtro de setembro", "🚨 Anomalias", "🧹 Dados processados"]
)

with aba1:
    st.subheader("Evolução diária")
    st.pyplot(grafico_diario(df), clear_figure=True)

    st.subheader("Tabela dinâmica — valor por mês e nível de risco")
    st.dataframe(pivot.style.format("R$ {:,.2f}"), use_container_width=True)

    st.info(
        "A tabela foi criada com `pivot_table`, usando mês nas linhas, "
        "nível de risco nas colunas, soma de valor e `margins=True`."
    )

with aba2:
    st.subheader("Setembro | SP ou RJ | valor > R$ 5.000")
    st.write(
        "Filtro vetorizado com operadores bitwise `&` e `|`, conforme especificação."
    )
    st.dataframe(
        filtro.sort_values("valor", ascending=False),
        use_container_width=True,
        hide_index=True,
    )

with aba3:
    st.subheader("Potenciais anomalias / fraudes")
    st.write("Critério: Z-Score por estado maior que 2,5.")
    st.dataframe(
        anomalias.sort_values("z_score", ascending=False),
        use_container_width=True,
        hide_index=True,
    )

with aba4:
    st.subheader("Amostra dos dados processados")
    st.dataframe(df.head(100), use_container_width=True, hide_index=True)

    st.subheader("Informações do arquivo de cotações")
    st.write(
        f"O arquivo `cotacoes.csv` possui {len(df_cotacoes)} registros e "
        f"{df_cotacoes['cotacao_usd'].isna().sum()} cotações ausentes. "
        "Ele foi carregado preservando o encoding UTF-8."
    )
    st.dataframe(df_cotacoes, use_container_width=True, hide_index=True)

with st.sidebar:
    st.header("Pipeline")
    st.markdown(
        """
        1. 📥 Leitura `latin1`
        2. 🧹 Mediana por estado
        3. 📱 Plataforma = Mobile
        4. 🕒 Fuso `America/Sao_Paulo`
        5. 📅 Dia da semana e mês
        6. ♻️ Remoção de duplicatas
        7. 🏷️ Risco via `.map()`
        8. 📊 `pivot_table`
        9. 🚨 Z-Score > 2,5
        10. 📈 Média móvel de 7 dias
        """
    )
