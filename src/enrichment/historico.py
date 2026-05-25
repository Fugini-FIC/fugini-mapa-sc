# ============================================================
# src/enrichment/historico.py
# Enriquece clientes com faturamento NF do banco erp_progress.
# ============================================================

import logging
import pandas as pd
import psycopg2

logger = logging.getLogger(__name__)

PG_ERP = dict(
    host="192.168.0.242",
    port=5432,
    dbname="erp_progress",
    user="postgres",
    password="Postgres2025",
)


def carregar_historico() -> pd.DataFrame:
    query = """
    WITH resumo AS (
        SELECT
            cod_cliente,
            MAX(data_emissao)              AS ultima_compra,
            SUM(valor_item_nf)             AS total_faturado,
            COUNT(DISTINCT nr_nota_fiscal) AS nr_notas
        FROM faturamento_nf
        GROUP BY cod_cliente
    ),
    ultimo_item AS (
        SELECT DISTINCT ON (f.cod_cliente)
            f.cod_cliente,
            f.cod_item   AS cod_ultimo_produto,
            f.qt_cxs_nf  AS ultima_qt_pedida
        FROM faturamento_nf f
        INNER JOIN resumo r
            ON f.cod_cliente   = r.cod_cliente
            AND f.data_emissao = r.ultima_compra
        ORDER BY f.cod_cliente, f.valor_item_nf DESC
    )
    SELECT
        r.cod_cliente,
        r.ultima_compra,
        r.total_faturado,
        r.nr_notas,
        TRIM(COALESCE(it.descricao_1, '') || COALESCE(it.descricao_2, '')) AS ultimo_produto,
        u.ultima_qt_pedida
    FROM resumo r
    LEFT JOIN ultimo_item u ON r.cod_cliente = u.cod_cliente
    LEFT JOIN itens it      ON u.cod_ultimo_produto = it.it_codigo
    """

    conn = psycopg2.connect(**PG_ERP)
    try:
        with conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
        df = pd.DataFrame(rows, columns=cols)
        logger.info(f"Faturamento NF carregado: {len(df):,} clientes.")
        return df
    except Exception as e:
        logger.warning(f"Não foi possível carregar faturamento NF: {e}")
        return pd.DataFrame(columns=[
            "cod_cliente", "ultima_compra", "total_faturado",
            "nr_notas", "ultimo_produto", "ultima_qt_pedida"
        ])
    finally:
        conn.close()


def enriquecer_com_historico(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["cod_cliente_int"] = pd.to_numeric(df["cod_cliente"], errors="coerce")

    historico = carregar_historico()

    if historico.empty:
        for col in ["ultima_compra", "total_faturado", "nr_notas",
                    "ultimo_produto", "ultima_qt_pedida"]:
            df[col] = None
        return df

    historico["cod_cliente"] = pd.to_numeric(historico["cod_cliente"], errors="coerce")

    df = df.merge(
        historico.rename(columns={"cod_cliente": "cod_cliente_int"}),
        on="cod_cliente_int",
        how="left",
    )

    com_historico = df["ultima_compra"].notna().sum()
    sem_historico = df["ultima_compra"].isna().sum()
    logger.info(f"Enriquecimento: {com_historico} com faturamento | {sem_historico} sem faturamento")

    df = df.drop(columns=["cod_cliente_int"])
    return df
