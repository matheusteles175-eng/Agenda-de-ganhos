import streamlit as st
import pandas as pd
import os
from datetime import date

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Driver Pro Mateus", page_icon="🚖", layout="centered")

# --- ARQUIVOS ---
user_id = st.session_state.get("usuario_atual", "default").lower()
arq_usuarios = "usuarios.csv"
arq_dados = f"dados_{user_id}.csv"
arq_carro = f"carro_{user_id}.csv"
arq_sonhos = f"sonhos_{user_id}.csv"
arq_dep_sonhos = f"dep_sonhos_{user_id}.csv"

# --- FUNÇÃO PARA CARREGAR CSV SEM ERRO DE COLUNA ---
def carregar_safe(arquivo, colunas_obrigatorias):
    if not os.path.exists(arquivo):
        df = pd.DataFrame(columns=colunas_obrigatorias)
        df.to_csv(arquivo, index=False)
        return df
    df = pd.read_csv(arquivo)
    for col in colunas_obrigatorias:
        if col not in df.columns:
            df[col] = 0.0 if col != "Item" and col != "Data" else ""
    return df

# --- LOGIN ---
if "logado" not in st.session_state: st.session_state.logado = False

if not st.session_state.logado:
    st.markdown("<h1 style='text-align: center;'>🚖 Login Driver Pro</h1>", unsafe_allow_html=True)
    u = st.text_input("Usuário").strip().lower()
    s = st.text_input("Senha", type="password").strip()
    if st.button("Entrar", use_container_width=True):
        if u == "matheus" and s == "123": # Login simples para teste
            st.session_state.logado = True
            st.session_state.usuario_atual = u
            st.rerun()
        else: st.error("Acesso negado.")
    st.stop()

# --- APP PRINCIPAL ---
st.title(f"Painel do {st.session_state.usuario_atual.capitalize()}")

# 1. IPVA COM EXPLICAÇÃO
st.header("⚙️ Veículo & IPVA")
df_c = carregar_safe(arq_carro, ["Fipe", "KM_Atual", "KM_Oleo", "Ja_Guardado"])

if df_c.empty:
    with st.form("set_car"):
        f = st.number_input("Valor FIPE", value=45000.0)
        k = st.number_input("KM Atual", value=100000.0)
        if st.form_submit_button("Salvar Carro"):
            pd.DataFrame([{"Fipe": f, "KM_Atual": k, "KM_Oleo": k+10000, "Ja_Guardado": 0.0}]).to_csv(arq_carro, index=False)
            st.rerun()
else:
    c = df_c.iloc[0]
    fipe_val = c['Fipe']
    total_ipva = fipe_val * 0.04
    
    # Cálculo de meses
    hoje = date.today()
    meses = max(1, (13 - hoje.month)) 
    
    col_i1, col_i2 = st.columns(2)
    guardado = col_i1.number_input("Quanto já tem guardado?", value=float(c['Ja_Guardado']))
    if col_i2.button("Atualizar Fundo"):
        df_c.at[0, 'Ja_Guardado'] = guardado
        df_c.to_csv(arq_carro, index=False)
        st.success("Valor atualizado!")

    falta = total_ipva - guardado
    st.info(f"O IPVA total é R$ {total_ipva:.2f}. Tirando o que você já tem, faltam **R$ {falta:.2f}**. Você deve guardar **R$ {falta/meses:.2f}** por mês até Janeiro.")

# 2. GANHOS (HISTÓRICO ACUMULADO)
st.divider()
st.header("💰 Ganhos")
df_d = carregar_safe(arq_dados, ["Data", "Ganho", "Gasto", "KM"])

with st.form("add_ganho", clear_on_submit=True):
    c_g, c_p = st.columns(2)
    v_g = c_g.number_input("Ganho de hoje", value=0.0)
    v_p = c_p.number_input("Gasto de hoje", value=0.0)
    if st.form_submit_button("Salvar"):
        nova = pd.DataFrame([{"Data": hoje.strftime("%d/%m"), "Ganho": v_g, "Gasto": v_p, "KM": 0}])
        pd.concat([df_d, nova], ignore_index=True).to_csv(arq_dados, index=False)
        st.rerun()

if not df_d.empty:
    lucro = df_d['Ganho'].sum() - df_d['Gasto'].sum()
    st.success(f"### Lucro Total Acumulado: R$ {lucro:.2f}")

# 3. CAIXINHAS (OBJETIVOS)
st.divider()
st.header("🎯 Caixinhas")
df_s = carregar_safe(arq_sonhos, ["Item", "Valor_Meta"])
df_dep = carregar_safe(arq_dep_sonhos, ["Item", "Data", "Valor_Depositado"])

with st.expander("Criar Nova Caixinha"):
    with st.form("new_s"):
        nome = st.text_input("Nome do Sonho")
        meta = st.number_input("Valor Alvo")
        if st.form_submit_button("Criar"):
            pd.concat([df_s, pd.DataFrame([{"Item": nome, "Valor_Meta": meta}])], ignore_index=True).to_csv(arq_sonhos, index=False)
            st.rerun()

for i, s in df_s.iterrows():
    with st.container(border=True):
        ja_tem = df_dep[df_dep['Item'] == s['Item']]['Valor_Depositado'].sum()
        st.subheader(f"🚀 {s['Item']}")
        st.write(f"Guardado: R$ {ja_tem:.2f} / Meta: R$ {s['Valor_Meta']:.2f}")
        st.progress(min(ja_tem / s['Valor_Meta'], 1.0) if s['Valor_Meta'] > 0 else 0.0)
        
        v_dep = st.number_input("Quanto vai guardar agora?", key=f"d_{i}", value=0.0)
        if st.button("Depositar", key=f"b_{i}"):
            novo_dep = pd.DataFrame([{"Item": s['Item'], "Data": str(hoje), "Valor_Depositado": v_dep}])
            pd.concat([df_dep, novo_dep], ignore_index=True).to_csv(arq_dep_sonhos, index=False)
            st.rerun()
