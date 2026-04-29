import streamlit as st
import pandas as pd
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Controle de Gastos", layout="wide")

# Estilo personalizado (cores)
st.markdown("""
    <style>
    .main {
        background-color: #f5f7fa;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 10px;
        height: 3em;
        width: 100%;
    }
    .stNumberInput, .stTextInput {
        border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# Inicializa os dados
if "gastos" not in st.session_state:
    st.session_state.gastos = []

# Título
st.title("💸 Controle de Gastos Inteligente")
st.write("Registre e visualize seus gastos em tempo real")

# Layout em colunas
col1, col2 = st.columns(2)

with col1:
    categorias = [
        "🍔 Comida",
        "💡 Luz",
        "🚿 Água",
        "📱 Internet",
        "💳 Dívidas",
        "🚗 Transporte",
        "🛒 Mercado",
        "📦 Outros"
    ]

    categoria = st.selectbox("Categoria", categorias)
    valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
    descricao = st.text_input("Descrição")

    if st.button("➕ Adicionar"):
        if valor > 0:
            st.session_state.gastos.append({
                "Data": datetime.now(),
                "Categoria": categoria,
                "Valor": valor,
                "Descrição": descricao
            })
            st.success("Adicionado!")
        else:
            st.warning("Digite um valor válido")

with col2:
    if st.session_state.gastos:
        df = pd.DataFrame(st.session_state.gastos)

        total = df["Valor"].sum()
        st.metric("💰 Total gasto", f"R$ {total:.2f}")

        # Agrupamento por categoria
        por_categoria = df.groupby("Categoria")["Valor"].sum()

        st.subheader("📊 Gastos por categoria")
        st.bar_chart(por_categoria)

        st.subheader("📈 Evolução dos gastos")
        df_ordenado = df.sort_values("Data")
        st.line_chart(df_ordenado.set_index("Data")["Valor"])

# Tabela completa
st.subheader("📋 Histórico de Gastos")
if st.session_state.gastos:
    df = pd.DataFrame(st.session_state.gastos)
    st.dataframe(df, use_container_width=True)

    if st.button("🗑️ Limpar tudo"):
        st.session_state.gastos = []
        st.warning("Dados apagados!")
else:
    st.info("Nenhum gasto registrado ainda.")
