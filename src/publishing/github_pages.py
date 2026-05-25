# ============================================================
# src/publishing/github_pages.py
# Publica os HTMLs no GitHub Pages via API.
# ============================================================

import base64
import logging
from pathlib import Path
from github import Github
from config.settings import GITHUB_TOKEN, GITHUB_REPO, USUARIOS_MAPA

logger = logging.getLogger(__name__)

OUTPUT_DIR = Path("data/output")
ARQUIVOS   = ["master_sc.html", "vendedor_sc.html"]


def publicar() -> str:
    logger.info(f"Conectando ao GitHub: {GITHUB_REPO}")
    g    = Github(GITHUB_TOKEN)
    repo = g.get_repo(GITHUB_REPO)

    try:
        branch = repo.get_branch("gh-pages")
        logger.info("Branch 'gh-pages' encontrado.")
    except Exception:
        repo.create_git_ref("refs/heads/gh-pages", repo.get_branch("main").commit.sha)
        logger.info("Branch 'gh-pages' criado.")

    for nome_arquivo in ARQUIVOS:
        path_local = OUTPUT_DIR / nome_arquivo
        if not path_local.exists():
            logger.warning(f"  Arquivo não encontrado: {nome_arquivo}")
            continue

        conteudo = path_local.read_bytes()
        tamanho  = len(conteudo) / 1024
        logger.info(f"  Publicando {nome_arquivo} ({tamanho:.1f} KB)...")

        conteudo_b64 = base64.b64encode(conteudo).decode("utf-8")

        try:
            existente = repo.get_contents(nome_arquivo, ref="gh-pages")
            repo.update_file(
                nome_arquivo,
                f"update: {nome_arquivo}",
                conteudo_b64,
                existente.sha,
                branch="gh-pages",
            )
        except Exception:
            repo.create_file(
                nome_arquivo,
                f"add: {nome_arquivo}",
                conteudo_b64,
                branch="gh-pages",
            )

        logger.info(f"  ✅ {nome_arquivo} atualizado")

    url = f"https://dadaset.github.io/fugini-mapa-sc/"
    logger.info(f"\n🌐 Publicado em: {url}")
    return url
