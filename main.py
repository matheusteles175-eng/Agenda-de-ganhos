import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime, timedelta

# 1. CONFIGURAÇÃO DA PÁGINA (Sempre o primeiro comando)
st.set_page_config(page_title="Driver Pro", layout="wide")

# 2. FUNÇÃO DE CONEXÃO E CRIAÇÃO DE TABELAS
def init_db():
    conn = sqlite3.connect("driver_pro.db", check_same_thread=False)
    c = conn.cursor()
    # Tabela de usuários
    c.execute("CREATE TABLE IF NOT EXISTS usuarios (usuario TEXT PRIMARY KEY, senha TEXT)")
    # Tabela de ganhos
    c.execute("""CREATE TABLE IF NOT EXISTS ganhos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT, data TEXT, ganho REAL, gasto REAL, km REAL, 
                inicio TEXT, fim TEXT)""")
    # Tabela de metas
    c.execute("CREATE TABLE IF NOT EXISTS metas (usuario TEXT PRIMARY KEY, km_alvo REAL, hora_alvo REAL, lucro_alvo REAL)")
    conn.commit()
    return conn

conn = init_db()

# 3. CONTROLE DE SESSÃO
if "logado" not in st.session_state:
    st.session_state.logado = False
if "user_atual" not in st.session_state:
    st.session_state.user_atual = ""

# 4. TELA DE ACESSO (SÓ MOSTRA SE NÃO ESTIVER LOGADO)
if not st.session_state.logado:
    st.title("🔐 Bem-vindo ao Driver Pro")
    
    aba_login, aba_cad = st.tabs(["Fazer Login", "Criar Nova Conta"])
    
    with aba_login:
        u = st.text_input("Usuário", key="login_u").lower().strip()
        s = st.text_input("Senha", type="password", key="login_s")
        if st.button("Entrar"):
            cursor = conn.cursor()
            user_db = cursor.execute("SELECT * FROM usuarios WHERE usuario=? AND senha=?", (u, s)).fetchone()
            if user_db:
                st.session_state.logado = True
                st.session_state.user_atual = u
                st.rerun()
            else:
                st.error("❌ Usuário ou senha não encontrados.")
                
    with aba_cad:
        nu = st.text_input("Escolha um Usuário", key="cad_u").lower().strip()
        ns = st.text_input("Escolha uma Senha", type="password", key="cad_s")
        if st.button("Cadastrar Conta"):
            if nu and ns:
                try:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO usuarios (usuario, senha) VALUES (?,?)", (nu, ns))
                    conn.commit()
                    st.success("✅ Conta criada! Agora vá na aba 'Fazer Login'.")
                except sqlite3.IntegrityError:
                    st.error("⚠️ Este nome de usuário já existe.")
            else:
                st.warning("Preencha todos os campos.")
    st.stop() # Interrompe aqui se não estiver logado

# ================= SE CHEGOU AQUI, ESTÁ LOGADO =================

user = st.session_state.user_atual

# Sidebar para Sair e Metas
with st.sidebar:
    st.title(f"👤 {user.capitalize()}")
    if st.button("Deslogar / Sair"):
        st.session_state.logado = False
        st.session_state.user_atual = ""
        st.rerun()
    
    st.divider()
    st.subheader("🎯 Configurar Metas")
    cursor = conn.cursor()
    meta_db = cursor.execute("SELECT * FROM metas WHERE usuario=?", (user,)).fetchone()
    
    # Valores padrão se não existirem no banco
    padrao_km = meta_db[1] if meta_db else 2.0
    padrao_hr = meta_db[2] if meta_db else 30.0
    padrao_lc = meta_db[3] if meta_db else 150.0

    m_km = st.number_input("Meta R$ por KM", value=float(padrao_km))
    m_hr = st.number_input("Meta R$ por Hora", value=float(padrao_hr))
    m_lc = st.number_input("Meta Lucro Diário", value=float(padrao_lc))

    if st.button("Salvar Configurações"):
        cursor.execute("INSERT OR REPLACE INTO metas VALUES (?,?,?,?)", (user, m_km, m_hr, m_lc))
        conn.commit()
        st.success("Metas atualizadas!")

# --- FUNÇÃO DE CÁLCULO ---
def calc_horas(h_ini, h_fim):
    try:
        t1 = datetime.strptime(h_ini, "%H:%M")
        t2 = datetime.strptime(h_fim, "%H:%M")
        return (t2 - t1).total_seconds() / 3600
    except: return 0

# --- DASHBOARD PRINCIPAL ---
st.header("📊 Painel de Desempenho")

aba1, aba2 = st.tabs(["📥 Lançar e Ver Médias", "📜 Histórico de Corridas"])

with aba1:
    c1, c2 = st.columns([1, 2])
    
    with c1:
        st.subheader("Lançamento do Dia")
        with st.form("registro_diario"):
            f_data = st.date_input("Data", date.today())
            f_ganho = st.number_input("Ganho Bruto (R$)", min_value=0.0)
            f_gasto = st.number_input("Gasto/Combustível (R$)", min_value=0.0)
            f_km = st.number_input("KM Rodados", min_value=0.0)
            f_ini = st.time_input("Início", value=datetime.strptime("08:00", "%H:%M"))
            f_fim = st.time_input("Fim", value=datetime.strptime("17:00", "%H:%M"))
            
            if st.form_submit_button("Salvar"):
                cursor = conn.cursor()
                cursor.execute("INSERT INTO ganhos (usuario, data, ganho, gasto, km, inicio, fim) VALUES (?,?,?,?,?,?,?)",
                               (user, str(f_data), f_ganho, f_gasto, f_km, f_ini.strftime("%H:%M"), f_fim.strftime("%H:%M")))
                conn.commit()
                st.rerun()

    with c2:
        st.subheader("Suas Médias")
        df = pd.read_sql_query(f"SELECT * FROM ganhos WHERE usuario='{user}'", conn)
        
        if not df.empty:
            df['data'] = pd.to_datetime(df['data']).dt.date
            df['lucro'] = df['ganho'] - df['gasto']
            df['tempo'] = df.apply(lambda r: calc_horas(r['inicio'], r['fim']), axis=1)
            
            p = st.radio("Período:", ["Hoje", "Últimos 7 dias", "Mês Atual"], horizontal=True)
            hoje = date.today()
            
            if p == "Hoje":
                dados = df[df['data'] == hoje]
            elif p == "Últimos 7 dias":
                dados = df[df['data'] >= (hoje - timedelta(days=7))]
            else:
                dados = df[df['data'] >= hoje.replace(day=1)]
                
            if not dados.empty:
                lucro_total = dados['lucro'].sum()
                km_total = dados['km'].sum()
                horas_total = dados['tempo'].sum()
                
                # Médias Reais
                media_km = lucro_total / km_total if km_total > 0 else 0
                media_hr = lucro_total / horas_total if horas_total > 0 else 0
                
                m1, m2, m3 = st.columns(3)
                m1.metric("Lucro Líquido", f"R$ {lucro_total:.2f}")
                m2.metric("Média R$/KM", f"R$ {media_km:.2f}", f"{media_km - m_km:.2f}")
                m3.metric("Média R$/Hora", f"R$ {media_hr:.2f}", f"{media_hr - m_hr:.2f}")
                
                if p == "Hoje" and lucro_total >= m_lc:
                    st.success("🚀 Parabéns! Meta batida!")
                    st.balloons()
            else:
                st.info("Nenhum dado para o período selecionado.")

with aba2:
    st.subheader("Todos os Registros")
    df_hist = pd.read_sql_query(f"SELECT id, data, ganho, gasto, km, inicio, fim FROM ganhos WHERE usuario='{user}' ORDER BY id DESC", conn)
    if not df_hist.empty:
        st.dataframe(df_hist, use_container_width=True)
        id_del = st.number_input("ID para excluir", min_value=1, step=1)
        if st.button("Remover Registro"):
            cursor = conn.cursor()
            cursor.execute("DELETE FROM ganhos WHERE id=? AND usuario=?", (id_del, user))
            conn.commit()
            st.rerun()
