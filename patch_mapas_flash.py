"""
Corrige o flash da tela de login nos mapas master_sc.html e vendedor_sc.html.
Esconde o card por padrão e só mostra se não houver hash na URL.

Uso:
    python patch_mapas_flash.py
"""
import shutil
from pathlib import Path

PASTA_OUTPUT = Path(r"C:\Users\accrisci\Desktop\Artur\Projetos\Projeto_19_Mapa_Clientes_Sao_Carlos\data\output")
ARQUIVOS = ["master_sc.html", "vendedor_sc.html"]

ANTIGO_CSS = "    .card { background: white; border-radius: 12px; padding: 40px;"
NOVO_CSS   = "    .card { display: none; background: white; border-radius: 12px; padding: 40px;"

ANTIGO_JS = """    window.addEventListener('DOMContentLoaded', () => {
      if (window.location.hash && window.location.hash.length > 1) {
        const senhaHash = decodeURIComponent(window.location.hash.substring(1));
        descriptografar(senhaHash);
      }
    });"""

NOVO_JS = """    window.addEventListener('DOMContentLoaded', () => {
      if (window.location.hash && window.location.hash.length > 1) {
        const senhaHash = decodeURIComponent(window.location.hash.substring(1));
        descriptografar(senhaHash);
      } else {
        document.querySelector('.card').style.display = 'block';
      }
    });"""

def patchear(caminho: Path):
    if not caminho.exists():
        print(f"[SKIP] {caminho.name} não encontrado")
        return

    conteudo = caminho.read_text(encoding="utf-8")

    if "display: none; background: white; border-radius: 12px; padding: 40px;" in conteudo:
        print(f"[SKIP] {caminho.name} já está patcheado")
        return

    if ANTIGO_CSS not in conteudo or ANTIGO_JS not in conteudo:
        print(f"[ERRO] Trecho esperado não encontrado em {caminho.name}")
        return

    bak = caminho.with_suffix(caminho.suffix + ".bak")
    shutil.copy2(caminho, bak)
    print(f"[BACKUP] {bak.name}")

    conteudo = conteudo.replace(ANTIGO_CSS, NOVO_CSS)
    conteudo = conteudo.replace(ANTIGO_JS, NOVO_JS)
    caminho.write_text(conteudo, encoding="utf-8")
    print(f"[OK] {caminho.name} patcheado")

for nome in ARQUIVOS:
    patchear(PASTA_OUTPUT / nome)

print("\nPronto. Copie os arquivos para a raiz e faça push no gh-pages.")
