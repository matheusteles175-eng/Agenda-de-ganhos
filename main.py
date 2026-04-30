import streamlit as st
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Cidade da Liberdade", layout="wide")

# Inicializando os dados se não existirem
if 'dividas' not in st.session_state:
    st.session_state.dividas = []
if 'pontos_cidade' not in st.session_state:
    st.session_state.pontos_cidade = 0

# --- ESTILO ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 20px; height: 3em; background-color: #2e7d32; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- TÍTULO ---
st.title("🏙️ Cidade da Liberdade Financeira")

# --- MENU LATERAL ---
menu = st.sidebar.radio("Navegação", ["Minha Cidade", "Exterminador de Dívidas", "Calculadora de Tempo"])

if menu == "Minha Cidade":
    st.header("Status do seu Reino")
    
    renda = st.number_input("Sua Renda Mensal (R$)", value=1000.0)
    total_divida = sum(d['valor'] for d in st.session_state.dividas)
    
    # Lógica Visual do Balão/Sufoco
    percentual = (total_divida / renda) if renda > 0 else 0
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Estado do Balão 🎈")
        if percentual > 0.9:
            st.error(f"⚠️ EXPLODINDO! ({percentual*100:.0f}%)")
            st.write("Seu balão financeiro está prestes a estourar. Pare de gastar agora!")
        elif percentual > 0.5:
            st.warning(f"🟡 Pesado... ({percentual*100:.0f}%)")
            st.write("O balão está murchando. Hora de cortar o cartão.")
        else:
            st.success(f"🟢 Leve! ({percentual*100:.0f}%)")
            st.write("Caminho livre para crescer.")

    with col2:
        st.subheader("Sua Cidade")
        # Evolução da cidade baseada em pontos (cada dívida paga = 10 pontos)
        casas = int(st.session_state.pontos_cidade / 10)
        desenho = "🌳" + ("🏠" * casas) + "🏢" if casas > 3 else "🌳" + ("🏠" * casas)
        st.title(desenho)
        st.info(f"Pontos de Conquista: {st.session_state.pontos_cidade}")

elif menu == "Exterminador de Dívidas":
    st.header("⚔️ Combate ao Cartão")
    
    with st.form("nova_divida", clear_on_submit=True):
        nome = st.text_input("Descrição da Dívida (ex: Cartão de Crédito)")
        valor = st.number_input("Valor da Parcela (R$)", min_value=0.0)
        enviar = st.form_submit_button("Lançar no Mapa")
        
        if enviar and nome:
            st.session_state.dividas.append({"nome": nome, "valor": valor})
            st.success("Inimigo detectado! Vamos pagar isso.")
            st.rerun()

    st.subheader("Dívidas Ativas")
    if st.session_state.dividas:
        df = pd.DataFrame(st.session_state.dividas)
        st.table(df)
        
        if st.button("Paguei uma Parcela! ✅"):
            st.session_state.dividas.pop(0) # Remove a primeira da lista
            st.session_state.pontos_cidade += 10 # Evolui a cidade
            st.balloons()
            st.rerun()
    else:
        st.write("Cidade limpa! Nenhuma dívida pendente.")

elif menu == "Calculadora de Tempo":
    st.header("⏱️ Quanto custa em esforço?")
    valor_item = st.number_input("Preço do que você quer comprar (R$)", value=100.0)
    ganho_dia = st.number_input("Quanto você ganha por dia trabalhado? (R$)", value=50.0)
    
    if ganho_dia > 0:
        dias = valor_item / ganho_dia
        st.metric("Dias de Trabalho", f"{dias:.1f} dias")
        
        if dias > 5:
            st.error("Isso vai custar muito da sua vida. Pense bem!")
        else:
            st.info("Compra razoável. Mas prefira pagar à vista!")

