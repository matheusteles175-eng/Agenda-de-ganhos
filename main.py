import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime, timedelta

# --- 1. CONFIGURAÇÃO E ESTILO ---
st.set_page_config(page_title="Driver Pro Inteligente", layout="wide", page_icon="🚖")

def aplicar_estilo():
    st.markdown("""
        <style>
        .main { background-color: #f5f7f9; }
        .stMetric { background-color: white; padding: 15px; border-radius: 10px; box-shadow: 2px 2px 10px rgba(0,0,0,0.05); }
        .metric-card {
            background-color: white;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
            border-left: 5px solid #1E88E5;
        }
        .alerta-manutencao {
            padding: 20px;
            border-radius: 15px;
            color: white;
            margin-bottom: 20px;
            font-weight: bold;
        }
        </style>
    """, unsafe_allow_html=True)

aplicar_estilo()

# --- 2. BANCO DE DADOS UNIFICADO ---
def conectar():
    conn = sqlite3.connect("driver_completo.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS usuarios (usuario TEXT PRIMARY KEY, senha TEXT)")
    cursor.execute("""CREATE TABLE IF NOT EXISTS ganhos (
        id INTEGER PRIMARY KEY AUTOINCREMENT, usuario TEXT, data TEXT, 
        ganho REAL, gasto REAL, km_rodado REAL, inicio TEXT, fim TEXT)""")
    cursor.execute("CREATE TABLE IF NOT EXISTS metas (usuario TEXT PRIMARY KEY, km_alvo REAL, hora_alvo REAL, lucro_alvo REAL)")
    cursor.execute("""CREATE TABLE IF NOT EXISTS veiculo (
        usuario TEXT PRIMARY KEY, km_inicial REAL, km_troca_alvo REAL, custo_estimado REAL)""")
    conn.commit()
    return conn, cursor

conn, cursor = conectar()

# --- 3. SISTEMA DE LOGIN ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.title("🚖 Driver Pro - Acesso")
    aba_l, aba_c = st.tabs(["🔑 Login", "📝 Cadastro"])
    with aba_l:
        with st.form("l"):
            u = st.text_input("Usuário").strip().lower()
            s = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar"):
                cursor.execute("SELECT * FROM usuarios WHERE usuario=? AND senha=?", (u, s))
                if cursor.fetchone():
                    st.session_state.autenticado = True
                    st.session_state.user = u
                    st.rerun()
                else: st.error("Dados incorretos.")
    with aba_c:
        with st.form("c"):
            nu = st.text_input("Novo Usuário").strip().lower()
            ns = st.text_input("Senha").strip()
            if st.form_submit_button("Cadastrar"):
                try:
                    cursor.execute("INSERT INTO usuarios VALUES (?,?)", (nu, ns))
                    conn.commit()
                    st.success("Cadastrado! Faça login.")
                except: st.error("Usuário já existe.")
    st.stop()

user = st.session_state.user

# --- 4. CARREGAMENTO DE DADOS E INTELIGÊNCIA ---
# Buscar dados do veículo
v_data = cursor.execute("SELECT * FROM veiculo WHERE usuario=?", (user,)).fetchone()
km_partida = v_data[1] if v_data else 204624.0
km_proxima_troca = v_data[2] if v_data else 206600.0
custo_previsto = v_data[3] if v_data else 300.0

# Buscar histórico de ganhos para somar KM
df_ganhos = pd.read_sql_query(f"SELECT * FROM ganhos WHERE usuario='{user}'", conn)
total_rodado_no_app = df_ganhos['km_rodado'].sum() if not df_ganhos.empty else 0
km_atual_calculado = km_partida + total_rodado_no_app
km_restante = km_proxima_troca - km_atual_calculado

# --- 5. BARRA LATERAL ---
with st.sidebar:
    st.markdown(f"### Olá, **{user.upper()}**!")
    if st.button("Sair"):
        st.session_state.autenticado = False
        st.rerun()
    
    st.divider()
    st.subheader("⚙️ Configuração do Carro")
    new_km_partida = st.number_input("KM Inicial (O que está no painel hoje)", value=float(km_partida))
    new_km_troca = st.number_input("Trocar com (KM)", value=float(km_proxima_troca))
    new_custo = st.number_input("Custo Estimado Manutenção (R$)", value=float(custo_previsto))
    if st.button("Atualizar Carro"):
        cursor.execute("INSERT OR REPLACE INTO veiculo VALUES (?,?,?,?)", (user, new_km_partida, new_km_troca, new_custo))
        conn.commit()
        st.rerun()

# --- 6. PAINEL PRINCIPAL ---
st.title("🏁 Driver Pro Inteligente")

# ALERTAS CRÍTICOS NO TOPO
if km_restante <= 1000:
    cor = "#EF6C00" if km_restante > 300 else "#C62828"
    st.markdown(f"""
        <div class="alerta-manutencao" style="background-color: {cor};">
            🚨 ATENÇÃO MATEUS: Faltam {km_restante:.0f} KM para sua manutenção!<br>
            Prepare R$ {custo_previsto:.2f} para a troca de óleo e filtros.
        </div>
    """, unsafe_allow_html=True)

tab_ganhos, tab_manutencao, tab_historico = st.tabs(["💰 Ganhos & Metas", "🔧 Inteligência Mecânica", "📋 Histórico"])

with tab_ganhos:
    col_input, col_stats = st.columns([1, 2])
    
    with col_input:
        st.markdown("<div class='metric-card'><h4>📝 Lançar Dia</h4></div>", unsafe_allow_html=True)
        with st.form("f_dia", clear_on_submit=True):
            d_data = st.date_input("Data", date.today())
            d_ganho = st.number_input("Ganho Total (R$)", step=10.0)
            d_gasto = st.number_input("Combustível (R$)", step=5.0)
            d_km = st.number_input("KM Rodados Hoje", step=1.0)
            if st.form_submit_button("Salvar Dia"):
                cursor.execute("INSERT INTO ganhos (usuario, data, ganho, gasto, km_rodado, inicio, fim) VALUES (?,?,?,?,?,?,?)",
                               (user, str(d_data), d_ganho, d_gasto, d_km, "08:00", "17:00"))
                conn.commit()
                st.rerun()

    with col_stats:
        if not df_ganhos.empty:
            df_ganhos['lucro'] = df_ganhos['ganho'] - df_ganhos['gasto']
            l_total = df_ganhos['lucro'].sum()
            
            c1, c2, c3 = st.columns(3)
            c1.metric("KM Atual do Carro", f"{km_atual_calculado:.0f} km")
            c2.metric("Lucro Acumulado", f"R$ {l_total:.2f}")
            c3.metric("Falta p/ Manutenção", f"{km_restante:.0f} km")
            
            st.write("### Evolução Diária")
            st.line_chart(df_ganhos.tail(10).set_index('data')['lucro'])
        else: st.info("Lance seu primeiro dia para ver as estatísticas!")

with tab_manutencao:
    st.header("🧠 Assistente de Manutenção Inteligente")
    if not df_ganhos.empty:
        # Lógica de Inteligência de Dados
        media_km_dia = df_ganhos['km_rodado'].mean()
        media_lucro_dia = df_ganhos['lucro'].mean()
        
        # Quantos dias faltam?
        dias_restantes = km_restante / media_km_dia if media_km_dia > 0 else 0
        reserva_sugerida = custo_previsto / dias_restantes if dias_restantes > 1 else custo_previsto
        
        c_a, c_b = st.columns(2)
        with c_a:
            st.subheader("Estimativa de Tempo")
            st.info(f"Você roda em média **{media_km_dia:.1f} KM/dia**.")
            st.warning(f"Nesse ritmo, você atingirá o limite da manutenção em **{dias_restantes:.0f} dias**.")
        
        with c_b:
            st.subheader("Planejamento Financeiro")
            st.success(f"Sugestão: Guarde **R$ {reserva_sugerida:.2f}** por dia.")
            st.write(f"Isso é apenas {((reserva_sugerida/media_lucro_dia)*100):.1f}% do seu lucro diário médio.")
            
        st.progress(max(0, min(1.0, 1 - (km_restante/2000)))) # Barra de progresso baseada nos últimos 2000km
    else:
        st.write("Aguardando dados suficientes para calcular médias...")

with tab_historico:
    st.subheader("Todos os Lançamentos")
    if not df_ganhos.empty:
        st.dataframe(df_ganhos[['id', 'data', 'ganho', 'gasto', 'km_rodado', 'lucro']], use_container_width=True)
        id_del = st.number_input("ID para excluir", min_value=1, step=1)
        if st.button("🗑️ Excluir"):
            cursor.execute("DELETE FROM ganhos WHERE id=? AND usuario=?", (id_del, user))
            conn.commit()
            st.rerun()
