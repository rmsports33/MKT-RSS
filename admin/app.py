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

# --- Secrets: .env local → Streamlit Cloud Secrets (fix precedência) ---
def _get_secret(name: str, default: str = "") -> str:
    v = (os.getenv(name, "") or "").strip()
    if v:
        return v
    try:
        if hasattr(st, "secrets") and name in st.secrets:
            return str(st.secrets[name]).strip()
    except Exception:
        pass
    return default

WP_URL = _get_secret("WP_URL", "")
WP_USER = _get_secret("WP_USER", "")
WP_APP_PASSWORD = _get_secret("WP_APP_PASSWORD", "")
GROQ_KEY = _get_secret("GROQ_API_KEY", "")
GROQ_MODEL = _get_secret("GROQ_MODEL", "llama-3.3-70b-versatile")
TURSO_URL = _get_secret("TURSO_DATABASE_URL", "")
TURSO_TOKEN = _get_secret("TURSO_AUTH_TOKEN", "")

# FEEDS para param (hardening: não hardcode)
try:
    from mkt_flow_p0.rss_ingestor import FEEDS_PADRAO
except Exception:
    FEEDS_PADRAO = {"tecnoblog": "https://tecnoblog.net/feed/"}

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("WP", WP_URL or "não configurado")
with col2:
    st.metric("Groq", GROQ_MODEL if GROQ_KEY else "sem chave")
with col3:
    st.metric("Turso dedup", "nuvem" if (TURSO_URL and TURSO_TOKEN) else "local")
with col4:
    if st.button("Atualizar dashboard"):
        st.rerun()

# Alerta de secrets faltando
faltando = [k for k, v in [("WP_URL", WP_URL), ("WP_USER", WP_USER), ("WP_APP_PASSWORD", WP_APP_PASSWORD)] if not v]
if faltando:
    st.caption(f"⚠️ Secrets faltando: {', '.join(faltando)} — defina em .env ou Streamlit Secrets (Settings→Secrets).")
if not GROQ_KEY:
    st.caption("⚠️ GROQ_API_KEY ausente — dry-run funciona, reescrita real falhará (429).")

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

# Ações — feed param (hardening)
st.subheader("Ações")
opcoes_fonte = list(FEEDS_PADRAO.keys())
fonte_sel = st.selectbox("Fonte RSS", opcoes_fonte, index=0, help="Escolhe feed; evita hardcode tecnoblog")
feed_url = FEEDS_PADRAO.get(fonte_sel, "")
with st.expander("Feed custom / URL direta (opcional)", expanded=False):
    custom = st.text_input("URL feed custom (sobrescreve seleção)", placeholder="https://...")
    if custom.strip():
        feed_url = custom.strip()
        fonte_sel = "custom"
    url_direta = st.text_input("URL da matéria para virar rascunho (bypass feed)", placeholder="https://...")
    limite = st.slider("Itens por execução", 1, 5, 1)

col_a, col_b = st.columns(2)
with col_a:
    if st.button(f"Rodar pipeline RSS ({fonte_sel}, {limite} item, dry-run)"):
        if not feed_url and not url_direta.strip():
            st.warning("Informe feed ou URL direta.")
        else:
            with st.spinner("Extraindo e reescrevendo..."):
                try:
                    from mkt_flow_p0.rss_ingestor import buscar_novidades
                    from pipeline_rss import processar_item
                    # URL direta tem prioridade (sem dedup de feed)
                    if url_direta.strip():
                        r = processar_item({"titulo": "URL direta", "link": url_direta.strip(), "fonte": "manual", "resumo": ""}, dry_run=True)
                        st.json(r)
                    else:
                        nov = buscar_novidades(feed_url, fonte=fonte_sel, limit=limite)
                        if "erro" in nov:
                            st.error(nov["erro"])
                        elif nov.get("novos"):
                            for item in nov["novos"]:
                                r = processar_item(item, dry_run=True)
                                st.json(r)
                        else:
                            st.info(f"Nenhuma pauta nova em {fonte_sel} (dedup Turso/SQLite).")
                except Exception as e:
                    st.error(str(e))
                    st.exception(e)
with col_b:
    if st.button("Ver rascunhos no WP"):
        if WP_URL:
            st.link_button("Abrir rascunhos", f"{WP_URL.rstrip('/')}/wp-admin/edit.php?post_status=draft&post_type=post")
        else:
            st.warning("Configure WP_URL nos Secrets.")

st.caption("Dica: adicione esta página à tela inicial do celular — vira app.")
