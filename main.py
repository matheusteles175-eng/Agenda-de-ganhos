import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime, timedelta

st.set_page_config(page_title="Driver Pro - Gestão de Ganhos", layout="wide", page_icon="🚖")

# --- BANCO DE DADOS ---
conn = sqlite3.connect("driver_pro.db", check_same_thread=False)
cursor = conn.cursor()

def init_db():
    cursor.execute("CREATE TABLE IF NOT EXISTS usuarios (usuario TEXT PRIMARY KEY, senha TEXT)")
    cursor.execute("""CREATE TABLE IF NOT EXISTS ganhos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, 
                        usuario TEXT, data TEXT, ganho REAL, gasto REAL, km REAL, 
                        inicio TEXT, fim TEXT)""")
    cursor.execute("CREATE TABLE IF NOT EXISTS metas (usuario TEXT PRIMARY KEY, km_alvo REAL, hora_alvo REAL, lucro_alvo REAL)")
    cursor.execute("CREATE TABLE IF NOT EXISTS gastos_fixos (id INTEGER PRIMARY KEY AUTOINCREMENT, usuario TEXT, nome TEXT, valor REAL, status TEXT, vencimento TEXT)")
    conn.commit()

init_db()

# --- AUTENTICAÇÃO ---
if "usuario" not in st.session_state:
    st.session_state.usuario = ""

if not st.session_state.usuario:
    st.title("🚖 Driver Pro Login")
    aba_l, aba_c = st.tabs(["Entrar", "Criar Conta"])
    with aba_l:
        u = st.text_input("Usuário").lower().strip()
        s = st.text_input("Senha", type="password")
        if st.button("Acessar"):
            cursor.execute("SELECT * FROM usuarios WHERE usuario=? AND senha=?", (u, s))
            if cursor.fetchone():
                st.session_state.usuario = u
                st.rerun()
            else: st.error("Dados inválidos")
    with aba_c:
        nu = st.text_input("Novo Usuário").lower().strip()
        ns = st.text_input("Nova Senha", type="password")
        if st.button("Cadastrar"):
            try:
                cursor.execute("INSERT INTO usuarios VALUES (?,?)", (nu, ns))
                conn.commit()
                st.success("Conta criada!")
            except: st.error("Usuário já existe")
    st.stop()

user = st.session_state.usuario

# --- FUNÇÕES DE CÁLCULO ---
def calc_horas(inicio, fim):
    fmt = '%H:%M'
    t1 = datetime.strptime(inicio, fmt)
    t2 = datetime.strptime(fim, fmt)
    delta = t2 - t1
    return delta.total_seconds() / 3600

# --- SIDEBAR (METAS) ---
with st.sidebar:
    st.header(f"👤 {user.capitalize()}")
    cursor.execute("SELECT * FROM metas WHERE usuario=?", (user,))
    m_data = cursor.fetchone()
    m_km = st.number_input("Meta R$/KM", value=m_data[1] if m_data else 2.0)
    m_hr = st.number_input("Meta R$/Hora", value=m_data[2] if m_data else 35.0)
    m_lc = st.number_input("Meta Lucro Diário", value=m_data[3] if m_data else 150.0)
    if st.button("Salvar Metas"):
        cursor.execute("INSERT OR REPLACE INTO metas VALUES (?,?,?,?)", (user, m_km, m_hr, m_lc))
        conn.commit()
        st.toast("Metas atualizadas!")
    
    if st.button("Sair"):
        st.session_state.usuario = ""
        st.rerun()

# --- CONTEÚDO PRINCIPAL ---
st.title("Painel de Controle de Ganhos")

tab1, tab2, tab3 = st.tabs(["📊 Dashboard & Lançamento", "📅 Histórico Detalhado", "💸 Despesas Fixas"])

with tab1:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("📝 Lançar Corrida")
        with st.form("form_ganhos"):
            data_cor = st.date_input("Data", date.today())
            v_ganho = st.number_input("Ganho Total (R$)", min_value=0.0, step=10.0)
            v_gasto = st.number_input("Gasto Combustível/Outros (R$)", min_value=0.0, step=5.0)
            v_km = st.number_input("KM Rodados", min_value=0.0, step=1.0)
            h_ini = st.time_input("Hora Início", datetime.now().replace(hour=8, minute=0))
            h_fim = st.time_input("Hora Fim", datetime.now().replace(hour=17, minute=0))
            
            if st.form_submit_button("Salvar Registro"):
                cursor.execute("INSERT INTO ganhos (usuario, data, ganho, gasto, km, inicio, fim) VALUES (?,?,?,?,?,?,?)",
                               (user, str(data_cor), v_ganho, v_gasto, v_km, h_ini.strftime("%H:%M"), h_fim.strftime("%H:%M")))
                conn.commit()
                st.success("Salvo!")
                st.rerun()

    # --- PROCESSAMENTO DE DADOS ---
    df = pd.read_sql_query(f"SELECT * FROM ganhos WHERE usuario='{user}'", conn)
    if not df.empty:
        df['data'] = pd.to_datetime(df['data'])
        df['lucro'] = df['ganho'] - df['gasto']
        df['horas'] = df.apply(lambda r: calc_horas(r['inicio'], r['fim']), axis=1)
        
        # Filtros de tempo
        hoje = pd.Timestamp(date.today())
        esta_semana = hoje - timedelta(days=hoje.weekday())
        este_mes = hoje.replace(day=1)

        def metricas(dataframe, titulo):
            lucro_t = dataframe['lucro'].sum()
            km_t = dataframe['km'].sum()
            hr_t = dataframe['horas'].sum()
            
            # Médias
            r_km = lucro_t / km_t if km_t > 0 else 0
            r_hr = lucro_t / hr_t if hr_t > 0 else 0
            
            st.markdown(f"### {titulo}")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Lucro Líquido", f"R$ {lucro_t:.2f}")
            c2.metric("R$ / KM", f"R$ {r_km:.2f}", delta=f"{r_km-m_km:.2f}" if m_km else None)
            c3.metric("R$ / Hora", f"R$ {r_hr:.2f}", delta=f"{r_hr-m_hr:.2f}" if m_hr else None)
            c4.metric("Total KM", f"{km_t:.1f} km")

        with col2:
            periodo = st.radio("Ver período:", ["Hoje", "Esta Semana", "Mês Atual"], horizontal=True)
            if periodo == "Hoje":
                metricas(df[df['data'] == hoje], "Resultados de Hoje")
            elif periodo == "Esta Semana":
                metricas(df[df['data'] >= esta_semana], "Resultados da Semana")
            else:
                metricas(df[df['data'] >= este_mes], "Resultados do Mês")

with tab2:
    st.subheader("📖 Todos os Lançamentos")
    df_show = pd.read_sql_query(f"SELECT id, data, ganho, gasto, km, inicio, fim FROM ganhos WHERE usuario='{user}' ORDER BY data DESC", conn)
    if not df_show.empty:
        # Cálculo de lucro para a tabela
        df_show['Lucro'] = df_show['ganho'] - df_show['gasto']
        st.dataframe(df_show, use_container_width=True)
        
        id_del = st.number_input("ID para excluir", min_value=0, step=1)
        if st.button("Excluir Registro"):
            cursor.execute("DELETE FROM ganhos WHERE id=? AND usuario=?", (id_del, user))
            conn.commit()
            st.rerun()
    else:
        st.info("Nenhum dado registrado.")

with tab3:
    st.subheader("💸 Gestão de Despesas Fixas (IPVA, Seguro, Aluguel)")
    c1, c2, c3 = st.columns(3)
    d_nome = c1.text_input("Item")
    d_valor = c2.number_input("Valor R$", min_value=0.0)
    d_venc = c3.date_input("Vencimento")
    
    if st.button("Adicionar Despesa"):
        cursor.execute("INSERT INTO gastos_fixos (usuario, nome, valor, status, vencimento) VALUES (?,?,?,?,?)",
                       (user, d_nome, d_valor, "Pendente", str(d_venc)))
        conn.commit()
        st.rerun()

    gastos_df = pd.read_sql_query(f"SELECT * FROM gastos_fixos WHERE usuario='{user}'", conn)
    if not gastos_df.empty:
        for i, row in gastos_df.iterrows():
            col1, col2, col3, col4 = st.columns([2,1,1,1])
            status_cor = "✅" if row['status'] == "Pago" else "🔴"
            col1.write(f"{status_cor} **{row['nome']}**")
            col2.write(f"R$ {row['valor']:.2f}")
            col3.write(f"Vence: {row['vencimento']}")
            if row['status'] == "Pendente":
                if col4.button("Pagar", key=f"pay_{row['id']}"):
                    cursor.execute("UPDATE gastos_fixos SET status='Pago' WHERE id=?", (row['id'],))
                    conn.commit()
                    st.rerun()
            elif col4.button("🗑️", key=f"del_g_{row['id']}"):
                cursor.execute("DELETE FROM gastos_fixos WHERE id=?", (row['id'],))
                conn.commit()
                st.rerun()
