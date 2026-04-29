import streamlit as st
import pandas as pd
import os
from datetime import date, time, datetime

st.set_page_config(page_title="Sistema Completo 🚖💸", layout="wide")

ARQUIVO_USUARIOS = "usuarios.csv"

# ---------------- USUÁRIOS ----------------
def carregar_usuarios():
    if os.path.exists(ARQUIVO_USUARIOS):
        return pd.read_csv(ARQUIVO_USUARIOS, dtype=str)
    else:
        df = pd.DataFrame([{"usuario": "matheus", "senha": "123"}])
        df.to_csv(ARQUIVO_USUARIOS, index=False)
        return df

if "logado" not in st.session_state:
    st.session_state.logado = False
if "usuario_atual" not in st.session_state:
    st.session_state.usuario_atual = ""

# ---------------- LOGIN ----------------
def tela_acesso():
    st.title("🚖 Sistema do Motorista")

    aba1, aba2 = st.tabs(["Entrar", "Criar Conta"])
    df_usuarios = carregar_usuarios()

    with aba1:
        u = st.text_input("Usuário").lower()
        s = st.text_input("Senha", type="password")

        if st.button("Entrar"):
            user = df_usuarios[(df_usuarios['usuario'].str.lower() == u) & (df_usuarios['senha'] == s)]
            if not user.empty:
                st.session_state.logado = True
                st.session_state.usuario_atual = u
                st.rerun()
            else:
                st.error("Login inválido")

    with aba2:
        nu = st.text_input("Novo usuário").lower()
        ns = st.text_input("Senha nova", type="password")

        if st.button("Criar conta"):
            if nu in df_usuarios['usuario'].values:
                st.error("Usuário já existe")
            else:
                df = pd.concat([df_usuarios, pd.DataFrame([{"usuario": nu, "senha": ns}])])
                df.to_csv(ARQUIVO_USUARIOS, index=False)
                st.success("Conta criada!")

# ---------------- APP ----------------
if st.session_state.logado:

    user = st.session_state.usuario_atual
    arq_dados = f"dados_{user}.csv"
    arq_gastos = f"gastos_{user}.csv"

    st.sidebar.write(f"👤 {user}")
    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.rerun()

    aba1, aba2 = st.tabs(["🚖 Ganhos", "💸 Gastos"])

    # ================= GANHOS =================
    with aba1:
        st.title("🚖 Controle de Ganhos")

        if os.path.exists(arq_dados):
            df = pd.read_csv(arq_dados)
        else:
            df = pd.DataFrame(columns=["Data","Ganho","Gasto","KM","H_Inicio","H_Fim"])

        col1, col2, col3 = st.columns(3)
        ganho = col1.number_input("Ganho")
        gasto = col2.number_input("Gasto")
        km = col3.number_input("KM")

        hi = st.time_input("Início")
        hf = st.time_input("Fim")

        if st.button("Salvar ganho"):
            nova = pd.DataFrame([{
                "Data": date.today(),
                "Ganho": ganho,
                "Gasto": gasto,
                "KM": km,
                "H_Inicio": hi,
                "H_Fim": hf
            }])
            df = pd.concat([df, nova])
            df.to_csv(arq_dados, index=False)
            st.success("Salvo!")

        if not df.empty:
            total = df["Ganho"].sum()
            gasto_total = df["Gasto"].sum()
            lucro = total - gasto_total

            st.metric("💰 Lucro Total", f"R$ {lucro:.2f}")
            st.line_chart(df["Ganho"])

    # ================= GASTOS =================
    with aba2:
        st.title("💸 Controle de Gastos Inteligente")

        if os.path.exists(arq_gastos):
            df = pd.read_csv(arq_gastos)
        else:
            df = pd.DataFrame(columns=["Data","Categoria","Valor","Descricao","Status","Vencimento"])

        categorias = ["Comida","Luz","Água","Internet","Dívidas","Transporte","Outros"]

        cat = st.selectbox("Categoria", categorias)
        val = st.number_input("Valor", min_value=0.0)
        desc = st.text_input("Descrição")
        venc = st.date_input("Data de vencimento")

        if st.button("Adicionar gasto"):
            novo = pd.DataFrame([{
                "Data": date.today(),
                "Categoria": cat,
                "Valor": val,
                "Descricao": desc,
                "Status": "Pendente",
                "Vencimento": venc
            }])
            df = pd.concat([df, novo])
            df.to_csv(arq_gastos, index=False)
            st.success("Adicionado!")

        if not df.empty:
            df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0)

            total = df["Valor"].sum()
            pago = df[df["Status"]=="Pago"]["Valor"].sum()
            pendente = df[df["Status"]=="Pendente"]["Valor"].sum()

            c1,c2,c3 = st.columns(3)
            c1.metric("Total", total)
            c2.metric("Pago", pago)
            c3.metric("Pendente", pendente)

            st.bar_chart(df.groupby("Categoria")["Valor"].sum())

            st.subheader("📋 Lista de contas")

            for i,row in df.iterrows():
                dias = (pd.to_datetime(row["Vencimento"]) - pd.to_datetime(date.today())).days

                if dias > 0:
                    por_dia = row["Valor"] / dias
                else:
                    por_dia = row["Valor"]

                col1,col2,col3,col4,col5 = st.columns(5)

                col1.write(row["Categoria"])
                col2.write(f"R$ {row['Valor']}")
                col3.write(row["Status"])
                col4.write(f"{dias} dias | R$ {por_dia:.2f}/dia")

                if row["Status"] == "Pendente":
                    if col5.button("Pagar", key=f"p{i}"):
                        df.at[i,"Status"] = "Pago"
                        df.to_csv(arq_gastos, index=False)
                        st.rerun()

                if col5.button("❌", key=f"d{i}"):
                    df = df.drop(i)
                    df.to_csv(arq_gastos, index=False)
                    st.rerun()

else:
    tela_acesso()
