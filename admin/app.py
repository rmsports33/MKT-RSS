"""
admin/app.py — Painel multi-plataforma (Streamlit, grátis).

Roda local: streamlit run admin/app.py
Roda na nuvem: share.streamlit.io (conecta o repo, secrets em Settings).

Funciona no celular, tablet ou PC — sem precisar abrir wp-admin.
Mostra: RSS do dia, custo, rascunhos, botão para disparar pipeline_rss
e aprovar rascunho (via WP API). Sem custo extra, usa as mesmas chaves.
"""
import os
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except Exception:
    pass

st.set_page_config(page_title="ConexoTech — Admin", layout="wide")
st.title("ConexoTech — Admin (celular/PC)")

# Secrets: local .env ou Streamlit Cloud Secrets
WP_URL = os.getenv("WP_URL", "") or st.secrets.get("WP_URL", "") if hasattr(st, "secrets") else ""
GROQ_KEY = os.getenv("GROQ_API_KEY", "")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("WP", WP_URL or "não configurado")
with col2:
    st.metric("Groq", "ok" if GROQ_KEY else "sem chave")
with col3:
    if st.button("Atualizar dashboard"):
        st.rerun()

# Dashboard
try:
    from mkt_flow_p0.dashboard import coletar_dados
    dados = coletar_dados()
    st.subheader("Hoje")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("RSS total", dados.get("rss_total", 0))
    c2.metric("Publicados", dados.get("rss_publicados", 0))
    c3.metric("Bloqueados", dados.get("rss_bloqueados", 0))
    c4.metric("Custo LLM", f"${dados.get('cost_total', 0)}")
    st.write("Por plataforma:", dados.get("by_platform", {}))
    if dados.get("rss"):
        st.dataframe(dados["rss"][:10], use_container_width=True)
except Exception as e:
    st.warning(f"Dashboard indisponível: {e}")

st.divider()

# Ações
st.subheader("Ações")
url = st.text_input("URL da matéria para virar rascunho (opcional)", placeholder="https://...")
col_a, col_b = st.columns(2)
with col_a:
    if st.button("Rodar pipeline RSS (1 item, dry-run)"):
        with st.spinner("Extraindo e reescrevendo..."):
            try:
                from mkt_flow_p0.rss_ingestor import buscar_novidades
                from pipeline_rss import processar_item
                nov = buscar_novidades("https://tecnoblog.net/feed/", limit=1)
                if nov.get("novos"):
                    r = processar_item(nov["novos"][0], dry_run=True)
                    st.json(r)
                else:
                    st.info("Nenhuma pauta nova (dedup Turso).")
            except Exception as e:
                st.error(str(e))
with col_b:
    if st.button("Ver rascunhos no WP"):
        if WP_URL:
            st.link_button("Abrir rascunhos", f"{WP_URL.rstrip('/')}/wp-admin/edit.php?post_status=draft&post_type=post")
        else:
            st.warning("Configure WP_URL nos Secrets.")

st.caption("Dica: adicione esta página à tela inicial do celular — vira app.")
