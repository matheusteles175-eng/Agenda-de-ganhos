import streamlit as st
import pandas as pd
import os
from datetime import date, datetime

st.set_page_config(page_title="Controle Motorista PRO", layout="wide")

# ---------------- NOME ----------------
if "nome" not in st.session_state:
    st.session_state.nome = ""

if st.session_state.nome == "":
    st.title("🚖 Bem-vindo")
    nome = st.text_input("Como podemos te chamar?")
    if st.button("Entrar"):
        if nome:
            st.session_state.nome = nome
            st.rerun()
    st.stop()

nome = st.session_state.nome

# ---------------- ARQUIVOS ----------------
arq_ganhos = f"ganhos_{nome}.csv"
arq_meta = f"meta_{nome}.csv"

st.title(f"🚖 Painel de {nome}")

# ---------------- METAS ----------------
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

# ---------------- DADOS ----------------
if os.path.exists(arq_ganhos):
    df = pd.read_csv(arq_ganhos)
else:
    df = pd.DataFrame(columns=["Data","Ganho","Gasto","KM","Inicio","Fim"])

for col in ["Ganho","Gasto","KM"]:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

# ---------------- INPUT ----------------
st.subheader("📥 Lançamento do Dia")

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
    st.success("Salvo!")
    st.rerun()

# ---------------- RESULTADO HOJE ----------------
st.subheader("📊 Resultado de Hoje")

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
        if diff < 0:
            diff += 24
        horas += diff

    valor_km = total_ganho/total_km if total_km else 0
    valor_hora = total_ganho/horas if horas else 0

    st.write(f"💰 Ganho: {total_ganho:.2f}")
    st.write(f"💸 Gasto: {total_gasto:.2f}")
    st.write(f"📈 Lucro: {lucro:.2f}")

    st.write(f"🚗 KM: {total_km:.2f}")
    st.write(f"⏱️ Hora: {valor_hora:.2f}")
    st.write(f"📏 KM valor: {valor_km:.2f}")

    # META PROGRESSIVA
    st.subheader("🎯 Progresso da Meta")

    falta = meta_lucro - lucro

    if lucro >= meta_lucro:
        st.success(f"{nome}, você bateu a meta! 🔥")
    else:
        st.warning(f"{nome}, faltam R$ {falta:.2f} para sua meta.")

    # ALERTA
    if lucro < meta_lucro:
        st.info(f"💡 Continue! Você está a R$ {falta:.2f} de atingir sua meta.")

    # ANÁLISE
    st.subheader("🧠 Análise")

    if valor_km >= meta_km:
        st.success("Meta de KM atingida")
    else:
        st.warning("KM abaixo da meta")

    if valor_hora >= meta_hora:
        st.success("Meta por hora atingida")
    else:
        st.warning("Hora abaixo da meta")

# ---------------- GRÁFICOS ----------------
if not df.empty:
    st.subheader("📈 Evolução")
    st.line_chart(df["Ganho"])

# ---------------- RESUMO SEMANAL ----------------
st.subheader("📅 Resumo Semanal")

if not df.empty:
    df["Data"] = pd.to_datetime(df["Data"])
    semana = df[df["Data"] > (pd.Timestamp.today() - pd.Timedelta(days=7))]

    if not semana.empty:
        st.write(f"Lucro últimos 7 dias: {(semana['Ganho'].sum() - semana['Gasto'].sum()):.2f}")

# ---------------- EXPORTAR ----------------
st.subheader("📁 Exportar")

if not df.empty:
    st.download_button(
        "Baixar Excel",
        df.to_csv(index=False),
        file_name="dados.csv"
    )

# ---------------- HISTÓRICO ----------------
st.subheader("📜 Histórico")

for i, r in df.iloc[::-1].iterrows():
    c1,c2,c3,c4 = st.columns([2,2,2,1])

    lucro = r["Ganho"] - r["Gasto"]

    c1.write(r["Data"])
    c2.write(f"Ganho: {r['Ganho']} / Gasto: {r['Gasto']}")
    c3.write(f"Lucro: {lucro:.2f}")

    if c4.button("🗑️", key=f"del{i}"):
        df = df.drop(i)
        df.to_csv(arq_ganhos, index=False)
        st.rerun()
