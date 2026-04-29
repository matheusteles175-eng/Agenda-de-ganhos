import streamlit as st
import pandas as pd
import os
from datetime import date, datetime

st.set_page_config(page_title="Sistema Profissional 🚖💸", layout="wide")

ARQ_USERS = "usuarios.csv"

# ---------------- USUÁRIOS ----------------
def carregar_users():
    if os.path.exists(ARQ_USERS):
        return pd.read_csv(ARQ_USERS, dtype=str)
    else:
        df = pd.DataFrame([{"usuario":"admin","senha":"123"}])
        df.to_csv(ARQ_USERS, index=False)
        return df

if "logado" not in st.session_state:
    st.session_state.logado = False
if "user" not in st.session_state:
    st.session_state.user = ""

# ---------------- LOGIN ----------------
def tela_login():
    st.title("🚖 Sistema do Motorista PRO")

    aba1, aba2 = st.tabs(["Entrar","Criar Conta"])
    df = carregar_users()

    with aba1:
        u = st.text_input("Usuário").lower()
        s = st.text_input("Senha", type="password")

        if st.button("Entrar"):
            user = df[(df["usuario"].str.lower()==u) & (df["senha"]==s)]
            if not user.empty:
                st.session_state.logado = True
                st.session_state.user = u
                st.rerun()
            else:
                st.error("Login inválido")

    with aba2:
        nu = st.text_input("Novo usuário").lower()
        ns = st.text_input("Nova senha", type="password")

        if st.button("Criar conta"):
            if nu in df["usuario"].values:
                st.error("Usuário já existe")
            else:
                df = pd.concat([df, pd.DataFrame([{"usuario":nu,"senha":ns}])])
                df.to_csv(ARQ_USERS, index=False)
                st.success("Conta criada!")

# ---------------- APP ----------------
if st.session_state.logado:

    user = st.session_state.user
    arq_ganhos = f"ganhos_{user}.csv"
    arq_gastos = f"gastos_{user}.csv"

    st.sidebar.write(f"👤 {user}")
    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.rerun()

    aba1, aba2 = st.tabs(["🚖 Ganhos","💸 Gastos"])

    # ================= GANHOS =================
    with aba1:
        st.title("🚖 Controle Profissional de Ganhos")

        if os.path.exists(arq_ganhos):
            df = pd.read_csv(arq_ganhos)
        else:
            df = pd.DataFrame(columns=["Data","Ganho","Gasto","KM","Inicio","Fim"])

        for col in ["Ganho","Gasto","KM"]:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        # INPUT
        c1,c2,c3 = st.columns(3)
        ganho = c1.number_input("💰 Ganho")
        gasto = c2.number_input("💸 Gasto")
        km = c3.number_input("🚗 KM")

        inicio = st.time_input("Início")
        fim = st.time_input("Fim")

        if st.button("Salvar ganho"):
            novo = pd.DataFrame([{
                "Data":date.today(),
                "Ganho":ganho,
                "Gasto":gasto,
                "KM":km,
                "Inicio":inicio.strftime("%H:%M"),
                "Fim":fim.strftime("%H:%M")
            }])
            df = pd.concat([df,novo])
            df.to_csv(arq_ganhos,index=False)
            st.rerun()

        if not df.empty:

            total_ganho = df["Ganho"].sum()
            total_gasto = df["Gasto"].sum()
            lucro = total_ganho - total_gasto
            total_km = df["KM"].sum()

            # horas
            horas = 0
            for _,r in df.iterrows():
                try:
                    t1 = datetime.strptime(r["Inicio"], "%H:%M")
                    t2 = datetime.strptime(r["Fim"], "%H:%M")
                    diff = (t2 - t1).total_seconds()/3600
                    if diff < 0:
                        diff += 24
                    horas += diff
                except:
                    pass

            valor_km = total_ganho/total_km if total_km>0 else 0
            valor_hora = total_ganho/horas if horas>0 else 0

            # METAS
            st.subheader("🎯 Metas")
            m1,m2,m3 = st.columns(3)
            meta_km = m1.number_input("Meta R$/KM",value=2.0)
            meta_hora = m2.number_input("Meta R$/Hora",value=30.0)
            meta_lucro = m3.number_input("Meta Lucro",value=100.0)

            # DASHBOARD
            d1,d2,d3,d4 = st.columns(4)
            d1.metric("💰 Total",f"R$ {total_ganho:.2f}")
            d2.metric("💸 Gasto",f"R$ {total_gasto:.2f}")
            d3.metric("📈 Lucro",f"R$ {lucro:.2f}")
            d4.metric("🚗 KM",f"{total_km:.1f}")

            d5,d6 = st.columns(2)
            d5.metric("💵 R$/KM",f"{valor_km:.2f}")
            d6.metric("⏱️ R$/Hora",f"{valor_hora:.2f}")

            # FRASES
            if valor_km >= meta_km and valor_hora >= meta_hora and lucro >= meta_lucro:
                frase = "🚀 Você está operando como um profissional de alta performance!"
            elif lucro < meta_lucro:
                frase = "🔥 Hoje foi treino. Ajuste e volte mais forte amanhã."
            else:
                frase = "📈 Você está evoluindo. Continue consistente."

            st.success(frase)

            st.line_chart(df["Ganho"])

            # HISTÓRICO
            st.subheader("Histórico")
            for i,r in df.iloc[::-1].iterrows():
                c1,c2,c3,c4 = st.columns([2,2,2,1])
                c1.write(r["Data"])
                c2.write(f"R$ {r['Ganho']} / R$ {r['Gasto']}")
                c3.write(f"Lucro: R$ {r['Ganho']-r['Gasto']:.2f}")

                if c4.button("🗑️",key=f"del{i}"):
                    df = df.drop(i)
                    df.to_csv(arq_ganhos,index=False)
                    st.rerun()

    # ================= GASTOS =================
    with aba2:
        st.title("💸 Controle de Dívidas")

        if os.path.exists(arq_gastos):
            df = pd.read_csv(arq_gastos)
        else:
            df = pd.DataFrame(columns=["Categoria","Valor","Status","Vencimento"])

        cat = st.selectbox("Categoria",["Comida","Luz","Água","Internet","Dívida","Outros"])
        val = st.number_input("Valor",min_value=0.0)
        venc = st.date_input("Vencimento")

        if st.button("Adicionar gasto"):
            novo = pd.DataFrame([{
                "Categoria":cat,
                "Valor":val,
                "Status":"Pendente",
                "Vencimento":venc
            }])
            df = pd.concat([df,novo])
            df.to_csv(arq_gastos,index=False)
            st.rerun()

        if not df.empty:
            df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0)

            total = df["Valor"].sum()
            pago = df[df["Status"]=="Pago"]["Valor"].sum()
            pendente = df[df["Status"]=="Pendente"]["Valor"].sum()

            c1,c2,c3 = st.columns(3)
            c1.metric("Total",total)
            c2.metric("Pago",pago)
            c3.metric("Pendente",pendente)

            st.bar_chart(df.groupby("Categoria")["Valor"].sum())

            st.subheader("Contas")

            for i,r in df.iterrows():
                dias = (pd.to_datetime(r["Vencimento"]) - pd.to_datetime(date.today())).days
                por_dia = r["Valor"]/dias if dias>0 else r["Valor"]

                c1,c2,c3,c4,c5 = st.columns(5)
                c1.write(r["Categoria"])
                c2.write(f"R$ {r['Valor']}")
                c3.write(r["Status"])
                c4.write(f"{dias} dias | R$ {por_dia:.2f}/dia")

                if r["Status"]=="Pendente":
                    if c5.button("Pagar",key=f"p{i}"):
                        df.at[i,"Status"]="Pago"
                        df.to_csv(arq_gastos,index=False)
                        st.rerun()

                if c5.button("❌",key=f"d{i}"):
                    df = df.drop(i)
                    df.to_csv(arq_gastos,index=False)
                    st.rerun()

else:
    tela_login()
