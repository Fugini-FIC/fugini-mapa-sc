# ============================================================
# src/ingestion/loader.py
# Carrega clientes da região de São Carlos diretamente do
# totvs_cliente.csv (\\192.168.0.226\pdi\in\full\).
#
# Filtros aplicados:
#   - cod-ibge nos municípios alvo (São Carlos, Araraquara, Ibaté, Itirapina)
#   - status-cliente == 'Ativo'
#   - NomERC in ['DISPONIVEL - FS', ''] (clientes disponíveis para prospecção)
# ============================================================

import logging
import pandas as pd
from config.settings import TOTVS_CLIENTE_CSV, IBGE_ALVO

logger = logging.getLogger(__name__)

# Mapeamento de colunas do CSV para nomes canônicos do pipeline
MAPEAMENTO = {
    "cod-cliente":   "cod_cliente",
    "nome-cliente":  "nome_cliente",
    "limite-disp":   "limite_disp",
    "lat-cliente":   "lat_totvs",
    "long-cliente":  "lng_totvs",
    "endereco":      "endereco",
    "bairro":        "bairro",
    "cep":           "cep",
    "cod-ibge":      "cod_ibge",
    "telefone":      "telefone",
    "cnpj":          "cnpj",
}

NOMERC_VALIDOS = {"DISPONIVEL - FS", ""}


def carregar_clientes() -> pd.DataFrame:
    """
    Lê o totvs_cliente.csv, filtra por região e disponibilidade,
    e retorna DataFrame com colunas canônicas.
    """
    logger.info(f"Lendo CSV: {TOTVS_CLIENTE_CSV}")
    df = pd.read_csv(TOTVS_CLIENTE_CSV, encoding="latin1", sep=";", dtype=str)
    logger.info(f"  {len(df):,} clientes no CSV total.")

    # Filtro por município
    ibge_str = {str(i) for i in IBGE_ALVO}
    df["cod-ibge"] = df["cod-ibge"].str.strip()
    mask_ibge = df["cod-ibge"].isin(ibge_str)

    # Filtro por status ativo
    mask_ativo = df["status-cliente"].str.strip() == "Ativo"

    # Filtro por disponibilidade (NomERC)
    mask_nomerc = df["NomERC"].fillna("").str.strip().isin(NOMERC_VALIDOS)

    df = df[mask_ibge & mask_ativo & mask_nomerc].copy()
    logger.info(f"  {len(df):,} clientes disponíveis na região.")

    # Renomeia colunas
    df = df.rename(columns=MAPEAMENTO)

    # Tipos numéricos
    for col in ["lat_totvs", "lng_totvs", "limite_disp"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["cod_ibge"]   = pd.to_numeric(df["cod_ibge"], errors="coerce")
    df["cod_cliente"] = df["cod_cliente"].astype(str).str.strip()
    df["fonte"]       = "sao_carlos"

    # Mantém só colunas canônicas disponíveis
    colunas = [c for c in MAPEAMENTO.values() if c in df.columns]
    df = df[colunas + ["fonte"]].copy()

    logger.info(f"  Colunas: {df.columns.tolist()}")
    return df
