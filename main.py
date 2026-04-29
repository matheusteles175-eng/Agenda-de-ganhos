import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime, timedelta

# --- 1. CONFIGURAÇÃO E ESTILO ---
st.set_page_config(page_title="Driver Pro - Conquistas", layout="wide", page_icon="🚀")

def aplicar_estilo():
    st.markdown("""
        <style>
        .main { background-color: #f0f2f6; }
        .stMetric { background-color: white; padding: 15px; border-radius: 15px; box-shadow: 0px 4px 10px rgba(0,0,0,0.05); }
        
        /* Card de Meta Estilo Caixinha */
        .card-conquista {
            background: linear-gradient(135deg, #6e8efb, #a777e3);
            padding: 25px;
            border-radius: 20px;
            color: white;
            margin-bottom: 20px;
            box-shadow: 0px 10px 20px rgba(110, 142, 251, 0.3);
        }
        
        .frase-motivacional {
            font-style: italic;
            color: #555;
            margin-bottom: 20px;
            text-align: center;
            font-size: 1.1em;
        }
        
        .sidebar-user {
            text-align: center;
            padding: 10px;
            background: #ffffff;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        </style>
    """, unsafe_allow_html=True)

aplicar_estilo()

# --- 2. BANCO DE DADOS ---
def conectar():
    conn = sqlite3.connect("driver_premium_v1.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS usuarios (usuario TEXT PRIMARY KEY, senha TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS ganhos (id INTEGER PRIMARY KEY AUTOINCREMENT, usuario TEXT, data TEXT, ganho REAL, gasto REAL, km_rodado REAL)")
    cursor.execute("CREATE TABLE IF NOT EXISTS veiculo (usuario TEXT PRIMARY KEY, km_inicial REAL, km_troca_alvo REAL, custo_estimado REAL, valor_fipe REAL)")
    cursor.execute("CREATE TABLE IF NOT EXISTS metas_livres (id INTEGER PRIMARY KEY AUTOINCREMENT, usuario TEXT, item TEXT, valor_total REAL, data_alvo TEXT)")
    conn.commit()
    return conn, cursor

conn, cursor = conectar()

# --- 3. LOGIN ---
if "autenticado" not in st.session_state: st.session_state.autenticado = False
if not st.session_state.autenticado:
    st.title("🚖 Driver Pro - Seu Futuro Começa Aqui")
    aba_l, aba_c = st.tabs(["🔑 Acessar", "📝 Começar Agora"])
    with aba_l:
        u = st.text_input("Usuário").strip().lower()
        s = st.text_input("Senha", type="password")
        if st.button("Entrar no Painel"):
            cursor.execute("SELECT * FROM usuarios WHERE usuario=? AND senha=?", (u, s))
            if cursor.fetchone():
                st.session_state.autenticado, st.session_state.user = True, u
                st.rerun()
    with aba_c:
        nu = st.text_input("Nome de Usuário").strip().lower()
        ns = st.text_input("Sua Senha", type="password")
        if st.button("Criar Minha Conta"):
            try:
                cursor.execute("INSERT INTO usuarios VALUES (?,?)", (nu, ns))
                conn.commit()
                st.success("Conta criada! Agora é só entrar.")
            except: st.error("Esse nome já está em uso.")
    st.stop()

user = st.session_state.user

# --- 4. CARREGAR DADOS ---
v_data = cursor.execute("SELECT * FROM veiculo WHERE usuario=?", (user,)).fetchone()
df_ganhos = pd.read_sql_query(f"SELECT * FROM ganhos WHERE usuario='{user}'", conn)
metas_livres = pd.read_sql_query(f"SELECT * FROM metas_livres WHERE usuario='{user}'", conn)

if v_data is None:
    st.header(f"Seja bem-vindo, {user.capitalize()}! 🚀")
    st.subheader("Para onde vamos hoje?")
    with st.form("config_v"):
        st.write("Antes de começar, me conte um pouco sobre seu carro para eu cuidar dele por você.")
        f1 = st.number_input("KM Atual do Painel:", value=200000.0)
        f2 = st.number_input("KM da Próxima Troca de Óleo:", value=210000.0)
        f3 = st.number_input("Quanto custa essa manutenção em média? (R$):", value=350.0)
        f4 = st.number_input("Qual o valor de mercado do seu carro? (R$):", value=45000.0)
        if st.form_submit_button("Configurar Tudo"):
            cursor.execute("INSERT INTO veiculo VALUES (?,?,?,?,?)", (user, f1, f2, f3, f4))
            conn.commit()
            st.rerun()
    st.stop()

km_partida, km_alvo, custo_m, valor_fipe = v_data[1], v_data[2], v_data[3], v_data[4]

# --- 5. INTERFACE DASHBOARD ---
st.title(f"Painel de Conquistas - {user.capitalize()} 🏁")
st.markdown(f'<p class="frase-motivacional">"O trabalho dignifica o homem e o planejamento realiza seus sonhos."</p>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["💰 Meus Ganhos", "🔧 Cuidado com o Carro", "🎯 Meus Sonhos", "⚙️ Configurações"])

# --- ABA 1: GANHOS ---
with tab1:
    c1, c2 = st.columns([1, 2])
    with c1:
        with st.form("f_ganho", clear_on_submit=True):
            st.subheader("📥 Registrar Jornada")
            g = st.number_input("Quanto você faturou hoje? (R$)", min_value=0.0)
            p = st.number_input("Gasto com combustível (R$)", min_value=0.0)
            k = st.number_input("Quantos KM você rodou?", min_value=0.0)
            if st.form_submit_button("Salvar Dia"):
                cursor.execute("INSERT INTO ganhos (usuario, data, ganho, gasto, km_rodado) VALUES (?,?,?,?,?)", (user, str(date.today()), g, p, k))
                conn.commit()
                st.rerun()
    with c2:
        if not df_ganhos.empty:
            km_atual_real = km_partida + df_ganhos['km_rodado'].sum()
            st.metric("Seu Carro está com", f"{km_atual_real:.0f} km")
            st.write("### Seu desempenho nos últimos dias")
            st.area_chart(df_ganhos.tail(10).set_index('data')['ganho'])

# --- ABA 2: MANUTENÇÃO E IPVA ---
with tab2:
    st.subheader("🛡️ Proteja seu instrumento de trabalho")
    col_m, col_i = st.columns(2)
    with col_m:
        km_atual = km_partida + df_ganhos['km_rodado'].sum()
        resta = km_alvo - km_atual
        st.metric("KM para Troca de Óleo", f"{resta:.0f} km")
        if resta <= 1000:
            st.error(f"⚠️ Atenção {user.capitalize()}, a manutenção está próxima!")
        
    with col_i:
        v_ipva = valor_fipe * 0.04
        st.metric("Previsão IPVA (SP)", f"R$ {v_ipva:.2f}")
        st.info("💡 Pagar o IPVA à vista garante desconto. Comece a guardar agora!")

# --- ABA 3: METAS E SONHOS (A PARTE QUE VOCÊ PEDIU) ---
with tab3:
    st.header("🎯 Qual o seu próximo objetivo?")
    st.write("Não trabalhe apenas para pagar contas. Trabalhe para conquistar seus bens!")
    
    col_add, col_list = st.columns([1, 2])
    
    with col_add:
        st.markdown("""
        <div style="background-color: white; padding: 20px; border-radius: 15px; border: 1px solid #ddd;">
            <strong>✨ Adicionar Novo Sonho</strong><br><br>
        """, unsafe_allow_html=True)
        with st.form("meta_livre", clear_on_submit=True):
            m_item = st.text_input("O que você quer conquistar?", placeholder="Ex: Moto Nova, Pneus, Viagem...")
            m_valor = st.number_input("Quanto custa esse sonho? (R$)", min_value=0.0)
            m_data = st.date_input("Até quando quer realizar?")
            if st.form_submit_button("Criar Minha Caixinha"):
                cursor.execute("INSERT INTO metas_livres (usuario, item, valor_total, data_alvo) VALUES (?,?,?,?)", (user, m_item, m_valor, str(m_data)))
                conn.commit()
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col_list:
        if not metas_livres.empty:
            for i, r in metas_livres.iterrows():
                d_alvo = datetime.strptime(r['data_alvo'], "%Y-%m-%d").date()
                dias_rest = (d_alvo - date.today()).days
                dias_rest = max(1, dias_rest)
                v_diario = r['valor_total'] / dias_rest
                
                st.markdown(f"""
                <div class="card-conquista">
                    <span style="font-size: 1.5em;">🚀 {r['item'].upper()}</span><br>
                    <hr style="border: 0.5px solid rgba(255,255,255,0.3)">
                    <span style="font-size: 1.1em;">Valor do Objetivo: <b>R$ {r['valor_total']:.2f}</b></span><br>
                    <span>Faltam <b>{dias_rest} dias</b> para você conquistar!</span><br><br>
                    <div style="background: rgba(255,255,255,0.2); padding: 10px; border-radius: 10px; text-align: center;">
                        <span style="font-size: 1.2em;">👉 Guarde <b>R$ {v_diario:.2f} por dia</b></span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"Concluí esta meta! ✅", key=f"btn_{r['id']}"):
                    cursor.execute("DELETE FROM metas_livres WHERE id=?", (r['id'],))
                    conn.commit()
                    st.rerun()
        else:
            st.info("Use o formulário ao lado para cadastrar seu primeiro sonho. Vamos juntos realizar!")

# --- ABA 4: AJUSTES ---
with tab4:
    st.subheader("⚙️ Configurações Gerais")
    if st.button("🚪 Sair do Sistema"):
        st.session_state.autenticado = False
        st.rerun()
    
    with st.expander("🔄 Atualizar Carro ou FIPE"):
        with st.form("reset"):
            u_f = st.number_input("Valor FIPE do Veículo", value=float(valor_fipe))
            u_k = st.number_input("KM Atual do Painel", value=float(km_partida + df_ganhos['km_rodado'].sum()))
            u_t = st.number_input("KM Próxima Troca de Óleo", value=float(km_alvo))
            u_c = st.number_input("Custo Médio da Troca", value=float(custo_m))
            if st.form_submit_button("Atualizar Tudo"):
                cursor.execute("UPDATE veiculo SET km_inicial=?, km_troca_alvo=?, custo_estimado=?, valor_fipe=? WHERE usuario=?", (u_k, u_t, u_c, u_f, user))
                cursor.execute("DELETE FROM ganhos WHERE usuario=?", (user,))
                conn.commit()
                st.rerun()
