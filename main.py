import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime, timedelta

# --- 1. CONFIGURAÇÃO INICIAL (OBRIGATÓRIO SER O PRIMEIRO) ---
st.set_page_config(page_title="Driver Pro Oficial", layout="wide")

# --- 2. GERENCIAMENTO DE BANCO DE DADOS (REVISADO) ---
def conectar():
    """Cria conexão e garante que as tabelas existam"""
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
    return conn, cursor

conn, cursor = conectar()

# --- 3. CONTROLE DE LOGIN (SESSION STATE) ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "user_logado" not in st.session_state:
    st.session_state.user_logado = ""

# --- 4. TELA DE LOGIN / CADASTRO ---
if not st.session_state.autenticado:
    st.title("🚖 Driver Pro - Acesso ao Sistema")
    
    tab_login, tab_cadastro = st.tabs(["Fazer Login", "Criar Nova Conta"])
    
    with tab_login:
        with st.form("form_login"):
            u_input = st.text_input("Usuário").strip().lower()
            s_input = st.text_input("Senha", type="password")
            btn_login = st.form_submit_button("Entrar no Painel")
            
            if btn_login:
                if u_input and s_input:
                    cursor.execute("SELECT * FROM usuarios WHERE usuario=? AND senha=?", (u_input, s_input))
                    user_data = cursor.fetchone()
                    if user_data:
                        st.session_state.autenticado = True
                        st.session_state.user_logado = u_input
                        st.rerun()
                    else:
                        st.error("❌ Usuário não encontrado ou senha incorreta.")
                else:
                    st.warning("Preencha todos os campos.")

    with tab_cadastro:
        with st.form("form_cadastro"):
            u_novo = st.text_input("Escolha um Nome de Usuário").strip().lower()
            s_nova = st.text_input("Escolha uma Senha", type="password")
            btn_cad = st.form_submit_button("Finalizar Cadastro")
            
            if btn_cad:
                if u_novo and s_nova:
                    try:
                        cursor.execute("INSERT INTO usuarios (usuario, senha) VALUES (?, ?)", (u_novo, s_nova))
                        conn.commit()
                        st.success(f"✅ Usuário '{u_novo}' cadastrado! Agora vá na aba de Login.")
                    except sqlite3.IntegrityError:
                        st.error("⚠️ Este nome de usuário já está em uso.")
                else:
                    st.warning("Preencha os campos para cadastrar.")
    
    st.stop() # Bloqueia o restante do app enquanto não logar

# --- 5. ÁREA DO MOTORISTA (LOGADO) ---
usuario = st.session_state.user_logado

# Barra Lateral
with st.sidebar:
    st.subheader(f"👤 Motorista: {usuario.upper()}")
    if st.button("Encerrar Sessão (Sair)"):
        st.session_state.autenticado = False
        st.session_state.user_logado = ""
        st.rerun()
    
    st.divider()
    st.subheader("🎯 Suas Metas")
    cursor.execute("SELECT km_alvo, hora_alvo, lucro_alvo FROM metas WHERE usuario=?", (usuario,))
    meta_at = cursor.fetchone()
    
    m_km = st.number_input("Meta R$/KM", value=meta_at[0] if meta_at else 2.0)
    m_hr = st.number_input("Meta R$/Hora", value=meta_at[1] if meta_at else 30.0)
    m_lc = st.number_input("Meta Lucro Dia", value=meta_at[2] if meta_at else 150.0)
    
    if st.button("Salvar Metas"):
        cursor.execute("INSERT OR REPLACE INTO metas VALUES (?, ?, ?, ?)", (usuario, m_km, m_hr, m_lc))
        conn.commit()
        st.toast("Metas salvas com sucesso!")

# --- 6. FUNÇÕES DE CÁLCULO ---
def calcular_duracao(inicio, fim):
    try:
        t1 = datetime.strptime(inicio, "%H:%M")
        t2 = datetime.strptime(fim, "%H:%M")
        diff = t2 - t1
        return diff.total_seconds() / 3600 # Retorna em horas decimais
    except:
        return 0

# --- 7. PAINEL PRINCIPAL ---
st.header("📊 Gestão de Ganhos e Médias")

aba_painel, aba_hist = st.tabs(["📈 Dashboard Diário", "📋 Histórico de Corridas"])

with aba_painel:
    col_l, col_r = st.columns([1, 2])
    
    with col_l:
        st.subheader("Lançamento")
        with st.form("add_ganho"):
            f_data = st.date_input("Data", date.today())
            f_ganho = st.number_input("Ganho Bruto (R$)", min_value=0.0)
            f_gasto = st.number_input("Gasto/Combustível (R$)", min_value=0.0)
            f_km = st.number_input("KM Rodados", min_value=0.0)
            f_ini = st.time_input("Início Jornada", value=datetime.strptime("08:00", "%H:%M"))
            f_fim = st.time_input("Fim Jornada", value=datetime.strptime("17:00", "%H:%M"))
            
            if st.form_submit_button("Gravar no Banco"):
                cursor.execute("INSERT INTO ganhos (usuario, data, ganho, gasto, km, inicio, fim) VALUES (?,?,?,?,?,?,?)",
                               (usuario, str(f_data), f_ganho, f_gasto, f_km, f_ini.strftime("%H:%M"), f_fim.strftime("%H:%M")))
                conn.commit()
                st.success("Salvo!")
                st.rerun()

    with col_r:
        st.subheader("Análise de Desempenho")
        df = pd.read_sql_query(f"SELECT * FROM ganhos WHERE usuario='{usuario}'", conn)
        
        if not df.empty:
            df['data'] = pd.to_datetime(df['data']).dt.date
            df['lucro'] = df['ganho'] - df['gasto']
            df['horas_trab'] = df.apply(lambda r: calcular_duracao(r['inicio'], r['fim']), axis=1)
            
            periodo = st.radio("Filtrar por:", ["Hoje", "Últimos 7 Dias", "Mês Atual"], horizontal=True)
            hoje_dt = date.today()
            
            if periodo == "Hoje":
                filtro_df = df[df['data'] == hoje_dt]
            elif periodo == "Últimos 7 Dias":
                filtro_df = df[df['data'] >= (hoje_dt - timedelta(days=7))]
            else:
                filtro_df = df[df['data'] >= hoje_dt.replace(day=1)]
            
            if not filtro_df.empty:
                l_total = filtro_df['lucro'].sum()
                km_total = filtro_df['km'].sum()
                hr_total = filtro_df['horas_trab'].sum()
                
                m_km_real = l_total / km_total if km_total > 0 else 0
                m_hr_real = l_total / hr_total if hr_total > 0 else 0
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Lucro Líquido", f"R$ {l_total:.2f}")
                c2.metric("Média R$/KM", f"R$ {m_km_real:.2f}", f"{m_km_real - m_km:.2f}")
                c3.metric("Média R$/Hora", f"R$ {m_hr_real:.2f}", f"{m_hr_real - m_hr:.2f}")
                
                if l_total >= m_lc and periodo == "Hoje":
                    st.balloons()
                    st.success("✅ Parabéns! Meta de lucro batida hoje!")
            else:
                st.info("Nenhum registro para este período.")

with aba_hist:
    st.subheader("Histórico Completo")
    df_lista = pd.read_sql_query(f"SELECT id, data, ganho, gasto, km, inicio, fim FROM ganhos WHERE usuario='{usuario}' ORDER BY id DESC", conn)
    if not df_lista.empty:
        st.dataframe(df_lista, use_container_width=True)
        
        id_excluir = st.number_input("ID para remover", min_value=1, step=1)
        if st.button("Confirmar Exclusão"):
            cursor.execute("DELETE FROM ganhos WHERE id=? AND usuario=?", (id_excluir, usuario))
            conn.commit()
            st.rerun()
