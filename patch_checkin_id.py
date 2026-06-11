"""
Atualiza o trecho do PATCH no checkin.html para passar checkin_id.
Roda uma vez. Faz backup .bak antes de alterar.

Uso:
    python patch_checkin_id.py
"""
import shutil
from pathlib import Path

ARQUIVO = Path(r"C:\Users\accrisci\Desktop\Artur\Projetos\Projeto_19_Mapa_Clientes_Sao_Carlos\data\output\checkin.html")

ANTIGO = """      const res = await fetch(`${API_BASE}/checkin`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          cod_vendedor, cod_cliente, nome_cliente,
          lat_vendedor: lat, lng_vendedor: lng,
          status_visita, observacao
        })
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || 'Erro ao registrar check-in.');
      }

      // 2) Se vier de agendamento, faz PATCH para atualizar status
      let agendamentoAtualizado = false;
      if (agendamentoId) {
        try {
          const patchRes = await fetch(`${API_BASE}/agendamentos?id=${agendamentoId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: status_visita })
          });
          agendamentoAtualizado = patchRes.ok;
        } catch (e) {
          // Check-in foi salvo; só o PATCH falhou. Não bloqueia.
          console.warn('Falha ao atualizar agendamento:', e);
        }
      }"""

NOVO = """      const res = await fetch(`${API_BASE}/checkin`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          cod_vendedor, cod_cliente, nome_cliente,
          lat_vendedor: lat, lng_vendedor: lng,
          status_visita, observacao
        })
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || 'Erro ao registrar check-in.');
      }

      const checkinData = await res.json();
      const checkinId   = checkinData?.id || null;

      // 2) Se vier de agendamento, faz PATCH para atualizar status e vincular checkin_id
      let agendamentoAtualizado = false;
      if (agendamentoId) {
        try {
          const patchRes = await fetch(`${API_BASE}/agendamentos?id=${agendamentoId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: status_visita, checkin_id: checkinId })
          });
          agendamentoAtualizado = patchRes.ok;
        } catch (e) {
          // Check-in foi salvo; só o PATCH falhou. Não bloqueia.
          console.warn('Falha ao atualizar agendamento:', e);
        }
      }"""

if not ARQUIVO.exists():
    print(f"[ERRO] Arquivo não encontrado: {ARQUIVO}")
    exit(1)

conteudo = ARQUIVO.read_text(encoding="utf-8")

if "checkinData" in conteudo:
    print("[SKIP] Já está patcheado.")
    exit(0)

if ANTIGO not in conteudo:
    print("[ERRO] Trecho esperado não encontrado. O arquivo pode ter sido alterado.")
    exit(1)

bak = ARQUIVO.with_suffix(ARQUIVO.suffix + ".bak")
shutil.copy2(ARQUIVO, bak)
print(f"[BACKUP] {bak.name}")

ARQUIVO.write_text(conteudo.replace(ANTIGO, NOVO), encoding="utf-8")
print("[OK] checkin.html patcheado com checkin_id no PATCH.")
