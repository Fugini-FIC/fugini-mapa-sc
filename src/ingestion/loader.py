# ============================================================
# src/ingestion/loader.py
# Carrega clientes da região de São Carlos diretamente do
# totvs_cliente.csv (\\192.168.0.226\pdi\in\full\).
#
# Dois grupos de clientes:
#   1. DISPONÍVEIS — sem dono (NomERC vazio), status Ativo
#   2. COM DONO — com representante real, status Ativo,
#      última compra calculada pelo historico.py
#
# O campo `tipo_cliente` distingue os dois grupos no mapa.
# ============================================================

import logging
import pandas as pd
from config.settings import TOTVS_CLIENTE_CSV, IBGE_ALVO, IBGE_CIDADE

logger = logging.getLogger(__name__)

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
    "NomERC":        "representante",
}

# NomERC que indicam cliente disponível (sem representante de campo)
NOMERC_VALIDOS = {"DISPONIVEL - FS", ""}

# NomERC que indicam categorias internas do TOTVS — excluir do mapa
NOMERC_EXCLUIDOS = {"EXPORTAÇÃO", "CLIENTE PLATAFORMA"}


def _normalizar(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns=MAPEAMENTO)
    for col in ["lat_totvs", "lng_totvs", "limite_disp"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df["cod_ibge"]      = pd.to_numeric(df["cod_ibge"], errors="coerce")
    df["cod_cliente"]   = df["cod_cliente"].astype(str).str.strip()
    df["representante"] = df["representante"].fillna("").str.strip()
    # Nome da cidade a partir do dicionário IBGE_CIDADE
    df["cidade"] = df["cod_ibge"].map(IBGE_CIDADE).fillna("Desconhecida")
    return df


def carregar_clientes() -> pd.DataFrame:
    """
    Retorna DataFrame com dois grupos de clientes:
    - tipo_cliente = 'disponivel'  → sem dono, NomERC vazio ou DISPONIVEL - FS
    - tipo_cliente = 'sem_compra'  → com representante real, marcado pelo historico.py
    """
    logger.info(f"Lendo CSV: {TOTVS_CLIENTE_CSV}")
    df_raw = pd.read_csv(TOTVS_CLIENTE_CSV, encoding="latin1", sep=";", dtype=str)
    logger.info(f"  {len(df_raw):,} clientes no CSV total.")

    ibge_str        = {str(i) for i in IBGE_ALVO}
    mask_ibge       = df_raw["cod-ibge"].str.strip().isin(ibge_str)
    mask_ativo      = df_raw["status-cliente"].str.strip() == "Ativo"
    mask_nomerc     = df_raw["NomERC"].fillna("").str.strip().isin(NOMERC_VALIDOS)
    mask_excluidos  = df_raw["NomERC"].fillna("").str.strip().isin(NOMERC_EXCLUIDOS)

    # Grupo 1 — Disponíveis (sem dono)
    df_disp = df_raw[mask_ibge & mask_ativo & mask_nomerc].copy()
    df_disp = _normalizar(df_disp)
    df_disp["tipo_cliente"] = "disponivel"
    df_disp["fonte"]        = "sao_carlos"
    logger.info(f"  Disponíveis: {len(df_disp):,}")

    # Grupo 2 — Com representante real (exclui categorias internas)
    cods_disp = set(df_disp["cod_cliente"])
    df_todos  = df_raw[mask_ibge & mask_ativo & ~mask_excluidos].copy()
    df_todos  = _normalizar(df_todos)
    df_todos  = df_todos[~df_todos["cod_cliente"].isin(cods_disp)].copy()
    df_todos["tipo_cliente"] = "sem_compra"  # provisório — confirmado pelo historico.py
    df_todos["fonte"]        = "sao_carlos"
    logger.info(f"  Com representante (candidatos 60+ dias): {len(df_todos):,}")

    colunas  = [c for c in MAPEAMENTO.values() if c in df_disp.columns] + ["cidade", "tipo_cliente", "fonte"]
    df_disp  = df_disp[[c for c in colunas if c in df_disp.columns]]
    df_todos = df_todos[[c for c in colunas if c in df_todos.columns]]

    df = pd.concat([df_disp, df_todos], ignore_index=True)
    df = df.drop_duplicates(subset="cod_cliente", keep="first")
    logger.info(f"  Total carregado: {len(df):,} clientes")
    return df