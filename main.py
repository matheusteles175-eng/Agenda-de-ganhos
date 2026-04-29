import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime, timedelta

# Configuração da página - DEVE SER A PRIMEIRA COISA
st.set_page_config(page_title="Driver Pro", layout="wide")

# ================= CONEXÃO COM BANCO =================
def init_db():
    conn = sqlite3.connect("driver_pro.db", check_same_thread=False)
    cursor = conn.cursor()
    # Tabela de Usuários
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            usuario TEXT PRIMARY KEY, 
            senha TEXT
        )
    """)
    # Tabela de Ganhos (com ID único para deletar)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ganhos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT, data TEXT, ganho REAL, gasto REAL, km REAL, 
            inicio TEXT, fim TEXT
        )
    """)
    # Tabela de Metas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS metas (
            usuario TEXT PRIMARY KEY, 
            km_alvo REAL, hora_alvo REAL, lucro_alvo REAL
        )
    """)
    conn.commit()
    return conn

conn = init_db()
cursor = conn.cursor()

# ================= SISTEMA DE LOGIN =================
if "usuario" not in st.session_state:
    st.session_state.usuario = None

if st.session_state.usuario is None:
    st.title("🔐 Driver Pro - Acesso")
    tab_login, tab_cad = st.tabs(["Login", "Criar Conta"])
    
    with tab_login:
        u = st.text_input("Usuário").lower().strip()
        s = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            user_db = cursor.execute("SELECT * FROM usuarios WHERE usuario=? AND senha=?", (u, s)).fetchone()
            if user_db:
                st.session_state.usuario = u
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos")
    
    with tab_cad:
        nu = st.text_input("Novo Usuário").lower().strip()
        ns = st.text_input("Nova Senha", type="password")
        if st.button("Cadastrar"):
            try:
                cursor.execute("INSERT INTO usuarios VALUES (?,?)", (nu, ns))
                conn.commit()
                st.success("Conta criada com sucesso! Vá para a aba Login.")
            except:
                st.error("Este nome de usuário já existe.")
    st.stop()

# ================= LOGADO - VARIÁVEIS =================
user = st.session_state.usuario

# Função para calcular horas trabalhadas
def calcular_horas(inicio, fim):
    try:
        t1 = datetime.strptime(inicio, "%H:%M")
        t2 = datetime.strptime(fim, "%H:%M")
        diff = t2 - t1
        return diff.total_seconds() / 3600
    except:
        return 0

# ================= LAYOUT PRINCIPAL =================
st.sidebar.title(f"Olá, {user.capitalize()}")
if st.sidebar.button("Sair"):
    st.session_state.usuario = None
    st.rerun()

# --- BUSCAR METAS DO USUÁRIO ---
meta_data = cursor.execute("SELECT * FROM metas WHERE usuario=?", (user,)).fetchone()
if not meta_data:
    m_km, m_hr, m_lucro = 2.0, 30.0, 150.0
else:
    _, m_km, m_hr, m_lucro = meta_data

st.sidebar.subheader("🎯 Suas Metas")
new_km = st.sidebar.number_input("Meta R$/KM", value=float(m_km))
new_hr = st.sidebar.number_input("Meta R$/Hora", value=float(m_hr))
new_lc = st.sidebar.number_input("Meta Lucro Dia", value=float(m_lucro))

if st.sidebar.button("Atualizar Metas"):
    cursor.execute("INSERT OR REPLACE INTO metas VALUES (?,?,?,?)", (user, new_km, new_hr, new_lc))
    conn.commit()
    st.rerun()

# ================= PAINEL DE CONTROLE =================
st.header("🚖 Controle de Ganhos e Médias")

aba1, aba2 = st.tabs(["📊 Dashboard Diário", "📜 Histórico e Exclusão"])

with aba1:
    col_form, col_metric = st.columns([1, 2])
    
    with col_form:
        st.subheader("Lançamento")
        with st.form("corrida"):
            d = st.date_input("Data", date.today())
            v_g = st.number_input("Ganho Total (R$)", min_value=0.0)
            v_c = st.number_input("Combustível/Gasto (R$)", min_value=0.0)
            v_k = st.number_input("KM Rodados", min_value=0.0)
            t_i = st.time_input("Início")
            t_f = st.time_input("Fim")
            
            if st.form_submit_button("Salvar Dia"):
                cursor.execute("INSERT INTO ganhos (usuario, data, ganho, gasto, km, inicio, fim) VALUES (?,?,?,?,?,?,?)",
                               (user, str(d), v_g, v_c, v_k, t_i.strftime("%H:%M"), t_f.strftime("%H:%M")))
                conn.commit()
                st.success("Dados salvos!")
                st.rerun()

    with col_metric:
        st.subheader("Métricas de Desempenho")
        df = pd.read_sql_query(f"SELECT * FROM ganhos WHERE usuario='{user}'", conn)
        
        if
