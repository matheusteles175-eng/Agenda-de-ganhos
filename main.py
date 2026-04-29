import streamlit as st
import sqlite3
import pandas as pd
import random
from datetime import date, datetime, timedelta

# --- 1. CONFIGURAÇÃO DE TELA ---
st.set_page_config(page_title="Driver Pro - O App do Mateus", layout="wide", page_icon="🚖")

def aplicar_estilo():
    st.markdown("""
        <style>
        .main { background-color: #f8f9fa; }
        .stMetric { background-color: white; padding: 15px; border-radius: 15px; box-shadow: 0px 4px 10px rgba(0,0,0,0.05); border-bottom: 5px solid #1e3c72; }
        .card-conquista {
            background: linear-gradient(135deg, #1e3c72, #2a5298);
            padding: 20px; border-radius: 20px; color: white; margin-bottom: 15px;
        }
        .msg-motivacao { padding: 15px; border-radius: 10px; background-color: #fff3cd; color: #856404; font-weight: bold; border-left: 5px solid #ffeeba; margin-bottom: 20px; }
        </style>
    """, unsafe_allow_html=True)

aplicar_estilo()

# --- 2. BANCO DE DADOS UNIFICADO ---
def conectar():
    conn = sqlite3.connect("driver_final_mateus.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS usuarios (usuario TEXT PRIMARY KEY, senha TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS ganhos (id INTEGER PRIMARY KEY AUTOINCREMENT, usuario TEXT, data TEXT, ganho REAL, gasto REAL, km_rodado REAL)")
    cursor.execute("CREATE TABLE IF NOT EXISTS veiculo (usuario TEXT PRIMARY KEY, km_inicial REAL, km_troca_alvo REAL, custo_estimado REAL, valor_fipe REAL)")
    cursor.execute("CREATE TABLE IF NOT EXISTS metas_livres (id INTEGER PRIMARY KEY AUTOINCREMENT, usuario TEXT, item TEXT, valor_total REAL, data_alvo TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS registro_diario (id INTEGER PRIMARY KEY AUTOINCREMENT, meta_id INTEGER, data TEXT, valor_pago REAL, status TEXT)")
    conn.commit()
    return conn, cursor

conn, cursor = conectar()

# --- 3. SISTEMA DE LOGIN ---
if "autenticado" not in st.session_state: st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.title("🚖 Bem-vindo ao Driver Pro")
    aba_l, aba_c = st.tabs(["🔑 Entrar", "📝 Criar Conta"])
    with aba_l:
        u = st.text_input("Usuário").strip().lower()
        s = st.text_input("Senha", type="password")
        if st.button("Acessar Painel"):
            res = cursor.execute("SELECT * FROM usuarios WHERE usuario=? AND senha=?", (u, s)).fetchone()
            if res:
                st.session_state.autenticado, st.session_state.user = True, u
                st.rerun()
            else: st.error("Usuário ou senha incorretos.")
    with aba_c:
        nu = st.text_input("Novo Usuário").strip().lower()
        ns = st.text_input("Nova Senha", type="password")
        if st.button("Cadastrar"):
            try:
                cursor.execute("INSERT INTO usuarios VALUES (?,?)", (nu, ns))
                conn.commit()
                st.success("Conta criada! Volte na aba de Login.")
            except: st.error("Este nome já existe.")
    st.stop()

user = st.session_state.user

# --- 4. CARREGAR DADOS ---
v_data = cursor.execute("SELECT * FROM veiculo WHERE usuario=?", (user,)).fetchone()
df_ganhos = pd.read_sql_query(f"SELECT * FROM ganhos WHERE usuario='{user}'", conn)
metas_livres = pd.read_sql_query(f"SELECT * FROM metas_livres WHERE usuario='{user}'", conn)

# --- 5. TELA PRINCIPAL ---
st.title(f"Painel de Controle - {user.capitalize()} 🏁")

# Abas de navegação (O "Coração" do App que tinha sumido)
tab_ganhos, tab_manutencao, tab_metas, tab_ajustes = st.tabs([
    "💰 Ganhos & Salário", 
    "🔧 Carro & IPVA", 
    "🎯 Minhas Caixinhas (Sonhos)", 
    "⚙️ Configurações"
])

# --- ABA 1: GANHOS ---
with tab_ganhos:
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("📥 Lançar Valor")
        with st.form("f_ganho", clear_on_submit=True):
            f_val = st.number_input("Valor Recebido (R$)")
            f_gas = st.number_input("Gasto (Combustível/Outros)")
            f_km = st.number_input("KM Rodados (Opcional)")
            if st.form_submit_button("Salvar Registro"):
                cursor.execute("INSERT INTO ganhos (usuario, data, ganho, gasto, km_rodado) VALUES (?,?,?,?,?)",
                               (user, str(date.today()), f_val, f_gas, f_km))
                conn.commit()
                st.rerun()
    with c2:
        if not df_ganhos.empty:
            ganho_t = df_ganhos['ganho'].sum()
            lucro_t = ganho_t - df_ganhos['gasto'].sum()
            st.metric("Lucro Total Acumulado", f"R$ {lucro_t:.2f}")
            st.line_chart(df_ganhos.tail(10).set_index('data')['ganho'])

# --- ABA 2: MANUTENÇÃO E IPVA ---
with tab_manutencao:
    if v_data:
        km_ini, km_alvo, custo_m, v_fipe = v_data[1], v_data[2], v_data[3], v_data[4]
        km_atual = km_ini + df_ganhos['km_rodado'].sum()
        
        col_m, col_i = st.columns(2)
        with col_m:
            st.subheader("🛠️ Troca de Óleo")
            resta = km_alvo - km_atual
            st.metric("Faltam", f"{resta:.0f} KM")
            if resta < 500: st.warning("Troca de óleo chegando!")
        
        with col_i:
            st.subheader("📄 IPVA Inteligente (SP)")
            v_ipva = v_fipe * 0.04
            hoje = date.today()
            vencimento = date(hoje.year + (1 if hoje.month > 1 else 0), 1, 15)
            meses_faltam = max(1, (vencimento.year - hoje.year) * 12 + (vencimento.month - hoje.month))
            st.write(f"Total: **R$ {v_ipva:.2f}**")
            st.info(f"Mateus, guarde **R$ {v_ipva/meses_faltam:.2f}/mês** para pagar em Janeiro.")
    else:
        st.info("Vá em 'Configurações' para cadastrar seu carro.")

# --- ABA 3: CAIXINHAS (METAS COM CALENDÁRIO) ---
with tab_metas:
    st.header("🎯 Suas Caixinhas de Sonhos")
    
    col_add, col_lista = st.columns([1, 2])
    with col_add:
        with st.form("nova_meta"):
            st.write("Adicionar Sonho")
            m_nome = st.text_input("O que você quer?")
            m_val = st.number_input("Valor (R$)")
            m_data = st.date_input("Data Alvo")
            if st.form_submit_button("Criar Meta"):
                cursor.execute("INSERT INTO metas_livres (usuario, item, valor_total, data_alvo) VALUES (?,?,?,?)", (user, m_nome, m_val, str(m_data)))
                conn.commit()
                st.rerun()

    with col_lista:
        for i, r in metas_livres.iterrows():
            st.markdown(f'<div class="card-conquista"><h4>{r["item"]} (R$ {r["valor_total"]:.2f})</h4></div>', unsafe_allow_html=True)
            
            # Calendário de 7 dias
            c_dias = st.columns(7)
            hoje = date.today()
            for d in range(7):
                dia_f = hoje - timedelta(days=3-d)
                dia_s = str(dia_f)
                reg = cursor.execute("SELECT status FROM registro_diario WHERE meta_id=? AND data=?", (r['id'], dia_s)).fetchone()
                
                with c_dias[d]:
                    st.write(dia_f.strftime("%d/%m"))
                    if reg:
                        st.write("✅" if reg[0] == "VERDE" else "🔴")
                    else:
                        if st.button("Marcar", key=f"m_{r['id']}_{dia_s}"):
                            st.session_state.marcar = (r['id'], dia_s, r['item'])

            # Lógica da Mensagem Motivacional ao Marcar
            if "marcar" in st.session_state and st.session_state.marcar[0] == r['id']:
                with st.form("f_marcar"):
                    v_pago = st.number_input(f"Quanto guardou para {st.session_state.marcar[2]}?", min_value=0.0)
                    if st.form_submit_button("Confirmar"):
                        status = "VERDE" if v_pago > 0 else "VERMELHO"
                        cursor.execute("INSERT INTO registro_diario (meta_id, data, valor_pago, status) VALUES (?,?,?,?)", (r['id'], st.session_state.marcar[1], v_pago, status))
                        conn.commit()
                        
                        if status == "VERMELHO":
                            st.markdown(f'<div class="msg-motivacao">Ei {user}, não desanima! O seu sonho do(a) {st.session_state.marcar[2]} vale o esforço. Amanhã a gente volta com tudo!</div>', unsafe_allow_html=True)
                        else:
                            st.balloons()
                            st.success("Isso aí! Mais um passo rumo ao seu objetivo!")
                        
                        del st.session_state.marcar
                        # st.rerun() removido para mostrar a mensagem antes de atualizar

# --- ABA 4: AJUSTES ---
with tab_ajustes:
    st.subheader("⚙️ Configurar Veículo")
    with st.form("cfg"):
        v_k = st.number_input("KM Atual", value=200000.0)
        v_t = st.number_input("KM Troca Óleo", value=210000.0)
        v_c = st.number_input("Custo Manutenção", value=350.0)
        v_f = st.number_input("Valor FIPE", value=45000.0)
        if st.form_submit_button("Salvar"):
            cursor.execute("INSERT OR REPLACE INTO veiculo VALUES (?,?,?,?,?)", (user, v_k, v_t, v_c, v_f))
            conn.commit()
            st.rerun()
    
    if st.button("Sair do Aplicativo"):
        st.session_state.autenticado = False
        st.rerun()
