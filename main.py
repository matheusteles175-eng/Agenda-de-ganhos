import streamlit as st
import pandas as pd
import os
from datetime import date, datetime

st.set_page_config(page_title="Controle Motorista PRO", layout="wide")

# ---------------- ARQUIVO USUÁRIOS ----------------
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
                st.success("Usuário criado! Faça login")

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

    <div class="balloon" style="left:10
