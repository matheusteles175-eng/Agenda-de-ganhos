import streamlit as st
import pandas as pd

st.title("📊 Gestor de Contas Simples")

# Inicializa a lista de contas se não existir
if 'contas' not in st.session_state:
    st.session_state.contas = []

# --- FORMULÁRIO DE ENTRADA ---
with st.form("nova_conta"):
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        nome = st.text_input("O que é? (Ex: Aluguel, Gás, Netflix)")
    with col2:
        valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
    with col3:
        data = st.date_input("Vencimento")
        
    submit = st.form_submit_button("Adicionar Conta")

if submit and nome:
    st.session_state.contas.append({"Nome": nome, "Valor": valor, "Data": data})
    st.success(f"Adicionado: {nome}")

# --- PROCESSAMENTO E EXIBIÇÃO ---
if st.session_state.contas:
    df = pd.DataFrame(st.session_state.contas)
    
    # Converter data para formato legível
    df['Data'] = pd.to_datetime(df['Data']).dt.strftime('%d/%m/%Y')

    st.subheader("📋 Suas Contas")
    st.table(df)

    # --- LÓGICA DE SOMA POR DATA ---
    st.subheader("🗓️ Resumo por Vencimento")
    
    # Agrupa por data e soma os valores
    resumo = df.groupby('Data')['Valor'].sum().reset_index()
    
    for index, row in resumo.iterrows():
        st.info(f"Você tem **R$ {row['Valor']:.2f}** em dívidas para o dia **{row['Data']}**")

    # Botão para limpar a lista
    if st.button("Limpar Tudo"):
        st.session_state.contas = []
        st.rerun()
else:
    st.write("Nenhuma conta adicionada ainda. Use o formulário acima!")
