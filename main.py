import streamlit as st
import pandas as pd
import os
from datetime import date, datetime

st.set_page_config(page_title="Controle Motorista PRO", layout="wide")

# ---------------- BANCO DE USUÁRIOS ----------------
arq_users = "usuarios.csv"

if os.path.exists(arq_users):
    users_df = pd.read_csv(arq_users)
else:
    users_df = pd.DataFrame(columns=["usuario","senha"])

# ---------------- LOGIN / CADASTRO ----------------
if "usuario" not in st.session_state:
    st.session_state.usuario = ""

if st.session_state.usuario == "":
    st.title("🔐 Acesso")

    aba_login, aba_cadastro = st.tabs(["Login", "Cadastrar"])

    # LOGIN
    with aba_login:
        user = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")

        if st.button("Entrar"):
            user_db = users_df[
                (users_df["usuario"] == user) &
                (users_df["senha"] == senha)
            ]

            if not user_db.empty:
                st.session_state.usuario = user
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos")

    # CADASTRO
    with aba_cadastro:
        novo_user = st.text_input("Novo usuário")
        nova_senha = st.text_input("Nova senha", type="password")

        if st.button("Cadastrar"):
            if novo_user == "" or nova_senha == "":
                st.warning("Preencha tudo")
            elif novo_user in users_df["usuario"].values:
                st.error("Usuário já existe")
            else:
                novo = pd.DataFrame([{
                    "usuario": novo_user,
                    "senha": nova_senha
                }])
                users_df = pd.concat([users_df, novo], ignore_index=True)
                users_df.to_csv(arq_users, index=False)
                st.success("Usuário criado! Agora faça login")

    st.stop()

usuario = st.session_state.usuario

# ---------------- ANIMAÇÃO ----------------
def soltar_baloes():
    st.markdown("""
    <style>
    .balloon {
        position: fixed;
        bottom: -100px;
        width: 40px;
        height: 60px;
        border-radius: 50%;
        animation: subir 6s linear;
        opacity: 0.8;
    }
    @keyframes subir {
        0% {transform: translateY(0);}
        100% {transform: translateY(-120vh);}
    }
    </style>
    <div class="balloon" style="left:10%; background:red;"></div>
    <div class="balloon" style="left:30%; background:blue;"></div>
    <div class="balloon" style="left:50%; background:green;"></div>
    <div class="balloon" style="left:70%; background:orange;"></div>
    <div class="balloon" style="left:90%; background:purple;"></div>
    """, unsafe_allow_html=True)

# ---------------- ARQUIVOS ----------------
arq_ganhos = f"ganhos_{usuario}.csv"
arq_meta = f"meta_{usuario}.csv"
arq_gastos = f"gastos_{usuario}.csv"

st.title(f"🚖 Painel de {usuario}")

# ---------------- ABAS ----------------
aba1, aba2 = st.tabs(["🚖 Ganhos", "💸 Despesas"])

# =========================================================
# ======================= GANHOS ===========================
# =========================================================
with aba1:

    st.subheader("🎯 Suas Metas")

    if os.path.exists(arq_meta):
        meta_df = pd.read_csv(arq_meta)
        meta_km = float(meta_df["km"][0])
        meta_hora = float(meta_df["hora"][0])
        meta_lucro = float(meta_df["lucro"][0])
    else:
        meta_km, meta_hora, meta_lucro = 2.0, 30.0, 100.0

    c1, c2, c3 = st.columns(3)
    meta_km = c1.number_input("Meta R$/KM", value=meta_km)
    meta_hora = c2.number_input("Meta R$/Hora", value=meta_hora)
    meta_lucro = c3.number_input("Meta de Lucro", value=meta_lucro)

    if st.button("Salvar metas"):
        pd.DataFrame([{
            "km": meta_km,
            "hora": meta_hora,
            "lucro": meta_lucro
        }]).to_csv(arq_meta, index=False)
        st.success("Metas salvas!")

    if os.path.exists(arq_ganhos):
        df = pd.read_csv(arq_ganhos)
    else:
        df = pd.DataFrame(columns=["Data","Ganho","Gasto","KM","Inicio","Fim"])

    for col in ["Ganho","Gasto","KM"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    st.subheader("📥 Lançamento do Dia")

    c1,c2,c3 = st.columns(3)
    ganho = c1.number_input("Ganho")
    gasto = c2.number_input("Gasto")
    km = c3.number_input("KM")

    inicio = st.time_input("Início")
    fim = st.time_input("Fim")

    if st.button("Salvar Dia"):
        if inicio == fim:
            st.error("Horários inválidos")
        else:
            novo = pd.DataFrame([{
                "Data": str(date.today()),
                "Ganho": ganho,
                "Gasto": gasto,
                "KM": km,
                "Inicio": inicio.strftime("%H:%M"),
                "Fim": fim.strftime("%H:%M")
            }])
            df = pd.concat([df, novo], ignore_index=True)
            df.to_csv(arq_ganhos, index=False)
            st.success("Salvo!")
            st.rerun()

    st.subheader("📊 Resultado de Hoje")

    hoje = str(date.today())
    df_hoje = df[df["Data"] == hoje
