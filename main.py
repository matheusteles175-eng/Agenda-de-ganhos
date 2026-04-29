import streamlit as st
import pandas as pd
import os
from datetime import date

# --- CONFIGURAÇÃO DE ARQUIVOS ---
user_path = st.session_state.get("usuario_atual", "matheus").lower()
arq_sonhos = f"sonhos_{user_path}.csv"
arq_depositos_sonhos = f"dep_sonhos_{user_path}.csv"

# Garantir que os arquivos existam
if not os.path.exists(arq_sonhos):
    pd.DataFrame(columns=["Item", "Valor_Meta", "Data_Alvo"]).to_csv(arq_sonhos, index=False)
if not os.path.exists(arq_depositos_sonhos):
    pd.DataFrame(columns=["Item", "Data", "Valor_Depositado"]).to_csv(arq_depositos_sonhos, index=False)

st.divider()
st.subheader("🎯 Suas Caixinhas de Objetivos")

# --- 1. CRIAR NOVO OBJETIVO ---
with st.expander("✨ Criar Novo Objetivo (Carro, Viagem, etc.)"):
    with st.form("novo_sonho"):
        nome_sonho = st.text_input("O que você quer conquistar?", placeholder="Ex: Meu Carro Novo")
        valor_meta = st.number_input("Qual o valor total? (R$)", value=None, placeholder="20000.00")
        data_alvo = st.date_input("Para quando é esse sonho?")
        if st.form_submit_button("Lançar Meta"):
            if nome_sonho and valor_meta:
                novo = pd.DataFrame([{"Item": nome_sonho, "Valor_Meta": valor_meta, "Data_Alvo": data_alvo}])
                pd.concat([pd.read_csv(arq_sonhos), novo], ignore_index=True).to_csv(arq_sonhos, index=False)
                st.rerun()

# --- 2. EXIBIR E INTERAGIR COM AS CAIXINHAS ---
df_s = pd.read_csv(arq_sonhos)
df_dep = pd.read_csv(arq_depositos_sonhos)

for i, sonho in df_s.iterrows():
    with st.container(border=True):
        # Cálculos da Caixinha
        nome = sonho['Item']
        meta = sonho['Valor_Meta']
        
        # Somar quanto já tem na caixinha (fictício/guardado)
        meus_depositos = df_dep[df_dep['Item'] == nome]
        ja_guardado = meus_depositos['Valor_Depositado'].sum()
        porcentagem = min(ja_guardado / meta, 1.0)
        falta = meta - ja_guardado

        st.markdown(f"### 🚀 {nome}")
        st.write(f"Meta: **R$ {meta:,.2f}** | Já guardado: <span style='color:green; font-weight:bold;'>R$ {ja_guardado:,.2f}</span>", unsafe_allow_html=True)
        
        # Barra de Progresso Visual
        st.progress(porcentagem)
        st.write(f"Faltam R$ {falta:,.2f} para o seu objetivo!")

        # --- GRÁFICO DE EVOLUÇÃO (A ONDINHA SUBINDO) ---
        if not meus_depositos.empty:
            # Criar a soma acumulada para o gráfico
            meus_depositos['Soma Acumulada'] = meus_depositos['Valor_Depositado'].cumsum()
            st.area_chart(meus_depositos.set_index('Data')['Soma Acumulada'], height=150)
        
        # --- INTERAÇÃO: DEPOSITAR NA CAIXINHA ---
        col_dep, col_msg = st.columns([1, 1.5])
        with col_dep:
            valor_hoje = st.number_input(f"Quanto guardou hoje?", value=None, placeholder="0.00", key=f"input_{i}")
            if st.button(f"📥 Guardar em {nome}", key=f"btn_{i}"):
                if valor_hoje:
                    novo_dep = pd.DataFrame([{"Item": nome, "Data": date.today(), "Valor_Depositado": valor_hoje}])
                    pd.concat([df_dep, novo_dep], ignore_index=True).to_csv(arq_depositos_sonhos, index=False)
                    st.success(f"R$ {valor_hoje} adicionados ao seu sonho!")
                    st.rerun()

        with col_msg:
            # MENSAGEM DE COACHING (DINÂMICA)
            if ja_guardado == 0:
                st.warning("O primeiro passo é o mais difícil! Coloque qualquer valor para começar a ver o gráfico subir.")
            elif porcentagem < 0.5:
                st.info(f"Boa, Mateus! Você já conquistou {porcentagem*100:.1f}% do seu sonho. Não para agora!")
            elif porcentagem >= 1.0:
                st.balloons()
                st.success("PARABÉNS! Você alcançou o seu objetivo! O esforço valeu a pena.")
            else:
                st.success("Você passou da metade! O topo está logo ali, mantenha o foco no seu objetivo!")

        # Opção de apagar a caixinha
        if st.button("🗑️ Excluir Meta", key=f"del_meta_{i}"):
            df_s.drop(i).to_csv(arq_sonhos, index=False)
            st.rerun()
