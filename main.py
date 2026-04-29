import streamlit as st
import pandas as pd
import os
from datetime import date, datetime

st.set_page_config(page_title="Controle Motorista PRO", layout="wide")

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

# ---------------- LOGIN ----------------
usuarios = {
    "mateus": "123",
    "joao": "456"
}

if "usuario" not in st.session_state:
    st.session_state.usuario = ""

if st.session_state.usuario == "":
    st.title("🔐 Login")

    user = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        if user in usuarios and usuarios[user] == senha:
            st.session_state.usuario = user.strip().lower()
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos")

    st.stop()

usuario = st.session_state.usuario

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

        c1,c2,c3 = st.columns(3)
        c1.metric("Lucro", f"R$ {lucro:.2f}")
        c2.metric("R$/KM", f"{valor_km:.2f}")
        c3.metric("R$/Hora", f"{valor_hora:.2f}")

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
        df = pd.read_csv(arq_gastos)
    else:
        df = pd.DataFrame(columns=["Nome","Categoria","Valor","Status","Vencimento"])

    # -------- INPUT --------
    nome_gasto = st.text_input("Nome da despesa")

    categorias = ["Comida","Luz","Água","Internet","Dívida","Transporte","Outros"]
    cat = st.selectbox("Categoria", categorias)

    valor = st.number_input("Valor", min_value=0.0)
    venc = st.date_input("Vencimento")

    if st.button("Adicionar gasto"):
        novo = pd.DataFrame([{
            "Nome": nome_gasto,
            "Categoria": cat,
            "Valor": valor,
            "Status": "Pendente",
            "Vencimento": venc
        }])
        df = pd.concat([df, novo], ignore_index=True)
        df.to_csv(arq_gastos, index=False)
        st.success("Gasto adicionado!")
        st.rerun()

    # -------- LISTA --------
    if not df.empty:

        st.subheader("📋 Contas")

        for i, r in df.iterrows():

            dias = (pd.to_datetime(r["Vencimento"]) - pd.to_datetime(date.today())).days

            if dias <= 0:
                por_dia = r["Valor"]
            else:
                por_dia = r["Valor"] / dias

            # STATUS VISUAL
            status_icon = "✅" if r["Status"] == "Pago" else "❌"

            c1,c2,c3,c4,c5,c6 = st.columns([2,2,2,2,1,1])

            c1.write(f"{status_icon} {r['Nome']}")
            c2.write(f"R$ {r['Valor']:.2f}")
            c3.write(f"{dias} dias")
            c4.write(f"R$ {por_dia:.2f}/dia")

            # botão pagar
            if r["Status"] == "Pendente":
                if c5.button("✔", key=f"p{i}"):
                    df.at[i, "Status"] = "Pago"
                    df.to_csv(arq_gastos, index=False)
                    st.rerun()

            # botão excluir
            if c6.button("🗑️", key=f"d{i}"):
                df = df.drop(i)
                df.to_csv(arq_gastos, index=False)
                st.rerun()
