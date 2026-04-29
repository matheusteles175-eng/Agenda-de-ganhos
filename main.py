import streamlit as st
import sqlite3
import pandas as pd
import random
from datetime import date, datetime, timedelta

# --- Estilos e Animações ---
st.set_page_config(page_title="Freedom Pro - Foco Total", layout="wide")

def aplicar_estilo():
    st.markdown("""
        <style>
        .stMetric { background-color: #ffffff; padding: 15px; border-radius: 15px; border-bottom: 4px solid #1e3c72; }
        .card-meta { background: #ffffff; padding: 20px; border-radius: 15px; border-left: 8px solid #6e8efb; margin-bottom: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .msg-motivacao { padding: 15px; border-radius: 10px; background-color: #fff3cd; color: #856404; font-weight: bold; border-left: 5px solid #ffeeba; }
        </style>
    """, unsafe_allow_html=True)

aplicar_estilo()

# --- Banco de Dados ---
def conectar():
    conn = sqlite3.connect("freedom_v7.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS metas_livres (id INTEGER PRIMARY KEY, usuario TEXT, item TEXT, valor_total REAL, data_alvo TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS registro_diario (id INTEGER PRIMARY KEY, meta_id INTEGER, data TEXT, valor_pago REAL, status TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS veiculo (usuario TEXT PRIMARY KEY, valor_fipe REAL)")
    conn.commit()
    return conn, cursor

conn, cursor = conectar()
user = "Mateus" # Pegando do login anterior

# --- Lógica IPVA São Paulo ---
def modulo_ipva():
    st.subheader("📄 Gestão de IPVA (Padrão SP - 4%)")
    v_data = cursor.execute("SELECT valor_fipe FROM veiculo WHERE usuario=?", (user,)).fetchone()
    
    if v_data:
        valor_fipe = v_data[0]
        valor_ipva = valor_fipe * 0.04
        
        # Cálculo de tempo até Janeiro (Vencimento padrão SP)
        hoje = date.today()
        vencimento = date(hoje.year + (1 if hoje.month > 1 else 0), 1, 15) # Estimativa dia 15/Jan
        meses_faltam = (vencimento.year - hoje.year) * 12 + (vencimento.month - hoje.month)
        meses_faltam = max(1, meses_faltam)
        reserva_mensal = valor_ipva / meses_restantes if 'meses_restantes' in locals() else valor_ipva / meses_faltam

        col1, col2, col3 = st.columns(3)
        col1.metric("Valor Total IPVA", f"R$ {valor_ipva:.2f}")
        col2.metric("Meses para o Vencimento", f"{meses_faltam} Meses")
        col3.metric("Reserva Mensal Sugerida", f"R$ {reserva_mensal:.2f}")
        
        st.info(f"💡 {user}, para pagar seu IPVA de R$ {valor_ipva:.2f} à vista em Janeiro, guarde R$ {reserva_mensal:.2f} todo mês.")
    else:
        st.warning("Configure o valor do seu veículo em 'Ajustes' para calcular o IPVA.")

# --- Lógica de Metas e Disciplina ---
def modulo_metas():
    st.header("🎯 Suas Metas de Vida")
    metas = pd.read_sql_query(f"SELECT * FROM metas_livres WHERE usuario='{user}'", conn)
    
    for _, meta in metas.iterrows():
        with st.container():
            st.markdown(f'<div class="card-meta"><h3>{meta["item"]}</h3></div>', unsafe_allow_html=True)
            
            # Calendário interativo de 7 dias
            cols = st.columns(7)
            hoje = date.today()
            for i in range(7):
                dia = hoje - timedelta(days=3-i)
                dia_str = str(dia)
                
                # Checar status no banco
                reg = cursor.execute("SELECT status, valor_pago FROM registro_diario WHERE meta_id=? AND data=?", (meta['id'], dia_str)).fetchone()
                
                with cols[i]:
                    st.write(dia.strftime("%d/%m"))
                    if reg:
                        if reg[0] == 'VERDE': st.success("✅")
                        else: st.error("🔴")
                    else:
                        if st.button("Marcar", key=f"m_{meta['id']}_{dia_str}"):
                            st.session_state.temp_meta = (meta['id'], dia_str)

            # Se clicou para marcar
            if "temp_meta" in st.session_state and st.session_state.temp_meta[0] == meta['id']:
                with st.form("confirm_dia"):
                    val = st.number_input("Quanto guardou hoje? (Digite 0 se não guardou)", min_value=0.0)
                    if st.form_submit_button("Registrar"):
                        status = "VERDE" if val > 0 else "VERMELHO"
                        cursor.execute("INSERT INTO registro_diario (meta_id, data, valor_pago, status) VALUES (?,?,?,?)", 
                                       (meta['id'], st.session_state.temp_meta[1], val, status))
                        conn.commit()
                        
                        # MENSAGENS MOTIVACIONAIS
                        if status == "VERMELHO":
                            st.warning(f"Ei {user}, não desanima! Às vezes o dia é corrido, mas amanhã a gente vai pra cima com tudo. Seu sonho de comprar o(a) {meta['item']} está em jogo, não desiste!")
                        else:
                            st.success(f"ISSO AÍ! Cada real conta. Você está mais perto do seu objetivo!")
                        
                        del st.session_state.temp_meta
                        st.rerun()

# --- Execução ---
modulo_ipva()
st.write("---")
modulo_metas()
