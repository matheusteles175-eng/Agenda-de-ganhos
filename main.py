import streamlit as st
import pandas as pd
import os
from datetime import date

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Calculadora de Ganhos", page_icon="🚖")

ARQUIVO_USUARIOS = "usuarios.csv"

# FUNÇÃO SIMPLIFICADA PARA CARREGAR
def carregar_usuarios():
    if os.path.exists(ARQUIVO_USUARIOS):
        return pd.read_csv(ARQUIVO_USUARIOS, dtype=str) # Lê tudo como texto para evitar erro
    else:
        df = pd.DataFrame([{"usuario": "matheus", "senha": "123"}])
        df.to_csv(ARQUIVO_USUARIOS, index=False)
        return df

if "logado" not in st.session_state:
    st.session_state.logado = False

# TELA DE ACESSO REFORMULADA
def tela_acesso():
    st.title("🚖 Sistema de Ganhos")
    aba1, aba2 = st.tabs(["Entrar", "Criar Conta"])
    
    df_usuarios = carregar_usuarios()

    with aba1:
        u = st.text_input("Usuário", key="login_user").strip()
        s = st.text_input("Senha", type="password", key="login_pass").strip()
        
        if st.button("Login"):
            # Verificação simples linha por linha para não travar
            sucesso = False
            for index, row in df_usuarios.iterrows():
                if str(row['usuario']).lower() == u.lower() and str(row['senha']) == s:
                    sucesso = True
                    break
            
            if sucesso:
                st.session_state.logado = True
                st.session_state.usuario_atual = u
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")

    with aba2:
        novo_u = st.text_input("Novo Usuário", key="cad_user").strip()
        novo_s = st.text_input("Nova Senha", type="password", key="cad_pass").strip()
        
        if st.button("Cadastrar"):
            if novo_u == "" or novo_s == "":
                st.error("Preencha todos os campos!")
            elif novo_u.lower() in df_usuarios['usuario'].str.lower().values:
                st.error("Este usuário já existe!")
            else:
                novo_reg = pd.DataFrame([{"usuario": novo_u, "senha": str(novo_s)}])
                novo_df = pd.concat([df_usuarios, novo_reg], ignore_index=True)
                novo_df.to_csv(ARQUIVO_USUARIOS, index=False)
                st.success("Conta criada! Tente logar agora.")
                st.balloons()

# LÓGICA DE EXIBIÇÃO
if st.session_state.logado:
    # --- ÁREA DO MOTORISTA ---
    st.sidebar.write(f"Logado como: **{st.session_state.usuario_atual}**")
    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.rerun()

    st.title(f"📊 Painel de {st.session_state.usuario_atual}")
    
    # Nome do arquivo de dados do usuário
    arq_dados = f"dados_{st.session_state.usuario_atual.lower()}.csv"
    
    if os.path.exists(arq_dados):
        df_dados = pd.read_csv(arq_dados)
    else:
        df_dados = pd.DataFrame(columns=["Data", "Ganho", "Gasto"])

    with st.form("lancamento"):
        g = st.number_input("Ganhos (R$)", min_value=0.0)
        p = st.number_input("Gastos (R$)", min_value=0.0)
        if st.form_submit_button("Salvar Registro"):
            nova_linha = pd.DataFrame({"Data": [date.today().strftime("%d/%m/%Y")], "Ganho": [g], "Gasto": [p]})
            df_dados = pd.concat([df_dados, nova_linha], ignore_index=True)
            df_dados.to_csv(arq_dados, index=False)
            st.success("Gravado com sucesso!")
            st.rerun()

    if not df_dados.empty:
        total = df_dados['Ganho'].sum() - df_dados['Gasto'].sum()
        st.metric("Saldo Atual", f"R$ {total:.2f}")
        st.dataframe(df_dados)
else:
    tela_acesso()
    
