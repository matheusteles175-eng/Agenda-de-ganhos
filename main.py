import streamlit as st
import pandas as pd
import os
from datetime import date, datetime

# --- CONFIGURAÇÕES ---
st.set_page_config(page_title="Driver Pro Mateus", page_icon="🚖", layout="centered")

# --- ARQUIVOS ---
user_path = st.session_state.get("usuario_atual", "matheus").lower()
arq_usuarios = "usuarios.csv"
arq_dados = f"dados_{user_path}.csv"
arq_carro = f"carro_{user_path}.csv"
arq_sonhos = f"sonhos_{user_path}.csv"
arq_dep_sonhos = f"dep_sonhos_{user_path}.csv"

# --- INICIALIZAÇÃO DE BANCO DE DADOS (CSV) ---
def inicializar():
    if not os.path.exists(arq_usuarios):
        pd.DataFrame([{"usuario": "matheus", "senha": "123"}]).to_csv(arq_usuarios, index=False)
    if not os.path.exists(arq_dados):
        pd.DataFrame(columns=["Data", "Ganho", "Gasto", "KM", "Inicio", "Fim"]).to_csv(arq_dados, index=False)
    if not os.path.exists(arq_carro):
        pd.DataFrame(columns=["Fipe", "KM_Atual", "KM_Oleo", "Ja_Guardado"]).to_csv(arq_carro, index=False)
    if not os.path.exists(arq_sonhos):
        pd.DataFrame(columns=["Item", "Valor_Meta", "Data_Alvo"]).to_csv(arq_sonhos, index=False)
    if not os.path.exists(arq_dep_sonhos):
        pd.DataFrame(columns=["Item", "Data", "Valor_Depositado"]).to_csv(arq_dep_sonhos, index=False)

inicializar()

# --- SISTEMA DE LOGIN ---
if "logado" not in st.session_state: st.session_state.logado = False

if not st.session_state.logado:
    st.markdown("<h1 style='text-align: center; color: #FFD700;'>🚖 Sistema Driver Pro</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["Entrar", "Criar Conta"])
    df_u = pd.read_csv(arq_usuarios, dtype=str)
    with t1:
        u = st.text_input("Usuário").strip().lower()
        s = st.text_input("Senha", type="password").strip()
        if st.button("Acessar Painel", use_container_width=True):
            if any((df_u['usuario'] == u) & (df_u['senha'] == s)):
                st.session_state.logado = True
                st.session_state.usuario_atual = u
                st.rerun()
            else: st.error("Erro no login.")
    st.stop()

# --- APP LOGADO ---
st.title(f"Painel de Gestão - {st.session_state.usuario_atual.capitalize()}")

# 1. MÓDULO IPVA & MANUTENÇÃO
st.header("⚙️ Meu Veículo & IPVA")
df_c = pd.read_csv(arq_carro)
if df_c.empty:
    with st.form("config_carro"):
        f = st.number_input("Valor FIPE", value=40000.0)
        k = st.number_input("KM Atual", value=100000.0)
        o = st.number_input("KM Próxima Troca Óleo", value=110000.0)
        if st.form_submit_button("Configurar Carro"):
            pd.DataFrame([{"Fipe": f, "KM_Atual": k, "KM_Oleo": o, "Ja_Guardado": 0.0}]).to_csv(arq_carro, index=False)
            st.rerun()
else:
    c = df_c.iloc[0]
    hoje = date.today()
    venc = date(hoje.year + (1 if hoje.month > 1 else 0), 1, 10)
    meses = max(1, (venc.year - hoje.year) * 12 + (venc.month - hoje.month))
    
    total_ipva = c['Fipe'] * 0.04
    col_ip1, col_ip2 = st.columns(2)
    guardado_ipva = col_ip1.number_input("Já guardei para IPVA (R$):", value=float(c['Ja_Guardado']))
    if col_ip2.button("Atualizar Fundo IPVA"):
        df_c.at[0, 'Ja_Guardado'] = guardado_ipva
        df_c.to_csv(arq_carro, index=False)
        st.rerun()

    parcela = (total_ipva - guardado_ipva) / meses
    st.info(f"📊 **Análise IPVA:** Falta R$ {total_ipva - guardado_ipva:.2f}. Guarde **R$ {parcela:.2f}/mês** até Janeiro ({meses} meses).")

# 2. GANHOS E HISTÓRICO (COM SOMA ACUMULADA)
st.divider()
st.header("💰 Ganhos Diários")
with st.container(border=True):
    c_g, c_p, c_km = st.columns(3)
    g = c_g.number_input("Ganho Bruto", value=None, placeholder="0.00")
    p = c_p.number_input("Gasto/Comb.", value=None, placeholder="0.00")
    km = c_km.number_input("KM Rodado", value=None, placeholder="0")
    if st.button("➕ SALVAR REGISTRO", use_container_width=True, type="primary"):
        if g is not None:
            nova = pd.DataFrame([{"Data": hoje.strftime("%d/%m/%Y"), "Ganho": g, "Gasto": p or 0, "KM": km or 0, "Inicio": "", "Fim": ""}])
            pd.concat([pd.read_csv(arq_dados), nova], ignore_index=True).to_csv(arq_dados, index=False)
            st.rerun()

df_d = pd.read_csv(arq_dados)
if not df_d.empty:
    lucro_total = df_d['Ganho'].sum() - df_d['Gasto'].sum()
    st.markdown(f"<div style='background-color:#28a745;padding:15px;border-radius:10px;text-align:center;color:white;'><h3>Lucro Total Acumulado: R$ {lucro_total:.2f}</h3></div>", unsafe_allow_html=True)
    
    with st.expander("📜 Ver Histórico Detalhado"):
        for i, r in df_d.iloc[::-1].iterrows():
            c1, c2, c3 = st.columns([1,2,1])
            c1.write(r['Data'])
            c2.write(f"Líquido: R$ {r['Ganho']-r['Gasto']:.2f} (Gasto: {r['Gasto']})")
            if c3.button("🗑️", key=f"del_{i}"):
                df_d.drop(i).to_csv(arq_dados, index=False)
                st.rerun()

# 3. CAIXINHAS DE SONHOS (INTERATIVO)
st.divider()
st.header("🎯 Caixinhas de Sonhos")
with st.expander("✨ Nova Caixinha"):
    with st.form("f_sonho"):
        n_s = st.text_input("Objetivo")
        v_s = st.number_input("Meta (R$)")
        if st.form_submit_button("Criar"):
            new_s = pd.DataFrame([{"Item": n_s, "Valor_Meta": v_s, "Data_Alvo": str(hoje)}])
            pd.concat([pd.read_csv(arq_sonhos), new_s], ignore_index=True).to_csv(arq_sonhos, index=False)
            st.rerun()

df_s = pd.read_csv(arq_sonhos)
df_dep = pd.read_csv(arq_dep_sonhos)

for i, s in df_s.iterrows():
    with st.container(border=True):
        ja = df_dep[df_dep['Item'] == s['Item']]['Valor_Depositado'].sum()
        progresso = min(ja / s['Valor_Meta'], 1.0)
        st.subheader(f"🚀 {s['Item']}")
        st.progress(progresso)
        st.write(f"Guardado: R$ {ja:.2f} de R$ {s['Valor_Meta']:.2f}")
        
        # Gráfico de evolução
        dep_sonho = df_dep[df_dep['Item'] == s['Item']]
        if not dep_sonho.empty:
            st.area_chart(dep_sonho.set_index('Data')['Valor_Depositado'].cumsum())

        val_dep = st.number_input("Depositar hoje:", key=f"in_{i}", value=None, placeholder="0.00")
        if st.button("📥 Guardar", key=f"bt_{i}"):
            if val_dep:
                n_dep = pd.DataFrame([{"Item": s['Item'], "Data": str(hoje), "Valor_Depositado": val_dep}])
                pd.concat([df_dep, n_dep], ignore_index=True).to_csv(arq_dep_sonhos, index=False)
                st.rerun()
