import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da página para ser leve e funcional
st.set_page_config(page_title="Cidade da Liberdade", layout="wide")

# --- ESTILIZAÇÃO LEVE ---
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

# --- SIMULAÇÃO DE BANCO DE DADOS (Pode ser trocado por SQLite depois) ---
if 'dividas' not in st.session_state:
    st.session_state.dividas = []
if 'pontos_cidade' not in st.session_state:
    st.session_state.pontos_cidade = 0

# --- TÍTULO ---
st.title("🏙️ Cidade da Liberdade Financeira")
st.write("Transforme suas dívidas em construções e recupere seu futuro.")

# --- BARRA LATERAL (MENU) ---
menu = st.sidebar.selectbox("Para onde vamos?", ["Minha Cidade", "Exterminador de Cartão", "Calculadora de Liberdade"])

# --- FUNÇÃO: MINHA CIDADE (O JOGO) ---
if menu == "Minha Cidade":
    st.header("Sua Evolução Visual")
    
    # Lógica do Balão/Peso (Sufoco)
    renda = st.number_input("Qual sua renda mensal real? (Sem contar limite)", value=1000.0)
    total_divida = sum(d['valor'] for d in st.session_state.dividas)
    percentual_uso = (total_divida / renda) if renda > 0 else 0
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        if percentual_uso > 0.9:
            st.error(f"💥 CUIDADO! Seu balão está explodindo! ({percentual_uso*100:.1f}%)")
            st.write("🔴 Você está sufocado pelas dívidas.")
        elif percentual_uso > 0.5:
            st.warning(f"🎈 O balão está ficando gordo... ({percentual_uso*100:.1f}%)")
        else:
            st.success(f"🟢 Balão sob controle! ({percentual_uso*100:.1f}%)")
            
    with col2:
        st.subheader("Sua Cidade Construída:")
        # Desenho simples da cidade usando Emojis (Super leve!)
        num_casas = int(st.session_state.pontos_cidade / 10)
        cidade_visual = "🌳" + ("🏠" * num_casas) + "🏙️" if num_casas > 5 else "🌳" + ("🏠" * num_casas)
        st.title(cidade_visual)
        st.info(f"Você tem {st.session_state.pontos_cidade} pontos de Liberdade. Cada dívida paga gera 10 pontos!")

# --- FUNÇÃO: EXTERMINADOR DE CARTÃO ---
elif menu == "Exterminador de Cartão":
    st.header("🛡️ Plano de Guerra contra o Cartão")
    
    with st.expander("➕ Registrar Dívida/Parcela"):
        nome = st.text_input("O que você comprou?")
        valor = st.number_input("Valor da Parcela (R$)", min_value=0.0)
        tipo = st.selectbox("Tipo", ["Cartão de Crédito", "Empréstimo", "Conta Fixa"])
        
        if st.button("Lançar no Sistema"):
            st.session_state.dividas.append({"nome": nome, "valor": valor, "tipo": tipo, "paga": False})
            st.success(f"Registrado: {nome}")

    st.subheader("Lista de Batalha")
    if st.session_state.dividas:
        df = pd.DataFrame(st.session_state.dividas)
        st.table(df)
        
        if st.button("Marcar última como PAGA ✅"):
            if st.session_state.dividas:
                st.session_state.dividas.pop() # Remove a dívida
                st.session_state.pontos_cidade += 10 # Ganha pontos no jogo
                st.balloons()
                st.rerun()
    else:
        st.write("Nenhuma dívida pendente! Sua cidade está em paz. 🕊️")

# --- FUNÇÃO: CALCULADORA DE LIBERDADE ---
elif menu == "Calculadora de Liberdade":
    st.header("⏱️ O Preço Real da Compra")
    st.write("Descubra quantos dias da sua vida você entrega para o banco.")
    
    valor_compra = st.number_input("Valor do produto no cartão (R$)", value=100.0)
    ganho_dia = st.number_input("Quanto você ganha limpo por dia? (R$)", value=50.0)
    
    dias = valor_compra / ganho_dia
    
    st.metric("Dias de Vida Entregues", f"{dias:.1f} Dias")
    
    if dias > 3:
        st.warning(f"Você vai trabalhar {dias:.1f} dias apenas para pagar isso. Vale sua energia?")
    else:
        st.success("Essa compra parece caber no seu esforço diário.")

    st.markdown("---")
    st.markdown("### 💡 Dica do Mestre:")
    st.info("Sempre que pensar em parcelar, lembre-se: O banco está comprando o seu tempo de trabalho do futuro.")

