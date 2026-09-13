import streamlit as st
import requests
st.set_page_config(page_title="MKT Flow", layout="wide")
st.title("🚀 MKT Flow 3.0")
st.markdown("Gerador de conteúdo com IA para marketing digital")

API_URL = "http://localhost:8000"

with st.form("form"):
    url = st.text_input("🔗 Link do Produto")
    nome = st.text_input("📦 Nome")
    preco = st.text_input("💰 Preço")
    tarefa = st.selectbox("📌 Tarefa", ["social", "article", "roi", "geo"])
    submitted = st.form_submit_button("⚡ Gerar")

if submitted and nome and preco:
    payload = {
        "user_input": f"Gere conteúdo para {tarefa}",
        "product_data": {"nome": nome, "preco": float(preco), "url": url or "", "programa": "mercado_livre"},
        "language": "pt"
    }
    with st.spinner("Gerando..."):
        try:
            r = requests.post(f"{API_URL}/generate", json=payload, timeout=60)
            if r.status_code == 200:
                result = r.json()
                st.success("✅ Conteúdo gerado!")
                st.markdown(result.get("content", "Nenhum conteúdo."))
            else:
                st.error(f"Erro: {r.text}")
        except Exception as e:
            st.error(f"Erro: {e}")