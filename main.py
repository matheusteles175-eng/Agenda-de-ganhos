import streamlit as st
import pandas as pd
import json
import os
import hashlib
import re
from datetime import datetime, date, timedelta

# --- CONFIGURAÇÕES VISUAIS PARA CELULAR ---
st.set_page_config(page_title="Renda Organizada", page_icon="💰", layout="centered")

# CSS para deixar os botões grandes e fáceis de tocar no celular
st.markdown("""
    <style>
    .stButton button {
        width: 100%;
        height: 3em;
        font-weight: bold;
    }
    div[data-baseweb="tab-list"] {
        display: flex;
        justify-content: center;
    }
    div[data-baseweb="tab"] {
        padding: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

PASTA = "data"
if not os.path.exists(PASTA): os.makedirs(PASTA)

USERS_FILE = os.path.join(PASTA, "users.json")
CALC_HIST_FILE = os.path.join(PASTA, "calc_hist.json")
NOTAS_FILE = os.path.join(PASTA, "notas.json")

def hash_senha(s): return hashlib.sha256(s.encode()).hexdigest()
def salvar(arq, dados):
    with open(arq, "w") as f: json.dump(dados, f)
def carregar(arq, default):
    if os.path.exists(arq):
        try:
            with open(arq, "r") as f: return json.load(f)
        except: return default
    return default

if 'logado' not in st.session_state: st.session_state.logado = False
if 'user' not in st.session_state: st.session_state.user = None

# --- TELA DE LOGIN ---
if not st.session_state.logado:
    st.title("📱 Renda Organizada")
    tab_log, tab_reg = st.tabs(["ENTRAR", "CADASTRAR"])
    with tab_log:
        u = st.text_input("Usuário")
        s = st.text_input("Senha", type="password")
        if st.button("ACESSAR APP"):
            users = carregar(USERS_FILE, {})
            if u in users and users[u] == hash_senha(s):
                st.session_state.logado = True
                st.session_state.user = u
                st.rerun()
            else: st.error("Login inválido")
    with tab_reg:
        u_c = st.text_input("Novo Usuário")
        s_c = st.text_input("Nova Senha", type="password")
        if st.button("CRIAR CONTA"):
            if u_c and s_c:
                users = carregar(USERS_FILE, {})
                users[u_c] = hash_senha(s_c)
                salvar(USERS_FILE, users)
                st.success("Pronto! Agora faça login.")

# --- INTERFACE COM NAVEGAÇÃO POR ABAS (MELHOR PARA CELULAR) ---
else:
    user = st.session_state.user
    file_user = os.path.join(PASTA, f"dados_{user}.json")
    dados_user = carregar(file_user, {})

    # No celular, as abas ficam no topo. É só clicar para mudar de "tela"
    t_ganhos, t_calc, t_notas, t_hist = st.tabs(["📊 Ganhos", "🧮 Calc", "📝 Notas", "📜 Hist"])

    # --- TELA GANHOS ---
    with t_ganhos:
        st.subheader("Registro de hoje")
        meta = st.number_input("Meta Líquida (R$)", value=0.0)
        c1, c2 = st.columns(2)
        ini = c1.text_input("Início", "08:00")
        fim = c2.text_input("Fim", "18:00")
        bruto = st.number_input("Valor Bruto (R$)", min_value=0.0)
        gastos = st.number_input("Gastos (R$)", min_value=0.0)
        km = st.number_input("KM Rodados", min_value=1.0)

        if st.button("CALCULAR E SALVAR"):
            try:
                t1, t2 = datetime.strptime(ini, "%H:%M"), datetime.strptime(fim, "%H:%M")
                if t2 < t1: t2 += timedelta(days=1)
                horas = (t2 - t1).total_seconds() / 3600
                liq = bruto - gastos
                dif = liq - meta
                
                if dif >= 0: st.success(f"Meta Batida! + R$ {dif:.2f}")
                else: st.error(f"Faltou R$ {abs(dif):.2f}")
                
                dados_user[str(date.today())] = {
                    "liquido": liq, "bruto": bruto, "gastos": gastos, "meta": meta,
                    "km": km, "hora_bruta": bruto/horas if horas>0 else 0,
                    "km_bruto": bruto/km, "horas_trab": horas, "dif": dif
                }
                salvar(file_user, dados_user)
            except Exception as e: st.error(f"Erro: {e}")

    # --- TELA CALCULADORA ---
    with t_calc:
        st.subheader("Soma Rápida")
        txt_calc = st.text_area("Valores (ex: 12.50 30 15,40):")
        nums = re.findall(r'\d+[.,]?\d*', txt_calc)
        total = sum(float(n.replace(",", ".")) for n in nums)
        st.info(f"TOTAL: R$ {total:.2f}")
        
        if st.button("Salvar na Lista"):
            h = carregar(CALC_HIST_FILE, [])
            h.append({"id": datetime.now().timestamp(), "val": f"R$ {total:.2f}", "data": datetime.now().strftime("%H:%M")})
            salvar(CALC_HIST_FILE, h)
            st.rerun()

    # --- TELA NOTAS ---
    with t_notas:
        st.subheader("Anotações")
        txt_n = st.text_area("Escreva aqui...")
        if st.button("Salvar Mensagem"):
            n = carregar(NOTAS_FILE, [])
            n.append({"id": datetime.now().timestamp(), "data": datetime.now().strftime("%d/%m"), "txt": txt_n})
            salvar(NOTAS_FILE, n)
            st.rerun()
        
        for nt in reversed(carregar(NOTAS_FILE, [])):
            with st.expander(f"Nota {nt['data']}"):
                st.write(nt['txt'])

    # --- TELA HISTÓRICO ---
    with t_hist:
        st.subheader("Meus Resultados")
        for dia, d in sorted(dados_user.items(), reverse=True):
            with st.container(border=True):
                st.write(f"**{dia}** - Líquido: R$ {d['liquido']:.2f}")
                if st.button(f"Apagar {dia}", key=f"del_{dia}"):
                    del dados_user[dia]
                    salvar(file_user, dados_user)
                    st.rerun()

    # Botão de Sair no final de tudo
    st.divider()
    if st.button("SAIR DO USUÁRIO"):
        st.session_state.logado = False
        st.rerun()
