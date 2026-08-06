# ⚠️ Documentação movida

Este arquivo era uma **cópia de junho/2026** da documentação do CRM e ficou
defasado. A documentação viva está centralizada no repo **privado**
`FIC-Fugini/fugini-crm`, em **`docs/`** (`docs/README.md` é o índice).

## O essencial DESTE repo (mapa São Carlos)

- **Pipeline diário:** roda no servidor **SRVFGN027** às 06:00 (tarefa
  `Pipeline_Mapa_Clientes_SaoCarlos`, pasta `C:\projetos\Projeto_19_...`).
  ⚠️ O servidor **não faz git pull** — mudou código aqui, copiar os arquivos
  para lá via `\\192.168.0.242\c$\projetos\...`.
- **`src/web/checkin.html`** é a FONTE do formulário de check-in (versionada).
  Publicar só ele, sem rodar o pipeline: `python publicar_checkin.py`
  (tem `--dry-run`). O mesmo arquivo existe no Projeto_23 (SP) — manter os
  dois em sincronia.
- **Ordem de deploy ao apertar validação de campo:** formulário primeiro
  (CDN do GitHub Pages leva ~10 min), API do CRM depois. Receita completa em
  `fugini-crm/docs/README.md`.
- **Popups do mapa:** botões 📍 Check-in e 📅 Agendar (este abre a `/agenda`
  do CRM — o mapa não chama a API de agendamentos). URL do CRM em
  `config/settings.py` (`CRM_BASE_URL`).
- **Crédito no heatmap** é deduplicado por matriz
  (`_df_credito_sem_duplicata_matriz` no `builder.py`) — o ERP replica o
  `limite_disp` da matriz nas filiais; sem isso São Carlos inflava 2,76x.
