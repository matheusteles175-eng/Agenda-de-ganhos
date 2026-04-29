import streamlit as st
import pandas as pd
import os
import hashlib
from datetime import datetime, date

# --- CONFIGURAÇÕES ---
st.set_page_config(page_title="Driver Pro Mateus", page_icon="🚖", layout="centered")

# --- FUNÇÃO DE CRIPTOGRAFIA ---
def criptografar(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

# --- USUÁRIO ATUAL ---
user_path = st.session_state.get("usuario_atual", "matheus").lower()

# --- ARQUIVOS ---
arq_usuarios = "usuarios.csv"
arq_dados = f"dados_{user_path}.csv"
arq_carro = f"carro_{user_path}.csv"
arq_sonhos = f"sonhos_{user_path}.csv"
arq_dep_sonhos = f"dep_sonhos_{user_path}.csv"

# --- FUNÇÃO SEGURA DE LEITURA CSV ---
def ler_csv_seguro(caminho, colunas=None):
    if os.path.exists(caminho) and os.path.getsize(caminho) > 0:
        return pd.read_csv(caminho)
    return pd.DataFrame(columns=colunas)

# --- INICIALIZAÇÃO ---
def inicializar():
    if not os.path.exists(arq_usuarios):
        pd.DataFrame([{
            "usuario": "matheus",
            "senha": criptografar("123")
        }]).to_csv(arq_usuarios, index=False)

    if not os.path.exists(arq_dados):
        pd.DataFrame(columns=["Data", "Ganho", "Gasto", "KM"]).to_csv(arq_dados, index=False)

    if not os.path.exists(arq_carro):
        pd.DataFrame(columns=["Fipe", "KM_Atual", "KM_Oleo", "Ja_Guardado"]).to_csv(arq_carro, index=False)

    if not os.path.exists(arq_sonhos):
        pd.DataFrame(columns=["Item", "Valor_Meta"]).to_csv(arq_sonhos, index=False)

    if not os.path.exists(arq_dep_sonhos):
        pd.DataFrame(columns=["Item", "Data", "Valor_Depositado"]).to_csv(arq_dep_sonhos, index=False)

inicializar()

# --- LOGIN ---
if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.title("🚖 Driver Pro")

    df_u = ler_csv_seguro(arq_usuarios)

    aba1, aba2 = st.tabs(["Entrar", "Criar Conta"])

    with aba1:
        u = st.text_input("Usuário").lower()
        s = st.text_input("Senha", type="password")

        if st.button("Entrar"):
            senha_hash = criptografar(s)
            if any((df_u['usuario'] == u) & (df_u['senha'] == senha_hash)):
                st.session_state.logado = True
                st.session_state.usuario_atual = u
                st.rerun()
            else:
                st.error("Login inválido")

    with aba2:
        novo_u = st.text_input("Novo usuário")
        nova_s = st.text_input("Nova senha", type="password")

        if st.button("Criar Conta"):
            if novo_u and nova_s:
                novo = pd.DataFrame([{
                    "usuario": novo_u.lower(),
                    "senha": criptografar(nova_s)
                }])
                pd.concat([df_u, novo]).to_csv(arq_usuarios, index=False)
                st.success("Conta criada!")

    st.stop()

# --- APP ---
st.title(f"🚖 Driver Pro - {st.session_state.usuario_atual}")

# LOGOUT
if st.button("🚪 Sair"):
    st.session_state.logado = False
    st.rerun()

# --- VEÍCULO ---
st.header("🚗 Veículo & IPVA")

df_c = ler_csv_seguro(arq_carro)

if df_c.empty:
    with st.form("carro"):
        fipe = st.number_input("Valor FIPE")
        km = st.number_input("KM Atual")
        km_oleo = st.number_input("KM Troca de Óleo")

        if st.form_submit_button("Salvar"):
            pd.DataFrame([{
                "Fipe": fipe,
                "KM_Atual": km,
                "KM_Oleo": km_oleo,
                "Ja_Guardado": 0
            }]).to_csv(arq_carro, index=False)
            st.rerun()
else:
    c = df_c.iloc[0]

    if c['KM_Atual'] >= c['KM_Oleo']:
        st.error("⚠️ Trocar óleo urgente!")

    ipva = c['Fipe'] * 0.04
    st.info(f"IPVA estimado: R$ {ipva:.2f}")

# --- GANHOS ---
st.header("💰 Ganhos")

hoje = datetime.now()

g = st.number_input("Ganho")
gas = st.number_input("Gasto")
km = st.number_input("KM")

if st.button("Salvar ganho"):
    novo = pd.DataFrame([{
        "Data": hoje,
        "Ganho": g,
        "Gasto": gas,
        "KM": km
    }])

    df = ler_csv_seguro(arq_dados)
    pd.concat([df, novo]).to_csv(arq_dados, index=False)
    st.rerun()

df = ler_csv_seguro(arq_dados)

if not df.empty:
    df['Data'] = pd.to_datetime(df['Data'])
    df['Lucro'] = df['Ganho'] - df['Gasto']

    st.subheader("Lucro total")
    st.success(f"R$ {df['Lucro'].sum():.2f}")

    st.line_chart(df.set_index('Data')['Lucro'])

    df['Ganho_por_KM'] = df['Ganho'] / df['KM'].replace(0, 1)
    st.write("💡 Média ganho/km:", round(df['Ganho_por_KM'].mean(), 2))

# --- META ---
st.header("🎯 Meta diária")

meta = st.number_input("Meta", value=200.0)

if not df.empty:
    hoje_str = date.today()
    ganho_hoje = df[df['Data'].dt.date == hoje_str]['Ganho'].sum()

    if ganho_hoje >= meta:
        st.success("Meta batida hoje!")
    else:
        st.warning(f"Faltam R$ {meta - ganho_hoje:.2f}")

# --- SONHOS ---
st.header("🎯 Sonhos")

df_s = ler_csv_seguro(arq_sonhos)
df_dep = ler_csv_seguro(arq_dep_sonhos)

with st.form("novo_sonho"):
    nome = st.text_input("Nome do sonho")
    valor = st.number_input("Valor")

    if st.form_submit_button("Criar"):
        novo = pd.DataFrame([{"Item": nome, "Valor_Meta": valor}])
        pd.concat([df_s, novo]).to_csv(arq_sonhos, index=False)
        st.rerun()

for i, s in df_s.iterrows():
    st.subheader(s['Item'])

    total = df_dep[df_dep['Item'] == s['Item']]['Valor_Depositado'].sum()
    progresso = min(total / s['Valor_Meta'], 1)

    st.progress(progresso)
    st.write(f"R$ {total:.2f} / R$ {s['Valor_Meta']:.2f}")

    val = st.number_input("Depositar", key=i)

    if st.button("Guardar", key=f"b{i}"):
        novo = pd.DataFrame([{
            "Item": s['Item'],
            "Data": datetime.now(),
            "Valor_Depositado": val
        }])
        pd.concat([df_dep, novo]).to_csv(arq_dep_sonhos, index=False)
        st.rerun()
