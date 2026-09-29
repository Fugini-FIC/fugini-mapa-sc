# ============================================================
# config/settings.py
# Configurações centralizadas do Projeto 19 — Mapa São Carlos
# ============================================================

import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent.parent / ".env", override=False)

# ============================================================
# GOOGLE MAPS
# ============================================================
GOOGLE_API_KEY          = os.getenv("GOOGLE_API_KEY", "")
GOOGLE_MAPS_FRONTEND_KEY = os.getenv("GOOGLE_MAPS_FRONTEND_KEY", "")

# ============================================================
# POSTGRESQL
# Host, usuário e senha vêm SÓ do .env — o repo é público, então
# nada de endereço ou credencial com valor padrão no código.
# ============================================================
PG_HOST     = os.environ["PG_HOST"]
PG_PORT     = int(os.getenv("PG_PORT", "5432"))
PG_DBNAME   = os.getenv("PG_DBNAME",   "mapa_clientes")
PG_USER     = os.environ["PG_USER"]
PG_PASSWORD = os.environ["PG_PASSWORD"]


def pg_params(dbname: str = PG_DBNAME) -> dict:
    """Parâmetros de conexão psycopg2 para um banco do servidor de dados."""
    return dict(host=PG_HOST, port=PG_PORT, dbname=dbname,
                user=PG_USER, password=PG_PASSWORD)

# ============================================================
# GITHUB
# ============================================================
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_REPO  = os.getenv("GITHUB_REPO", "Fugini-FIC/fugini-mapa-sc")

# ============================================================
# CRM
# ============================================================
# URL do CRM (Next.js na Vercel). Usada nos popups para levar o vendedor
# a agenda com o cliente ja preenchido. O mapa NAO chama a API de
# agendamentos direto: quem cria a visita e o CRM, atras do login.
CRM_BASE_URL = os.getenv("CRM_BASE_URL", "https://fugini-checkin-api.vercel.app")

# ============================================================
# REGIÃO — São Carlos e entorno
# ============================================================
IBGE_ALVO = [
    3548906,  # São Carlos
    3503208,  # Araraquara
    3519055,  # Ibaté
    3523404,  # Itirapina
]

IBGE_CIDADE = {
    3548906: "São Carlos",
    3503208: "Araraquara",
    3519055: "Ibaté",
    3523404: "Itirapina",
}

NOME_REGIAO = "São Carlos e Região"

# ============================================================
# FONTE DE DADOS — CSV do TOTVS
# ============================================================
TOTVS_CLIENTE_CSV = os.environ["TOTVS_CLIENTE_CSV"]

# ============================================================
# USUÁRIOS DO MAPA
# Senhas vêm do .env (MAPA_SENHA_<USUARIO>) e TÊM de ser iguais a
# vendedores.mapa_senha no Supabase: o CRM abre o mapa com
# mapa_url#mapa_senha e o /api/checkin recusa senha diferente.
# ============================================================

def _senha_mapa(usuario: str) -> str:
    """Senha do mapa, lida do .env como MAPA_SENHA_<USUARIO>."""
    return os.environ[f"MAPA_SENHA_{usuario.upper()}"]

USUARIOS_MAPA = {
    "master_sc":   {"senha": _senha_mapa("master_sc"), "arquivo": "master_sc.html"},
    "vendedor_sc": {"senha": _senha_mapa("vendedor_sc"), "arquivo": "vendedor_sc.html"},
}

# ============================================================
# COR DO MAPA — área única
# ============================================================
COR_AREA = {
    "marker": "#e74c3c",
    "fill":   "#e74c3c",
}

# ============================================================
# GEOCODIFICAÇÃO
# ============================================================
GEOCODING_BATCH_SIZE              = 50
GEOCODING_MAX_WORKERS             = 5
GEOCODING_SLEEP_BETWEEN_BATCHES   = 1.0

# Bounding box do Brasil
GEO_LAT_MIN = -33.75
GEO_LAT_MAX =  5.27
GEO_LNG_MIN = -73.99
GEO_LNG_MAX = -28.84