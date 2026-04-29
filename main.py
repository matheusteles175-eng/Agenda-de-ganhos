import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime, timedelta

# --- 1. CONFIGURAÇÃO E ESTILO ---
st.set_page_config(page_title="Driver Pro Mateus", layout="wide")

def conectar():
    conn = sqlite3.connect("driver_mateus_v9.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS usuarios (usuario TEXT PRIMARY KEY, senha TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS veiculo (usuario TEXT PRIMARY KEY, km_ini REAL, km_alvo REAL, custo REAL, fipe REAL)")
    cursor.execute("CREATE TABLE IF NOT EXISTS metas (id INTEGER PRIMARY KEY, usuario TEXT, item TEXT, valor REAL, data TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS registros (meta_id INTEGER, data TEXT, valor REAL, status TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS ganhos (usuario TEXT, data TEXT, ganho REAL, gasto REAL, km REAL)")
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
            user_db = cursor.execute("SELECT * FROM usuarios WHERE usuario=? AND senha=?", (u, s)).fetchone()
            if user_db:
                st.session_state.autenticado, st.session_state.user = True, u
                st.rerun()
            else: st.error("Usuário ou senha inválidos.")
            
    with aba_cad:
        nu = st.text_input("Novo Usuário").lower().strip()
        ns = st.text_input("Nova Senha", type="password")
        if st.button("Finalizar Cadastro"):
            try:
                cursor.execute("INSERT INTO usuarios VALUES (?,?)", (nu, ns))
                conn.commit()
                st.success("Conta criada com sucesso! Faça o login.")
            except: st.error("Este usuário já existe.")
    st.stop()

# --- 3. VERIFICAÇÃO DE CONFIGURAÇÃO DO CARRO ---
user = st.session_state.user
v_data = cursor.execute("SELECT * FROM veiculo WHERE usuario=?", (user,)).fetchone()

if v_data is None:
    st.header(f"Bem-vindo, {user.capitalize()}! 🚀")
    st.subheader("Configure seu veículo para liberar o painel:")
    with st.form("cfg_obrigatoria"):
        f1 = st.number_input("Valor FIPE do seu veículo (R$)", value=40000.0)
        f2 = st.number_input("KM Atual do Painel", value=100000.0)
        f3 = st.number_input("KM da Próxima Troca de Óleo", value=110000.0)
        if st.form_submit_button("Salvar e Abrir Meu App"):
            cursor.execute("INSERT INTO veiculo VALUES (?,?,?,?,?)", (user, f2, f3, 350.0, f1))
            conn.commit()
            st.rerun()
    st.stop()

# --- 4. PAINEL PRINCIPAL (ABAS REORGANIZADAS) ---
st.title(f"Painel do {user.capitalize()} 🏁")
t_cfg, t_ganhos, t_metas = st.tabs(["⚙️ Carro & IPVA", "💰 Ganhos Diários", "🎯 Caixinhas (Sonhos)"])

with t_cfg:
    st.subheader("Informações do Veículo")
    v_fipe = v_data[4]
    v_ipva = v_fipe * 0.04
    hoje = date.today()
    vencimento = date(hoje.year + (1 if hoje.month > 1 else 0), 1, 15)
    meses_ipva = max(1, (vencimento.year - hoje.year) * 12 + (vencimento.month - hoje.month))
    
    c1, c2 = st.columns(2)
    c1.metric("IPVA Total (Estimado)", f"R$ {v_ipva:.2f}")
    c2.metric("Guardar p/ Mês (IPVA)", f"R$ {v_ipva/meses_ipva:.2f}")
    
    st.info(f"💡 Mateus, reserve R$ {v_ipva/meses_ipva:.2f} todo mês para pagar o IPVA em Janeiro sem sustos.")
    if st.button("Deslogar"): st.session_state.autenticado = False; st.rerun()

with t_ganhos:
    st.subheader("Registro de Entradas")
    with st.form("form_ganhos"):
        g = st.number_input("Quanto faturou hoje?")
        gst = st.number_input("Gasto com combustível/outros")
        if st.form_submit_button("Salvar Ganho"):
            cursor.execute("INSERT INTO ganhos VALUES (?,?,?,?,?)", (user, str(hoje), g, gst, 0))
            conn.commit(); st.success("Registrado!")

with t_metas:
    st.subheader("Suas Conquistas")
    with st.expander("➕ Criar Nova Caixinha"):
        with st.form("f_metas"):
            item = st.text_input("Qual o seu sonho?"); valor = st.number_input("Valor (R$)"); data_m = st.date_input("Data Alvo")
            if st.form_submit_button("Criar"):
                cursor.execute("INSERT INTO metas (usuario, item, valor, data) VALUES (?,?,?,?)", (user, item, valor, str(data_m)))
                conn.commit(); st.rerun()

    metas_db = pd.read_sql_query(f"SELECT * FROM metas WHERE usuario='{user}'", conn)
    for _, m in metas_db.iterrows():
        dt_alvo = datetime.strptime(m['data'], "%Y-%m-%d").date()
        meses_m = max(1, (dt_alvo.year - hoje.year) * 12 + (dt_alvo.month - hoje.month))
        st.markdown(f"---")
        st.markdown(f"### 🚀 {m['item']} (Total: R$ {m['valor']:.2f})")
        st.write(f"👉 **Planejamento: Guardar R$ {m['valor']/meses_m:.2f} por mês**")
        
        cols = st.columns(7)
        for x in range(7):
            dia_f = hoje - timedelta(days=3-x)
            with cols[x]:
                st.write(dia_f.strftime("%d/%m"))
                if st.button("Marcar", key=f"m_{m['id']}_{dia_f}"):
                    st.session_state.temp = (m['id'], str(dia_f), m['item'])
        
        if "temp" in st.session_state and st.session_state.temp[0] == m['id']:
            with st.form(f"p_{m['id']}"):
                v_pago = st.number_input(f"Quanto guardou hoje para {st.session_state.temp[2]}?")
                if st.form_submit_button("Confirmar"):
                    if v_pago <= 0:
                        st.warning(f"Não desanima, Mateus! O {st.session_state.temp[2]} está te esperando. Amanhã você consegue!")
                    else:
                        st.balloons(); st.success("Isso aí! O seu bem está cada vez mais perto!")
                    del st.session_state.temp
