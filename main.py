import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime

st.set_page_config(page_title="Controle Motorista PRO", layout="wide")

# ================= BANCO =================
conn = sqlite3.connect("app.db", check_same_thread=False)
cursor = conn.cursor()

# CRIA TABELAS AUTOMATICAMENTE
cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    usuario TEXT PRIMARY KEY,
    senha TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS ganhos (
    usuario TEXT,
    data TEXT,
    ganho REAL,
    gasto REAL,
    km REAL,
    inicio TEXT,
    fim TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS metas (
    usuario TEXT,
    km REAL,
    hora REAL,
    lucro REAL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS gastos (
    usuario TEXT,
    nome TEXT,
    valor REAL,
    status TEXT,
    vencimento TEXT
)
""")

conn.commit()

# ================= LOGIN =================
if "usuario" not in st.session_state:
    st.session_state.usuario = ""

if st.session_state.usuario == "":
    st.title("🔐 Acesso")

    aba_login, aba_cadastro = st.tabs(["Login", "Cadastrar"])

    # LOGIN
    with aba_login:
        user = st.text_input("Usuário").strip().lower()
        senha = st.text_input("Senha", type="password")

        if st.button("Entrar"):
            cursor.execute("SELECT * FROM usuarios WHERE usuario=? AND senha=?", (user, senha))
            if cursor.fetchone():
                st.session_state.usuario = user
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos")

    # CADASTRO
    with aba_cadastro:
        novo_user = st.text_input("Novo usuário").strip().lower()
        nova_senha = st.text_input("Nova senha", type="password")

        if st.button("Cadastrar"):
            try:
                cursor.execute("INSERT INTO usuarios VALUES (?,?)", (novo_user, nova_senha))
                conn.commit()
                st.success("Usuário criado!")
                st.rerun()
            except:
                st.error("Usuário já existe")

    st.stop()

usuario = st.session_state.usuario

# ================= ANIMAÇÃO =================
def soltar_baloes():
    st.balloons()

st.title(f"🚖 Painel de {usuario}")

aba1, aba2 = st.tabs(["🚖 Ganhos", "💸 Despesas"])

# ================= GANHOS =================
with aba1:

    st.subheader("🎯 Metas")

    cursor.execute("SELECT km, hora, lucro FROM metas WHERE usuario=?", (usuario,))
    meta = cursor.fetchone()

    if meta:
        meta_km, meta_hora, meta_lucro = meta
    else:
        meta_km, meta_hora, meta_lucro = 2.0, 30.0, 100.0

    c1,c2,c3 = st.columns(3)
    meta_km = c1.number_input("R$/KM", value=float(meta_km))
    meta_hora = c2.number_input("R$/Hora", value=float(meta_hora))
    meta_lucro = c3.number_input("Meta Lucro", value=float(meta_lucro))

    if st.button("Salvar metas"):
        cursor.execute("DELETE FROM metas WHERE usuario=?", (usuario,))
        cursor.execute("INSERT INTO metas VALUES (?,?,?,?)", (usuario, meta_km, meta_hora, meta_lucro))
        conn.commit()
        st.success("Metas salvas")

    st.subheader("📥 Lançamento")

    c1,c2,c3 = st.columns(3)
    ganho = c1.number_input("Ganho")
    gasto = c2.number_input("Gasto")
    km = c3.number_input("KM")

    inicio = st.time_input("Início")
    fim = st.time_input("Fim")

    if st.button("Salvar Dia"):
        cursor.execute("INSERT INTO ganhos VALUES (?,?,?,?,?,?,?)", (
            usuario,
            str(date.today()),
            ganho,
            gasto,
            km,
            inicio.strftime("%H:%M"),
            fim.strftime("%H:%M")
        ))
        conn.commit()
        st.rerun()

    st.subheader("📊 Hoje")

    df = pd.read_sql_query(f"SELECT * FROM ganhos WHERE usuario='{usuario}'", conn)
    hoje = str(date.today())
    df_hoje = df[df["data"] == hoje]

    if not df_hoje.empty:
        lucro = df_hoje["ganho"].sum() - df_hoje["gasto"].sum()

        if lucro >= meta_lucro:
            st.success("Meta batida!")
            soltar_baloes()
        else:
            st.warning(f"Faltam R$ {meta_lucro - lucro:.2f}")

# ================= DESPESAS =================
with aba2:

    st.subheader("💸 Despesas")

    nome = st.text_input("Nome da despesa")
    valor = st.number_input("Valor", min_value=0.0)
    venc = st.date_input("Vencimento")

    if st.button("Adicionar"):
        cursor.execute("INSERT INTO gastos VALUES (?,?,?,?,?)", (
            usuario, nome, valor, "Pendente", str(venc)
        ))
        conn.commit()
        st.rerun()

    df = pd.read_sql_query(f"SELECT rowid, * FROM gastos WHERE usuario='{usuario}'", conn)

    if not df.empty:
        for _, r in df.iterrows():

            dias = (pd.to_datetime(r["vencimento"]) - pd.to_datetime(date.today())).days
            por_dia = r["valor"] if dias <= 0 else r["valor"]/dias

            status = "✅" if r["status"] == "Pago" else "❌"

            c1,c2,c3,c4,c5,c6 = st.columns(6)

            c1.write(f"{status} {r['nome']}")
            c2.write(f"R$ {r['valor']:.2f}")
            c3.write(f"{dias} dias")
            c4.write(f"{por_dia:.2f}/dia")

            if r["status"] == "Pendente":
                if c5.button("✔", key=f"p{r['rowid']}"):
                    cursor.execute("UPDATE gastos SET status='Pago' WHERE rowid=?", (r["rowid"],))
                    conn.commit()
                    st.rerun()

            if c6.button("🗑️", key=f"d{r['rowid']}"):
                cursor.execute("DELETE FROM gastos WHERE rowid=?", (r["rowid"],))
                conn.commit()
                st.rerun()
