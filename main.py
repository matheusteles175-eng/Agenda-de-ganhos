import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime, timedelta

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="Driver Pro Mateus", layout="wide")

def conectar():
    conn = sqlite3.connect("driver_mateus_v12.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS usuarios (usuario TEXT PRIMARY KEY, senha TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS veiculo (usuario TEXT PRIMARY KEY, km_ini REAL, km_alvo REAL, custo REAL, fipe REAL, guardado_ipva REAL)")
    cursor.execute("CREATE TABLE IF NOT EXISTS metas (id INTEGER PRIMARY KEY, usuario TEXT, item TEXT, valor REAL, data TEXT, guardado REAL)")
    cursor.execute("CREATE TABLE IF NOT EXISTS ganhos (usuario TEXT, data TEXT, ganho REAL, gasto REAL, km REAL, h_ini TEXT, h_fim TEXT)")
    conn.commit()
    return conn, cursor

conn, cursor = conectar()

# --- 2. LOGIN E CADASTRO ---
if "autenticado" not in st.session_state: st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.title("🚖 Driver Pro - Acesso")
    aba_login, aba_cad = st.tabs(["🔑 Entrar", "📝 Criar Conta"])
    with aba_login:
        u = st.text_input("Usuário").lower().strip()
        s = st.text_input("Senha", type="password")
        if st.button("Acessar Aplicativo"):
            if cursor.execute("SELECT * FROM usuarios WHERE usuario=? AND senha=?", (u, s)).fetchone():
                st.session_state.autenticado, st.session_state.user = True, u
                st.rerun()
            else: st.error("Usuário ou senha inválidos.")
    with aba_cad:
        nu = st.text_input("Novo Usuário").lower().strip()
        ns = st.text_input("Nova Senha", type="password")
        if st.button("Finalizar Cadastro"):
            try:
                cursor.execute("INSERT INTO usuarios VALUES (?,?)", (nu, ns))
                conn.commit(); st.success("Conta criada!")
            except: st.error("Usuário já existe.")
    st.stop()

user = st.session_state.user
hoje = date.today()

# --- 3. CONFIGURAÇÃO DO VEÍCULO ---
v_data = cursor.execute("SELECT * FROM veiculo WHERE usuario=?", (user,)).fetchone()
if v_data is None:
    st.header(f"Bem-vindo, {user.capitalize()}! Configure seu carro:")
    with st.form("cfg"):
        f1 = st.number_input("Valor FIPE", value=40000.0)
        f2 = st.number_input("KM Atual", value=100000.0)
        if st.form_submit_button("Salvar"):
            cursor.execute("INSERT INTO veiculo VALUES (?,?,?,?,?,?)", (user, f2, f2+10000, 350.0, f1, 0.0))
            conn.commit(); st.rerun()
    st.stop()

# --- 4. PAINEL PRINCIPAL ---
st.title(f"Painel do {user.upper()} 🏁")
tab_resumo, tab_ganhos, tab_metas = st.tabs(["📊 Resumo e IPVA", "💰 Ganhos e Histórico", "🎯 Caixinhas"])

with tab_resumo:
    # Lógica IPVA Detalhada
    fipe, guardado_ipva = v_data[4], v_data[5]
    total_ipva = fipe * 0.04
    meses_jan = max(1, (13 - hoje.month))
    falta_ipva = total_ipva - guardado_ipva
    
    st.subheader("📌 Planejamento IPVA")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total IPVA", f"R$ {total_ipva:.2f}")
    c2.metric("Já Guardado", f"R$ {guardado_ipva:.2f}")
    c3.metric("Falta Guardar", f"R$ {falta_ipva:.2f}")
    
    st.info(f"💡 Mateus, de hoje até Janeiro faltam {meses_jan} meses. A conta é: (R$ {total_ipva:.2f} - R$ {guardado_ipva:.2f}) / {meses_jan} meses. **Guarde R$ {falta_ipva/meses_jan:.2f} por mês.**")
    
    new_ipva = st.number_input("Adicionar valor ao fundo IPVA:", value=0.0)
    if st.button("Atualizar Fundo"):
        cursor.execute("UPDATE veiculo SET guardado_ipva = guardado_ipva + ? WHERE usuario=?", (new_ipva, user))
        conn.commit(); st.rerun()

with tab_ganhos:
    # Lançamento
    with st.form("g", clear_on_submit=True):
        col1, col2 = st.columns(2)
        h_i = col1.text_input("Início", "08:00")
        h_f = col2.text_input("Fim", "18:00")
        g, gst, k = st.columns(3)
        v_g = g.number_input("Ganho Bruto", value=None, placeholder="0.00")
        v_gst = gst.number_input("Gasto", value=None, placeholder="0.00")
        v_k = k.number_input("KM Rodado", value=None, placeholder="0")
        if st.form_submit_button("Gravar Jornada"):
            cursor.execute("INSERT INTO ganhos VALUES (?,?,?,?,?,?,?)", (user, str(hoje), v_g, v_gst, v_k, h_i, h_f))
            conn.commit(); st.success("Gravado!"); st.rerun()

    # Histórico
    st.subheader("📜 Histórico Recente")
    df_g = pd.read_sql_query(f"SELECT * FROM ganhos WHERE usuario='{user}' ORDER BY data DESC", conn)
    if not df_g.empty:
        for i, row in df_g.iterrows():
            with st.container(border=True):
                c1, c2, c3 = st.columns([1, 2, 1])
                c1.write(f"📅 {row['data']}")
                c2.write(f"💰 Lucro: **R$ {row['ganho']-row['gasto']:.2f}** (Bruto: {row['ganho']} | Gasto: {row['gasto']})")
                c3.write(f"⏰ {row['h_ini']} - {row['h_fim']}")

with tab_metas:
    st.subheader("🎯 Objetivos (Caixinhas)")
    with st.expander("➕ Nova Meta"):
        with st.form("m"):
            it = st.text_input("Sonho"); v = st.number_input("Valor"); d = st.date_input("Data")
            if st.form_submit_button("Criar"):
                cursor.execute("INSERT INTO metas (usuario, item, valor, data, guardado) VALUES (?,?,?,?,?)", (user, it, v, str(d), 0.0))
                conn.commit(); st.rerun()

    metas = pd.read_sql_query(f"SELECT * FROM metas WHERE usuario='{user}'", conn)
    for i, m in metas.iterrows():
        with st.container(border=True):
            ja = m['guardado'] or 0.0
            progresso = min(ja / m['valor'], 1.0) if m['valor'] > 0 else 0
            st.write(f"### 🚀 {m['item']}")
            st.progress(progresso)
            st.write(f"Já guardou R$ {ja:.2f} de R$ {m['valor']:.2f}")
            
            v_dep = st.number_input(f"Quanto guardar para {m['item']} hoje?", key=f"dep_{i}")
            if st.button("Depositar", key=f"btn_{i}"):
                cursor.execute("UPDATE metas SET guardado = guardado + ? WHERE id=?", (v_dep, m['id']))
                conn.commit(); st.rerun()
