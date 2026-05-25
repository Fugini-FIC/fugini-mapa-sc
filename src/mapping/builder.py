# ============================================================
# src/mapping/builder.py
# Gera o mapa Folium para São Carlos e Região.
# Área única — sem K-Means, sem múltiplas áreas.
# ============================================================

import logging
import pandas as pd
import folium
import folium.plugins
from pathlib import Path

from config.settings import USUARIOS_MAPA, COR_AREA, NOME_REGIAO
from src.mapping.crypto      import criptografar_html
from src.mapping.roteamento  import gerar_roteamento_html

logger = logging.getLogger(__name__)

OUTPUT_DIR = Path("data/output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _safe_str(val, default="-") -> str:
    if val is None:
        return default
    try:
        if pd.isna(val):
            return default
    except (TypeError, ValueError):
        pass
    s = str(val).strip()
    return default if s.lower() in ("nan", "none", "nat", "") else s


def _safe_float(val, default=0.0) -> float:
    if val is None:
        return default
    try:
        if pd.isna(val):
            return default
        return float(val)
    except (TypeError, ValueError):
        return default


def _safe_date(val, default="-") -> str:
    if val is None:
        return default
    try:
        if pd.isna(val):
            return default
        return pd.Timestamp(val).strftime("%d/%m/%Y")
    except (TypeError, ValueError):
        return default


def montar_mapa(df: pd.DataFrame, df_prospects: pd.DataFrame | None = None) -> folium.Map:
    """Monta mapa Folium com marcadores de clientes e prospects."""

    # Centro na região de São Carlos
    mapa = folium.Map(
        location=[-21.994, -47.890],
        zoom_start=10,
        tiles="CartoDB positron",
    )

    # CSS global
    mapa.get_root().html.add_child(folium.Element(
        """<style>
        .leaflet-overlay-pane { pointer-events: none !important; }
        .leaflet-control-layers { display: none !important; }
        .leaflet-top.leaflet-left { right: 10px !important; left: auto !important; }
        </style>"""
    ))

    # Marcadores de clientes
    fg_clientes = folium.FeatureGroup(name="Clientes", show=True)
    for _, row in df.iterrows():
        if not pd.notna(row.get("lat_final")) or not pd.notna(row.get("lng_final")):
            continue

        nome    = _safe_str(row.get("nome_cliente"), "N/D")
        cod     = _safe_str(row.get("cod_cliente"),  "N/D")
        cidade  = _safe_str(row.get("nome_municipio"), "N/D")
        credito = _safe_float(row.get("limite_disp"))
        ult_nf  = _safe_date(row.get("ultima_compra"))
        fat     = _safe_float(row.get("total_faturado"))
        fat_fmt = f"R$ {fat:,.2f}" if fat > 0 else "-"

        popup_html = f"""
        <div style="font-family:Arial;font-size:12px;min-width:180px">
            <b>{nome}</b><br>
            <span style="color:#666">Cód: {cod}</span><br>
            <span style="color:#666">{cidade}</span><br>
            <span style="color:#666">Crédito disp.: R$ {credito:,.2f}</span><br>
            <span style="color:#666">Última NF: {ult_nf}</span><br>
            <span style="color:#666">Faturamento total: {fat_fmt}</span>
        </div>
        """
        folium.CircleMarker(
            location=[float(row["lat_final"]), float(row["lng_final"])],
            radius=6,
            color=COR_AREA["marker"],
            fill=True,
            fill_color=COR_AREA["fill"],
            fill_opacity=0.85,
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=folium.Tooltip(nome),
        ).add_to(fg_clientes)

    fg_clientes.add_to(mapa)

    # Heatmap de crédito disponível
    fg_heat = folium.FeatureGroup(name="Heatmap Crédito", show=False)
    heat_data = [
        [float(row["lat_final"]), float(row["lng_final"]), float(row["limite_disp"])]
        for _, row in df.iterrows()
        if pd.notna(row.get("lat_final")) and pd.notna(row.get("lng_final"))
        and pd.notna(row.get("limite_disp")) and float(row.get("limite_disp", 0)) > 0
        and row.get("geo_valida_final", True)
    ]
    if heat_data:
        folium.plugins.HeatMap(heat_data, min_opacity=0.3, radius=20, blur=15).add_to(fg_heat)
    fg_heat.add_to(mapa)

    # Prospects por CNAE
    if df_prospects is not None and not df_prospects.empty:
        for cnae in sorted(df_prospects["cnae"].dropna().unique()):
            df_cnae   = df_prospects[df_prospects["cnae"] == cnae]
            descricao = df_cnae["descricao_cnae"].iloc[0] if not df_cnae.empty else cnae
            fg_p      = folium.FeatureGroup(name=f"Prospect: {descricao}", show=False)

            for _, row in df_cnae.iterrows():
                nome  = _safe_str(row.get("razao_social") or row.get("nome_fantasia"), "N/D")
                cnpj  = _safe_str(row.get("cnpj"), "N/D")
                ende  = f"{_safe_str(row.get('logradouro'))} {_safe_str(row.get('numero'))}".strip()
                bairro = _safe_str(row.get("bairro"))
                cidade = _safe_str(row.get("municipio"))

                popup_html = f"""
                <div style="font-family:Arial;font-size:12px;min-width:180px">
                    <b>{nome}</b><br>
                    <span style="color:#888;font-size:10px">PROSPECT</span><br>
                    <span style="color:#666">CNPJ: {cnpj}</span><br>
                    <span style="color:#666">CNAE: {descricao}</span><br>
                    <span style="color:#666">{ende}</span><br>
                    <span style="color:#666">{bairro} — {cidade}</span>
                </div>
                """
                folium.CircleMarker(
                    location=[float(row["lat_final"]), float(row["lng_final"])],
                    radius=4,
                    color="#888888",
                    fill=True,
                    fill_color="#aaaaaa",
                    fill_opacity=0.5,
                    popup=folium.Popup(popup_html, max_width=250),
                    tooltip=folium.Tooltip(f"{nome} — {descricao}"),
                ).add_to(fg_p)

            fg_p.add_to(mapa)

    # Prospects por CNAE — checkboxes no painel
    n_clientes = int(df["geo_valida_final"].sum()) if "geo_valida_final" in df.columns else len(df)
    soma_cred  = df[df.get("geo_valida_final", pd.Series([True]*len(df)))]["limite_disp"].fillna(0).sum()
    cred_fmt   = f"R$ {soma_cred/1_000:.0f}K" if soma_cred >= 1_000 else f"R$ {soma_cred:,.0f}"

    prospects_html = ""
    if df_prospects is not None and not df_prospects.empty:
        cnaes = (
            df_prospects.groupby(["cnae", "descricao_cnae"])
            .size().reset_index(name="n")
            .sort_values("n", ascending=False)
        )
        linhas_cnae = ""
        for _, row in cnaes.iterrows():
            layer_name = f"Prospect: {row['descricao_cnae']}"
            linhas_cnae += f"""
          <label style="display:flex;align-items:center;cursor:pointer;gap:6px;margin-bottom:4px;">
            <input type="checkbox"
                   onchange="toggleLayer('{layer_name}', this.checked)"
                   style="width:13px;height:13px;cursor:pointer;accent-color:#888;">
            <span style="display:inline-block;width:9px;height:9px;border-radius:50%;
                         background:#aaa;flex-shrink:0;"></span>
            <span style="font-size:10px;color:#555;">{row['descricao_cnae']} ({row['n']})</span>
          </label>"""

        prospects_html = f"""
        <div style="border-top:1px solid #eee;margin-top:8px;padding-top:8px;">
          <div style="font-size:11px;font-weight:700;color:#888;margin-bottom:6px;">
            🎯 PROSPECÇÃO ({len(df_prospects):,})
          </div>
          {linhas_cnae}
        </div>"""

    painel_html = f"""
    <div id="painel-resumo" style="
        position: fixed; top: 10px; left: 10px; z-index: 1000;
        background: rgba(255,255,255,0.97); border-radius: 10px;
        padding: 14px 16px; box-shadow: 0 2px 12px rgba(0,0,0,0.15);
        min-width: 200px; max-width: 240px;
        font-family: 'Segoe UI', Arial, sans-serif;
        border-left: 4px solid #e74c3c;
        max-height: 90vh; overflow-y: auto;
    ">
      <div style="font-size:12px;font-weight:700;color:#e74c3c;margin-bottom:10px;">
        📊 {NOME_REGIAO.upper()}
      </div>
      <label style="display:flex;align-items:center;cursor:pointer;gap:6px;margin-bottom:8px;">
        <input type="checkbox" checked
               onchange="toggleLayer('Clientes', this.checked)"
               style="width:14px;height:14px;cursor:pointer;accent-color:#e74c3c;">
        <span style="display:inline-block;width:10px;height:10px;border-radius:50%;
                     background:#e74c3c;flex-shrink:0;"></span>
        <span style="font-weight:700;font-size:12px;color:#1a1a2e;">Clientes</span>
      </label>
      <div style="padding-left:34px;font-size:11px;color:#555;line-height:1.7;margin-bottom:8px;">
        <div>👥 {n_clientes} clientes disponíveis</div>
        <div>💳 {cred_fmt} crédito disponível</div>
      </div>
      <div style="padding-left:0;margin-bottom:8px;">
        <label style="display:flex;align-items:center;cursor:pointer;gap:6px;">
          <input type="checkbox"
                 onchange="toggleLayer('Heatmap Crédito', this.checked)"
                 style="width:13px;height:13px;cursor:pointer;">
          <span style="font-size:11px;color:#555;">🔥 Heatmap Crédito</span>
        </label>
      </div>
      {prospects_html}
    </div>
    <script>
    function toggleLayer(layerName, visible) {{
      var labels = document.querySelectorAll('.leaflet-control-layers-overlays label');
      labels.forEach(function(label) {{
        if (label.textContent.trim() === layerName) {{
          var checkbox = label.querySelector('input');
          if (checkbox && checkbox.checked !== visible) checkbox.click();
        }}
      }});
    }}
    </script>"""
    mapa.get_root().html.add_child(folium.Element(painel_html))

    folium.LayerControl(collapsed=False).add_to(mapa)

    # Painel de roteamento
    mapa.get_root().html.add_child(
        folium.Element(gerar_roteamento_html(df))
    )

    return mapa


def _salvar_html(mapa: folium.Map, path_raw: Path, path_out: Path, senha: str | None, criptografar: bool):
    mapa.save(str(path_raw))
    if criptografar and senha:
        criptografar_html(path_raw, path_out, senha)
        logger.info(f"  Criptografado: {path_out.name}")
        path_raw.unlink()
    else:
        if path_out.exists():
            path_out.unlink()
        path_raw.rename(path_out)


def exportar_mapas(df: pd.DataFrame, criptografar: bool = True, df_prospects: pd.DataFrame | None = None) -> dict:
    """Gera e salva os HTMLs em data/output/."""
    arquivos = {}

    for usuario, dados in USUARIOS_MAPA.items():
        arquivo = dados["arquivo"]
        senha   = dados["senha"]
        slug    = arquivo.replace(".html", "")

        logger.info(f"Gerando {arquivo}...")
        mapa = montar_mapa(df, df_prospects=df_prospects)
        _salvar_html(
            mapa,
            OUTPUT_DIR / f"_{slug}_raw.html",
            OUTPUT_DIR / arquivo,
            senha,
            criptografar,
        )
        arquivos[usuario] = OUTPUT_DIR / arquivo
        logger.info(f"✅ {arquivo}")

    logger.info(f"\n📁 HTMLs em: {OUTPUT_DIR.resolve()}")
    return arquivos