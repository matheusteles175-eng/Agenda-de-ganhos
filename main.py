import streamlit as st
import pandas as pd
import os
from datetime import date, datetime

st.set_page_config(page_title="Controle PRO 🚖💸", layout="wide")

# ---------------- ESTILO ----------------
st.markdown("""
<style>
.main {background-color: #0f172a;}
h1, h2, h3 {color: white;}
.stMetric {background-color: #1e293b; padding: 15px; border-radius: 10px;}
</style>
""", unsafe_allow_html=True)

# ---------------- NOME ----------------
if "nome" not in st.session_state:
    st.session_state.nome = ""

if st.session_state.nome == "":
    st.title("🚀 Bem-vindo ao Controle PRO")
    nome = st.text_input("Como podemos te chamar?")
    if st.button("Entrar"):
        if nome:
            st.session_state.nome = nome
            st.rerun()
    st.stop()

nome = st.session_state.nome

# ---------------- ARQUIVOS ----------------
arq_ganhos = f"ganhos_{nome}.csv"
arq_gastos = f"gastos_{nome}.csv"
arq_meta = f"meta_{nome}.csv"

st.title(f"🚖 Painel de {nome}")

# ---------------- ABAS ----------------
aba1, aba2 = st.tabs(["🚖 Ganhos", "💸 Despesas"])

# =========================================================
# ======================= GANHOS ===========================
# =========================================================
with aba1:

    st.subheader("🎯 Metas")

    if os.path.exists(arq_meta):
        meta_df = pd.read_csv(arq_meta)
        meta_km = float(meta_df["km"][0])
        meta_hora = float(meta_df["hora"][0])
        meta_lucro = float(meta_df["lucro"][0])
    else:
        meta_km, meta_hora, meta_lucro = 2.0, 30.0, 100.0

    c1,c2,c3 = st.columns(3)
    meta_km = c1.number_input("Meta R$/KM", value=meta_km)
    meta_hora = c2.number_input("Meta R$/Hora", value=meta_hora)
    meta_lucro = c3.number_input("Meta Lucro", value=meta_lucro)

    if st.button("Salvar metas"):
        pd.DataFrame([{"km":meta_km,"hora":meta_hora,"lucro":meta_lucro}]).to_csv(arq_meta,index=False)
        st.success("Metas salvas!")

    # -------- dados --------
    if os.path.exists(arq_ganhos):
        df = pd.read_csv(arq_ganhos)
    else:
        df = pd.DataFrame(columns=["Data","Ganho","Gasto","KM","Inicio","Fim"])

    for col in ["Ganho","Gasto","KM"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    st.subheader("📥 Lançamento")

    c1,c2,c3 = st.columns(3)
    ganho = c1.number_input("Ganho")
    gasto = c2.number_input("Gasto")
    km = c3.number_input("KM")

    inicio = st.time_input("Início")
    fim = st.time_input("Fim")

    if st.button("Salvar Dia"):
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
        st.rerun()

    # -------- RESULTADO --------
    hoje = str(date.today())
    df_hoje = df[df["Data"] == hoje]

    if not df_hoje.empty:

        total_ganho = df_hoje["Ganho"].sum()
        total_gasto = df_hoje["Gasto"].sum()
        lucro = total_ganho - total_gasto
        total_km = df_hoje["KM"].sum()

        horas = 0
        for _, r in df_hoje.iterrows():
            t1 = datetime.strptime(r["Inicio"], "%H:%M")
            t2 = datetime.strptime(r["Fim"], "%H:%M")
            diff = (t2 - t1).total_seconds()/3600
            if diff < 0: diff += 24
            horas += diff

        valor_km = total_ganho/total_km if total_km else 0
        valor_hora = total_ganho/horas if horas else 0

        st.subheader("📊 Resultado Hoje")

        c1,c2,c3 = st.columns(3)
        c1.metric("Lucro", f"R$ {lucro:.2f}")
        c2.metric("R$/KM", f"{valor_km:.2f}")
        c3.metric("R$/Hora", f"{valor_hora:.2f}")

        falta = meta_lucro - lucro

        if lucro >= meta_lucro:
            st.success(f"{nome}, você superou sua meta! 🚀")
        else:
            st.warning(f"{nome}, faltam R$ {falta:.2f} para sua meta.")

# =========================================================
# ======================= GASTOS ===========================
# =========================================================
with aba2:

    st.subheader("💸 Controle de Despesas")

    if os.path.exists(arq_gastos):
        df = pd.read_csv(arq_gastos)
    else:
        df = pd.DataFrame(columns=["Categoria","Valor","Status","Vencimento"])

    cat = st.selectbox("Categoria",["Comida","Luz","Água","Internet","Dívida","Outros"])
    val = st.number_input("Valor", min_value=0.0)
    venc = st.date_input("Vencimento")

    if st.button("Adicionar gasto"):
        novo = pd.DataFrame([{
            "Categoria":cat,
            "Valor":val,
            "Status":"Pendente",
            "Vencimento":venc
        }])
        df = pd.concat([df, novo], ignore_index=True)
        df.to_csv(arq_gastos, index=False)
        st.rerun()

    if not df.empty:
        df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0)

        total = df["Valor"].sum()
        pago = df[df["Status"]=="Pago"]["Valor"].sum()
        pendente = df[df["Status"]=="Pendente"]["Valor"].sum()

        c1,c2,c3 = st.columns(3)
        c1.metric("Total", f"R$ {total:.2f}")
        c2.metric("Pago", f"R$ {pago:.2f}")
        c3.metric("Pendente", f"R$ {pendente:.2f}")

        st.bar_chart(df.groupby("Categoria")["Valor"].sum())

        st.subheader("📋 Contas")

        for i,r in df.iterrows():
            dias = (pd.to_datetime(r["Vencimento"]) - pd.to_datetime(date.today())).days
            por_dia = r["Valor"]/dias if dias>0 else r["Valor"]

            c1,c2,c3,c4,c5 = st.columns(5)

            c1.write(r["Categoria"])
            c2.write(f"R$ {r['Valor']}")
            c3.write(r["Status"])
            c4.write(f"{dias} dias | {por_dia:.2f}/dia")

            if r["Status"]=="Pendente":
                if c5.button("Pagar", key=f"p{i}"):
                    df.at[i,"Status"]="Pago"
                    df.to_csv(arq_gastos,index=False)
                    st.rerun()

            if c5.button("❌", key=f"d{i}"):
                df = df.drop(i)
                df.to_csv(arq_gastos,index=False)
                st.rerun()
