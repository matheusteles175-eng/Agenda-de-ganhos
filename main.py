import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime, timedelta

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Driver Pro", layout="wide")

# 2. FUNÇÃO DO BANCO DE DADOS (SQLite)
def conectar_banco():
    conn = sqlite3.connect("driver_pro.db", check_same_thread=False)
    cursor = conn.cursor()
    # Tabela de Usuários
    cursor.execute("CREATE TABLE IF NOT EXISTS usuarios (usuario TEXT PRIMARY KEY, senha TEXT)")
    # Tabela de Ganhos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ganhos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT, data TEXT, ganho REAL, gasto REAL, km REAL, 
            inicio TEXT, fim TEXT
        )
    """)
    # Tabela de Metas
    cursor.execute("CREATE TABLE IF NOT EXISTS metas (usuario TEXT PRIMARY KEY, km_alvo REAL, hora_alvo REAL, lucro_alvo REAL)")
    conn.commit()
    return conn

conn = conectar_banco()
cursor = conn.cursor()

# 3. GESTÃO DE LOGIN NO SESSION STATE
if "usuario" not in st.session_state:
    st.session_state.usuario = None

# 4. TELA DE LOGIN
if st.session_state.usuario is None:
    st.title("🔐 Acesso Driver Pro")
    aba_login, aba_cad = st.tabs(["Entrar", "Criar Conta"])
    
    with aba_login:
        u = st.text_input("Usuário").lower().strip()
        s = st.text_input("Senha", type="password")
        if st.button("Logar"):
            res = cursor.execute("SELECT * FROM usuarios WHERE usuario=? AND senha=?", (u, s)).fetchone()
            if res:
                st.session_state.usuario = u
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")
                
    with aba_cad:
        nu = st.text_input("Novo Usuário").lower().strip()
        ns = st.text_input("Nova Senha", type="password")
        if st.button("Cadastrar"):
            try:
                cursor.execute("INSERT INTO usuarios VALUES (?,?)", (nu, ns))
                conn.commit()
                st.success("Cadastro realizado! Use a aba de Login.")
            except:
                st.error("Erro: Este nome de usuário já existe.")
    st.stop()

# 5. CÁLCULO DE HORAS TRABALHADAS
def diff_horas(h1, h2):
    try:
        fmt = "%H:%M"
        delta = datetime.strptime(h2, fmt) - datetime.strptime(h1, fmt)
        return delta.total_seconds() / 3600
    except:
        return 0

# 6. DASHBOARD PRINCIPAL
user = st.session_state.usuario
st.title(f"🚖 Painel de Controle - {user.capitalize()}")

# --- SIDEBAR (METAS) ---
st.sidebar.header("🎯 Suas Metas")
meta_db = cursor.execute("SELECT * FROM metas WHERE usuario=?", (user,)).fetchone()
m_km = st.sidebar.number_input("Meta R$/KM", value=meta_db[1] if meta_db else 2.0)
m_hr = st.sidebar.number_input("Meta R$/Hora", value=meta_db[2] if meta_db else 30.0)
m_lc = st.sidebar.number_input("Meta Lucro/Dia", value=meta_db[3] if meta_db else 150.0)

if st.sidebar.button("Salvar Metas"):
    cursor.execute("INSERT OR REPLACE INTO metas VALUES (?,?,?,?)", (user, m_km, m_hr, m_lc))
    conn.commit()
    st.toast("Metas Atualizadas!")

if st.sidebar.button("Sair"):
    st.session_state.usuario = None
    st.rerun()

# --- ABAS ---
tab1, tab2 = st.tabs(["📊 Ganhos & Médias", "📜 Histórico"])

with tab1:
    col_input, col_dash = st.columns([1, 2])
    
    with col_input:
        st.subheader("Novo Lançamento")
        with st.form("form_registro"):
            data_reg = st.date_input("Data", date.today())
            v_ganho = st.number_input("Ganho Total (R$)", min_value=0.0)
            v_gasto = st.number_input("Gasto (R$)", min_value=0.0)
            v_km = st.number_input("KM Rodados", min_value=0.0)
            t_ini = st.time_input("Início Trabalho", value=datetime.strptime("08:00", "%H:%M"))
            t_fim = st.time_input("Fim Trabalho", value=datetime.strptime("17:00", "%H:%M"))
            
            if st.form_submit_button("Salvar Registro"):
                cursor.execute("INSERT INTO ganhos (usuario, data, ganho, gasto, km, inicio, fim) VALUES (?,?,?,?,?,?,?)",
                               (user, str(data_reg), v_ganho, v_gasto, v_km, t_ini.strftime("%H:%M"), t_fim.strftime("%H:%M")))
                conn.commit()
                st.rerun()

    with col_dash:
        st.subheader("Desempenho Detalhado")
        df = pd.read_sql_query(f"SELECT * FROM ganhos WHERE usuario='{user}'", conn)
        
        if not df.empty:
            df['data'] = pd.to_datetime(df['data']).dt.date
            df['lucro'] = df['ganho'] - df['gasto']
            df['horas'] = df.apply(lambda r: diff_horas(r['inicio'], r['fim']), axis=1)
            
            filtro = st.radio("Período:", ["Hoje", "Semana", "Mês"], horizontal=True)
            hoje = date.today()
            
            if filtro == "Hoje":
                dados = df[df['data'] == hoje]
            elif filtro == "Semana":
                dados = df[df['data'] >= (hoje - timedelta(days=7))]
            else:
                dados = df[df['data'] >= (hoje - timedelta(days=30))]
            
            if not dados.empty:
                lucro_t = dados['lucro'].sum()
                km_t = dados['km'].sum()
                hr_t = dados['horas'].sum()
                
                # Médias
                r_km = lucro_t / km_t if km_t > 0 else 0
                r_hr = lucro_t / hr_t if hr_t > 0 else 0
                
                m1, m2, m3 = st.columns(3)
                m1.metric("Lucro Líquido", f"R$ {lucro_t:.2f}")
                m2.metric("Média R$/KM", f"R$ {r_km:.2f}", f"{r_km - m_km:.2f}")
                m3.metric("Média R$/Hora", f"R$ {r_hr:.2f}", f"{r_hr - m_hr:.2f}")
                
                if lucro_t >= m_lc and filtro == "Hoje":
                    st.success("Meta diária atingida! 🚀")
                    st.balloons()
            else:
                st.info("Sem registros para este período.")

with tab2:
    st.subheader("Gerenciar Histórico")
    df_hist = pd.read_sql_query(f"SELECT id, data, ganho, gasto, km, inicio, fim FROM ganhos WHERE usuario='{user}' ORDER BY id DESC", conn)
    if not df_hist.empty:
        st.table(df_hist) # st.table é mais simples e evita erros de exibição
        id_excluir = st.number_input("ID para apagar", min_value=1, step=1)
        if st.button("Confirmar Exclusão"):
            cursor.execute("DELETE FROM ganhos WHERE id=? AND usuario=?", (id_excluir, user))
            conn.commit()
            st.rerun()
    else:
        st.write("Histórico vazio.")
