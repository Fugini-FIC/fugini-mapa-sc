# ============================================================
# src/mapping/roteamento.py
# Gera os painéis de roteamento TSP (área individual e master).
# ============================================================

import json
import pandas as pd



def _safe_str(val, default="-") -> str:
    """Converte valor para string, retornando default para None/NaN/nan."""
    if val is None:
        return default
    try:
        if pd.isna(val):
            return default
    except (TypeError, ValueError):
        pass
    s = str(val).strip()
    if s.lower() in ("nan", "none", "nat", ""):
        return default
    return s


def _safe_float(val, default=0.0) -> float:
    """Converte valor para float, retornando default para None/NaN."""
    if val is None:
        return default
    try:
        if pd.isna(val):
            return default
        return float(val)
    except (TypeError, ValueError):
        return default


def _safe_date(val, default="-") -> str:
    """Converte data para string dd/mm/YYYY, retornando default para None/NaN."""
    if val is None:
        return default
    try:
        if pd.isna(val):
            return default
        return pd.Timestamp(val).strftime("%d/%m/%Y")
    except (TypeError, ValueError):
        return default


def _build_cliente_dict(row) -> dict:
    """Monta o dicionário de um cliente para o JSON do roteamento."""
    return {
        "lat":           float(row["lat_final"]),
        "lng":           float(row["lng_final"]),
        "nome":          _safe_str(row.get("nome_cliente"),   "N/D"),
        "cod":           _safe_str(row.get("cod_cliente"),    "N/D"),
        "cidade":        _safe_str(row.get("nome_municipio"), "N/D"),
        "endereco":      _safe_str(row.get("endereco"),       "-"),
        "bairro":        _safe_str(row.get("bairro"),         "-"),
        "cep":           _safe_str(row.get("cep"),            "-"),
        "telefone":      _safe_str(row.get("telefone"),       "-"),
        "cnpj":          _safe_str(row.get("cnpj"),           "-"),
        "credito":       _safe_float(row.get("limite_disp")),
        "ultima_compra": _safe_date(row.get("ultima_compra")),
        # TODO: migrar ultimo_produto para nome do item quando ETL de itens estiver implementado
        # Atualmente: cod_item do faturamento_nf
        # Futuro: JOIN com tabela itens (banco erp_progress) para trazer descricao_1
        "ultimo_produto": _safe_str(row.get("ultimo_produto"), "-"),
        "ultima_qt":      _safe_float(row.get("ultima_qt_pedida")),
        "total_faturado": _safe_float(row.get("total_faturado")),
    }


# ============================================================
# PAINEL DE ROTEAMENTO — ÁREA INDIVIDUAL
# ============================================================

def gerar_roteamento_html(df_area: pd.DataFrame) -> str:
    """
    Gera o painel de roteamento + lógica TSP em JavaScript.
    Aparece no canto inferior direito do mapa.
    """
    clientes_js = json.dumps([
        _build_cliente_dict(row)
        for _, row in df_area.iterrows()
        if pd.notna(row["lat_final"]) and pd.notna(row["lng_final"])
    ], ensure_ascii=False)

    return """
    <div id="painel-rota" style="
        position: fixed;
        bottom: 10px;
        right: 10px;
        z-index: 1000;
        background: rgba(255,255,255,0.97);
        border-radius: 10px;
        padding: 14px 16px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.15);
        min-width: 200px;
        max-width: 230px;
        font-family: 'Segoe UI', Arial, sans-serif;
        border-left: 4px solid #2980b9;
    ">
      <div style="font-size:12px;font-weight:700;color:#2980b9;margin-bottom:8px;">
        🗺️ ROTEIRO
      </div>
      <input id="endereco-partida" type="text" placeholder="Seu endereço de partida"
             style="width:100%;padding:6px 8px;border:1.5px solid #ddd;border-radius:6px;
                    font-size:11px;margin-bottom:6px;box-sizing:border-box;outline:none;">
      <button onclick="calcularRota()"
              style="width:100%;padding:7px;background:#2980b9;color:white;border:none;
                     border-radius:6px;font-size:11px;font-weight:700;cursor:pointer;">
        Calcular Rota
      </button>
      <button id="btn-exportar" onclick="exportarExcel()"
              style="width:100%;padding:7px;background:#27ae60;color:white;border:none;
                     border-radius:6px;font-size:11px;font-weight:700;cursor:pointer;
                     margin-top:4px;display:none;">
        📥 Exportar Excel
      </button>
      <div id="rota-status" style="font-size:10px;color:#888;margin-top:6px;"></div>
      <div id="rota-resultado" style="margin-top:8px;font-size:11px;
                                       max-height:250px;overflow-y:auto;"></div>
    </div>

    <script>
    var CLIENTES = """ + clientes_js + """;
    var CORES_DIAS = ['#e74c3c','#2980b9','#27ae60','#8e44ad','#f39c12','#16a085','#c0392b'];
    var rotaLayers = [];
    var layersPorDia = {};

    function haversineKm(lat1, lng1, lat2, lng2) {
      var R = 6371;
      var dLat = (lat2-lat1)*Math.PI/180;
      var dLng = (lng2-lng1)*Math.PI/180;
      var a = Math.sin(dLat/2)*Math.sin(dLat/2) +
              Math.cos(lat1*Math.PI/180)*Math.cos(lat2*Math.PI/180)*
              Math.sin(dLng/2)*Math.sin(dLng/2);
      return R*2*Math.atan2(Math.sqrt(a),Math.sqrt(1-a));
    }

    function nearestNeighbor(clientes, latP, lngP) {
      var nv = clientes.slice(), rota = [], latA = latP, lngA = lngP;
      while (nv.length > 0) {
        var melhor = null, melhorD = Infinity;
        nv.forEach(function(c) {
          var d = haversineKm(latA, lngA, c.lat, c.lng);
          if (d < melhorD) { melhorD = d; melhor = c; }
        });
        rota.push(melhor);
        latA = melhor.lat; lngA = melhor.lng;
        nv.splice(nv.indexOf(melhor), 1);
      }
      return rota;
    }

    function agruparDias(rota, porDia) {
      var dias = [];
      for (var i = 0; i < rota.length; i += porDia) dias.push(rota.slice(i, i+porDia));
      if (dias.length > 1 && dias[dias.length-1].length === 1) {
        var ultimo = dias.pop()[0];
        var melhorDia = 0, melhorDist = Infinity;
        dias.forEach(function(dia, idx) {
          var ult = dia[dia.length-1];
          var d = haversineKm(ult.lat, ult.lng, ultimo.lat, ultimo.lng);
          if (d < melhorDist) { melhorDist = d; melhorDia = idx; }
        });
        dias[melhorDia].push(ultimo);
      }
      return dias;
    }

    async function geocodificarNominatim(endereco) {
      var url = 'https://nominatim.openstreetmap.org/search?format=json&limit=1&countrycodes=br&q=' +
                encodeURIComponent(endereco);
      var resp = await fetch(url, {headers: {'Accept-Language': 'pt-BR'}});
      var data = await resp.json();
      if (data.length === 0) return null;
      return {lat: parseFloat(data[0].lat), lng: parseFloat(data[0].lon)};
    }

    function getMap() {
      for (var key in window) {
        try { if (key.startsWith('map_') && window[key] && window[key].eachLayer) return window[key]; }
        catch(e) {}
      }
      return null;
    }

    function limparRotas() {
      var m = getMap(); if (!m) return;
      rotaLayers.forEach(function(l) { m.removeLayer(l); });
      rotaLayers = [];
      layersPorDia = {};
    }

    function toggleDia(idx, visible) {
      var m = getMap(); if (!m) return;
      (layersPorDia[idx] || []).forEach(function(l) {
        if (visible) { m.addLayer(l); } else { m.removeLayer(l); }
      });
    }

    function desenharRota(dias, latP, lngP) {
      var m = getMap(); if (!m) return;
      limparRotas();

      dias.forEach(function(dia, idx) {
        var cor = CORES_DIAS[idx % CORES_DIAS.length];
        layersPorDia[idx] = [];
        var pts = [[latP, lngP]];
        dia.forEach(function(c) { pts.push([c.lat, c.lng]); });
        pts.push([latP, lngP]);
        var linha = L.polyline(pts, {color: cor, weight: 3, opacity: 0.8, dashArray: '6,4'}).addTo(m);
        rotaLayers.push(linha);
        layersPorDia[idx].push(linha);

        dia.forEach(function(c, i) {
          var icon = L.divIcon({
            html: '<div style="background:' + cor + ';color:white;border-radius:50%;' +
                  'width:20px;height:20px;display:flex;align-items:center;justify-content:center;' +
                  'font-size:10px;font-weight:700;border:2px solid white;box-shadow:0 1px 3px rgba(0,0,0,0.3);">' +
                  (i+1) + '</div>',
            iconSize: [20,20], iconAnchor: [10,10], className: ''
          });
          var mk = L.marker([c.lat, c.lng], {icon: icon})
            .bindPopup('<b>Dia ' + (idx+1) + ' - Visita ' + (i+1) + '</b><br>' + c.nome + '<br>' + c.cidade)
            .addTo(m);
          rotaLayers.push(mk);
          layersPorDia[idx].push(mk);
        });
      });

      var iconP = L.divIcon({
        html: '<div style="background:#1a1a2e;color:white;border-radius:50%;' +
              'width:24px;height:24px;display:flex;align-items:center;justify-content:center;' +
              'font-size:14px;border:2px solid white;box-shadow:0 1px 3px rgba(0,0,0,0.3);">🏠</div>',
        iconSize: [24,24], iconAnchor: [12,12], className: ''
      });
      rotaLayers.push(L.marker([latP, lngP], {icon: iconP}).bindPopup('<b>Ponto de partida</b>').addTo(m));
    }

    function exibirRoteiro(dias, distTotal) {
      var html = '<div style="font-size:10px;color:#888;margin-bottom:8px;">' +
                 '📏 Distância estimada: ' + distTotal.toFixed(1) + ' km</div>';
      dias.forEach(function(dia, idx) {
        var cor = CORES_DIAS[idx % CORES_DIAS.length];
        html += '<div style="margin-bottom:8px;">';
        html += '<label style="display:flex;align-items:center;cursor:pointer;gap:6px;margin-bottom:3px;">' +
                '<input type="checkbox" checked ' +
                'onchange="toggleDia(' + idx + ', this.checked)" ' +
                'style="width:13px;height:13px;cursor:pointer;accent-color:' + cor + ';">' +
                '<span style="display:inline-block;width:9px;height:9px;border-radius:50%;' +
                'background:' + cor + ';flex-shrink:0;"></span>' +
                '<span style="font-weight:700;font-size:11px;color:#1a1a2e;">Dia ' + (idx+1) + '</span>' +
                '</label>';
        dia.forEach(function(c, i) {
          html += '<div style="padding-left:26px;font-size:10px;color:#444;line-height:1.6;">' +
                  (i+1) + '. ' + c.nome + '</div>';
        });
        html += '</div>';
      });
      document.getElementById('rota-resultado').innerHTML = html;
    }

    async function calcularRota() {
      var endereco = document.getElementById('endereco-partida').value.trim();
      var status   = document.getElementById('rota-status');
      var resultado = document.getElementById('rota-resultado');
      if (!endereco) { status.innerHTML = '⚠️ Digite um endereço.'; return; }

      status.innerHTML = '🔍 Geocodificando...';
      resultado.innerHTML = '';

      var partida = await geocodificarNominatim(endereco);
      if (!partida) { status.innerHTML = '❌ Endereço não encontrado.'; return; }

      status.innerHTML = '⚙️ Calculando rota...';
      var rota  = nearestNeighbor(CLIENTES, partida.lat, partida.lng);
      var dias  = agruparDias(rota, 6);

      var dist = haversineKm(partida.lat, partida.lng, rota[0].lat, rota[0].lng);
      for (var i = 0; i < rota.length-1; i++)
        dist += haversineKm(rota[i].lat, rota[i].lng, rota[i+1].lat, rota[i+1].lng);
      dist += haversineKm(rota[rota.length-1].lat, rota[rota.length-1].lng, partida.lat, partida.lng);

      desenharRota(dias, partida.lat, partida.lng);
      exibirRoteiro(dias, dist);
      status.innerHTML = '✅ ' + dias.length + ' dias | ' + rota.length + ' clientes';
      window._diasRotaAtual = dias;
      var btnExp = document.getElementById('btn-exportar');
      if (btnExp) btnExp.style.display = 'block';
    }

    document.getElementById('endereco-partida').addEventListener('keydown', function(e) {
      if (e.key === 'Enter') calcularRota();
    });

    function exportarExcel() {
      if (!window._diasRotaAtual || window._diasRotaAtual.length === 0) return;
      if (typeof XLSX === 'undefined') {
        var script = document.createElement('script');
        script.src = 'https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js';
        script.onload = function() { _gerarExcel(); };
        document.head.appendChild(script);
      } else {
        _gerarExcel();
      }
    }

    function _gerarExcel() {
      var wb = XLSX.utils.book_new();
      (window._diasRotaAtual || []).forEach(function(dia, idx) {
        var linhas = dia.map(function(c, i) {
          return {
            'Ordem':              i + 1,
            'Código':             c.cod,
            'Cliente':            c.nome,
            'Cidade':             c.cidade,
            'Endereço':           c.endereco,
            'Bairro':             c.bairro,
            'CEP':                c.cep,
            'Telefone':           c.telefone,
            'CNPJ':               c.cnpj,
            'Crédito Disponível': c.credito,
            'Última Compra':      c.ultima_compra,
            'Faturamento Total':  c.total_faturado,
            'Último Produto':     c.ultimo_produto,
            'Qtd Última Compra':  c.ultima_qt,
          };
        });
        var ws = XLSX.utils.json_to_sheet(linhas);
        ws['!cols'] = [
          {wch:6},{wch:10},{wch:35},{wch:20},
          {wch:35},{wch:20},{wch:12},{wch:15},{wch:18},{wch:18},{wch:14},{wch:18},{wch:20},{wch:10}
        ];
        XLSX.utils.book_append_sheet(wb, ws, 'Dia ' + (idx + 1));
      });
      XLSX.writeFile(wb, 'roteiro.xlsx');
    }
    </script>"""


