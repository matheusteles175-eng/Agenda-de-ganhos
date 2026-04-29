import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime, timedelta

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="Driver Pro Mateus", layout="wide")

def conectar():
    conn = sqlite3.connect("driver_mateus_v8.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS usuarios (usuario TEXT PRIMARY KEY, senha TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS veiculo (usuario TEXT PRIMARY KEY, km_ini REAL, km_alvo REAL, custo REAL, fipe REAL)")
    cursor.execute("CREATE TABLE IF NOT EXISTS metas (id INTEGER PRIMARY KEY, usuario TEXT, item TEXT, valor REAL, data TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS registros (meta_id INTEGER, data TEXT, valor REAL, status TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS ganhos (usuario TEXT, data TEXT, ganho REAL, gasto REAL, km REAL)")
    conn.commit()
    return conn, cursor

conn, cursor = conectar()

# --- 2. LOGIN ---
if "autenticado" not in st.session_state: st.session_state.autenticado = False
if not st.session_state.autenticado:
    u = st.text_input("Usuário").lower()
    s = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        st.session_state.autenticado, st.session_state.user = True, u
        st.rerun()
    st.stop()

user = st.session_state.user
v_data = cursor.execute("SELECT * FROM veiculo WHERE usuario=?", (user,)).fetchone()

# --- 3. CONFIGURAÇÃO INICIAL DO CARRO (FORÇADA NO INÍCIO) ---
if v_data is None:
    st.header(f"Olá {user.capitalize()}, configure seu carro para começar!")
    with st.form("cfg_ini"):
        f1 = st.number_input("Valor FIPE do Carro", value=45000.0)
        f2 = st.number_input("KM Atual", value=100000.0)
        f3 = st.number_input("KM Próxima Troca Óleo", value=110000.0)
        if st.form_submit_button("Salvar e Abrir App"):
            cursor.execute("INSERT INTO veiculo VALUES (?,?,?,?,?)", (user, f2, f3, 300.0, f1))
            conn.commit()
            st.rerun()
    st.stop()

# --- 4. ABAS (Ajustes Primeiro agora) ---
t_cfg, t_ganhos, t_metas = st.tabs(["⚙️ Configurações/IPVA", "💰 Ganhos Diários", "🎯 Caixinhas de Sonhos"])

with t_cfg:
    st.subheader("Dados do Veículo e IPVA")
    v_fipe = v_data[4]
    v_ipva = v_fipe * 0.04
    meses = max(1, (13 - date.today().month)) # Até Janeiro
    st.metric("IPVA Total Estimado", f"R$ {v_ipva:.2f}")
    st.info(f"Mateus, guarde R$ {v_ipva/meses:.2f} por mês para o IPVA.")
    if st.button("Sair"): st.session_state.autenticado = False; st.rerun()

with t_ganhos:
    with st.form("g"):
        g = st.number_input("Ganho de Hoje"); gst = st.number_input("Gasto")
        if st.form_submit_button("Gravar"): st.success("Salvo!")

with t_metas:
    st.subheader("Suas Caixinhas")
    with st.expander("Novo Sonho"):
        with st.form("m"):
            i = st.text_input("Item"); v = st.number_input("Valor"); d = st.date_input("Data")
            if st.form_submit_button("Criar"):
                cursor.execute("INSERT INTO metas (usuario, item, valor, data) VALUES (?,?,?,?)", (user, i, v, str(d)))
                conn.commit(); st.rerun()

    metas = pd.read_sql_query(f"SELECT * FROM metas WHERE usuario='{user}'", conn)
    for _, m in metas.iterrows():
        dt_alvo = datetime.strptime(m['data'], "%Y-%m-%d").date()
        meses_m = max(1, (dt_alvo.year - date.today().year) * 12 + (dt_alvo.month - date.today().month))
        
        st.markdown(f"### {m['item']} - R$ {m['valor']:.2f}")
        st.write(f"👉 **Guardar R$ {m['valor']/meses_m:.2f} por mês**")
        
        cols = st.columns(7)
        for x in range(7):
            dia = date.today() - timedelta(days=3-x)
            with cols[x]:
                st.write(dia.strftime("%d/%m"))
                if st.button("Marcar", key=f"{m['id']}{dia}"):
                    st.session_state.temp = (m['id'], str(dia))
        
        if "temp" in st.session_state and st.session_state.temp[0] == m['id']:
            with st.form("p"):
                val = st.number_input("Quanto guardou hoje?")
                if st.form_submit_button("Confirmar"):
                    msg = "Boa! Mais perto do sonho!" if val > 0 else "Não desanima, Mateus! Amanhã você consegue!"
                    st.info(msg); del st.session_state.temp
