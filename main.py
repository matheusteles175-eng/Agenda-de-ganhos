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

    # DADOS
    if os.path.exists(arq_ganhos):
        df_ganhos = pd.read_csv(arq_ganhos)
    else:
        df_ganhos = pd.DataFrame(columns=["Data","Ganho","Gasto","KM","Inicio","Fim"])

    for col in ["Ganho","Gasto","KM"]:
        df_ganhos[col] = pd.to_numeric(df_ganhos[col], errors="coerce").fillna(0)

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
            df_ganhos = pd.concat([df_ganhos, novo], ignore_index=True)
            df_ganhos.to_csv(arq_ganhos, index=False)
            st.success("Salvo!")
            st.rerun()

    st.subheader("📊 Resultado de Hoje")

    hoje = str(date.today())
    df_hoje = df_ganhos[df_ganhos["Data"] == hoje]

    if not df_hoje.empty:

        total_ganho = df_hoje["Ganho"].sum()
        total_gasto = df_hoje["Gasto"].sum()
        lucro = total_ganho - total_gasto

        if lucro >= meta_lucro:
            st.success("Meta batida! 🔥")
            st.balloons()
            soltar_baloes()
        else:
            falta = meta_lucro - lucro
            st.warning(f"Faltam R$ {falta:.2f}")

# =========================================================
# ======================= DESPESAS =========================
# =========================================================
with aba2:

    st.subheader("💸 Controle de Despesas")

    if os.path.exists(arq_gastos):
        df_gastos = pd.read_csv(arq_gastos)
    else:
        df_gastos = pd.DataFrame(columns=["Nome","Valor","Status","Vencimento"])

    nome_gasto = st.text_input("Nome da despesa")
    valor = st.number_input("Valor", min_value=0.0)
    venc = st.date_input("Vencimento")

    if st.button("Adicionar gasto"):
        if nome_gasto == "":
            st.warning("Digite o nome da despesa")
        else:
            novo = pd.DataFrame([{
                "Nome": nome_gasto,
                "Valor": valor,
                "Status": "Pendente",
                "Vencimento": venc
            }])
            df_gastos = pd.concat([df_gastos, novo], ignore_index=True)
            df_gastos.to_csv(arq_gastos, index=False)
            st.success("Gasto adicionado!")
            st.rerun()

    if not df_gastos.empty:
        st.subheader("📋 Contas")

        for i, r in df_gastos.iterrows():

            dias = (pd.to_datetime(r["Vencimento"]) - pd.to_datetime(date.today())).days

            if dias <= 0:
                por_dia = r["Valor"]
            else:
                por_dia = r["Valor"] / dias

            status_icon = "✅" if r["Status"] == "Pago" else "❌"

            c1,c2,c3,c4,c5,c6 = st.columns(6)

            c1.write(f"{status_icon} {r['Nome']}")
            c2.write(f"R$ {r['Valor']:.2f}")
            c3.write(f"{dias} dias")
            c4.write(f"R$ {por_dia:.2f}/dia")

            if r["Status"] == "Pendente":
                if c5.button("✔", key=f"p{i}"):
                    df_gastos.at[i,"Status"] = "Pago"
                    df_gastos.to_csv(arq_gastos, index=False)
                    st.rerun()

            if c6.button("🗑️", key=f"d{i}"):
                df_gastos = df_gastos.drop(i)
                df_gastos.to_csv(arq_gastos, index=False)
                st.rerun()
