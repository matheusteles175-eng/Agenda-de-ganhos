import streamlit as st
import pandas as pd
import os
import hashlib
from datetime import date

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Driver Pro Mateus", layout="centered")

# Variável global para evitar o NameError
HOJE_ATUAL = date.today()

# --- FUNÇÃO DE CRIPTOGRAFIA SIMPLES ---
def hash_senha(senha):
    return hashlib.sha256(str.encode(senha)).hexdigest()

# --- BANCO DE DADOS (CSV) ---
user_id = st.session_state.get("usuario_atual", "default").lower()
arq_usuarios = "usuarios_v2.csv" # Versão nova para resetar erros
arq_dados = f"dados_{user_id}.csv"
arq_carro = f"carro_{user_id}.csv"
arq_sonhos = f"sonhos_{user_id}.csv"
arq_dep_sonhos = f"dep_sonhos_{user_id}.csv"

def carregar_safe(arquivo, colunas):
    if not os.path.exists(arquivo):
        df = pd.DataFrame(columns=colunas)
        df.to_csv(arquivo, index=False)
        return df
    df = pd.read_csv(arquivo)
    for col in colunas:
        if col not in df.columns: df[col] = 0.0
    return df

# --- TELA DE ACESSO (LOGIN E CADASTRO REAL) ---
if "logado" not in st.session_state: st.session_state.logado = False

if not st.session_state.logado:
    st.title("🚖 Driver Pro - Acesso")
    tab1, tab2 = st.tabs(["Entrar", "Criar Conta"])
    
    if not os.path.exists(arq_usuarios):
        pd.DataFrame(columns=["usuario", "senha"]).to_csv(arq_usuarios, index=False)
    
    df_u = pd.read_csv(arq_usuarios, dtype=str)

    with tab1:
        u = st.text_input("Usuário").lower().strip()
        s = st.text_input("Senha", type="password")
        if st.button("Login"):
            s_hash = hash_senha(s)
            if any((df_u['usuario'] == u) & (df_u['senha'] == s_hash)):
                st.session_state.logado = True
                st.session_state.usuario_atual = u
                st.rerun()
            else: st.error("Incorreto!")

    with tab2:
        nu = st.text_input("Novo Usuário").lower().strip()
        ns = st.text_input("Nova Senha", type="password")
        if st.button("Cadastrar"):
            if nu and ns:
                if nu in df_u['usuario'].values: st.error("Já existe!")
                else:
                    nova_u = pd.DataFrame([{"usuario": nu, "senha": hash_senha(ns)}])
                    pd.concat([df_u, nova_u]).to_csv(arq_usuarios, index=False)
                    st.success("Cadastrado! Vá em 'Entrar'.")
    st.stop()

# --- APP PRINCIPAL ---
st.title(f"Painel: {st.session_state.usuario_atual.upper()}")

# 1. IPVA
st.header("⚙️ Veículo e IPVA")
df_c = carregar_safe(arq_carro, ["Fipe", "KM_Atual", "KM_Oleo", "Ja_Guardado"])
if df_c.empty:
    with st.form("car"):
        f = st.number_input("Valor Fipe", 40000.0)
        if st.form_submit_button("Salvar"):
            pd.DataFrame([{"Fipe":f, "KM_Atual":100000, "KM_Oleo":110000, "Ja_Guardado":0.0}]).to_csv(arq_carro, index=False)
            st.rerun()
else:
    c = df_c.iloc[0]
    total_i = c['Fipe'] * 0.04
    col1, col2 = st.columns(2)
    guardado = col1.number_input("Já guardado:", value=float(c['Ja_Guardado']))
    if col2.button("Salvar Fundo"):
        df_c.at[0, 'Ja_Guardado'] = guardado
        df_c.to_csv(arq_carro, index=False)
        st.rerun()
    st.info(f"Falta R$ {total_i - guardado:.2f} para o IPVA.")

# 2. GANHOS
st.header("💰 Ganhos")
df_d = carregar_safe(arq_dados, ["Data", "Ganho", "Gasto"])
with st.form("ganhos"):
    g_h = st.number_input("Ganho de hoje")
    gas_h = st.number_input("Gasto de hoje")
    if st.form_submit_button("Salvar Ganho"):
        nova = pd.DataFrame([{"Data": HOJE_ATUAL.strftime("%d/%m"), "Ganho": g_h, "Gasto": gas_h}])
        pd.concat([df_d, nova]).to_csv(arq_dados, index=False)
        st.rerun()

# 3. CAIXINHAS
st.header("🎯 Caixinhas")
df_s = carregar_safe(arq_sonhos, ["Item", "Valor_Meta"])
df_dep = carregar_safe(arq_dep_sonhos, ["Item", "Data", "Valor_Depositado"])

with st.expander("Nova Meta"):
    with st.form("meta"):
        it = st.text_input("Objetivo")
        vm = st.number_input("Meta R$")
        if st.form_submit_button("Criar"):
            pd.concat([df_s, pd.DataFrame([{"Item":it, "Valor_Meta":vm}])]).to_csv(arq_sonhos, index=False)
            st.rerun()

for i, s in df_s.iterrows():
    ja_tem = df_dep[df_dep['Item'] == s['Item']]['Valor_Depositado'].sum()
    st.write(f"🚀 **{s['Item']}**: R$ {ja_tem} / R$ {s['Valor_Meta']}")
    v_add = st.number_input("Guardar quanto?", key=f"s_{i}")
    if st.button("Depositar", key=f"b_{i}"):
        n_dep = pd.DataFrame([{"Item": s['Item'], "Data": str(HOJE_ATUAL), "Valor_Depositado": v_add}])
        pd.concat([df_dep, n_dep]).to_csv(arq_dep_sonhos, index=False)
        st.rerun()
