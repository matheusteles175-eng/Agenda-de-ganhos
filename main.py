import streamlit as st
import pandas as pd
import os
from datetime import date

# --- 1. CONFIGURAÇÃO E BANCO DE USUÁRIOS ---
st.set_page_config(page_title="App de Ganhos Multiusuário", page_icon="🚖")

ARQUIVO_USUARIOS = "usuarios.csv"

# Função para carregar a lista de usuários cadastrados
def carregar_usuarios():
    if os.path.exists(ARQUIVO_USUARIOS):
        return pd.read_csv(ARQUIVO_USUARIOS)
    else:
        # Se não existir, cria o arquivo com um usuário padrão (você!)
        df = pd.DataFrame([{"usuario": "matheus", "senha": "123"}])
        df.to_csv(ARQUIVO_USUARIOS, index=False)
        return df

# Inicializa o estado do login
if "logado" not in st.session_state:
    st.session_state.logado = False

# --- 2. TELAS DE ACESSO (LOGIN E CADASTRO) ---
def tela_acesso():
    st.title("🚖 Bem-vindo ao App de Ganhos")
    
    aba1, aba2 = st.tabs(["Fazer Login", "Criar Nova Conta"])
    
    df_usuarios = carregar_usuarios()

    with aba1:
        u_login = st.text_input("Usuário", key="u_login").lower()
        s_login = st.text_input("Senha", type="password", key="s_login")
        
        if st.button("Entrar"):
            # Verifica se o usuário existe e a senha bate
            user_match = df_usuarios[(df_usuarios['usuario'] == u_login) & (df_usuarios['senha'] == str(s_login))]
            if not user_match.empty:
                st.session_state.logado = True
                st.session_state.usuario_atual = u_login
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")

    with aba2:
        st.subheader("Crie sua conta gratuita")
        novo_u = st.text_input("Escolha um Nome de Usuário", key="u_cad").lower()
        novo_s = st.text_input("Escolha uma Senha", type="password", key="s_cad")
        confirmar_s = st.text_input("Confirme a Senha", type="password")
        
        if st.button("Cadastrar"):
            if novo_u in df_usuarios['usuario'].values:
                st.warning("Este nome de usuário já existe. Escolha outro!")
            elif novo_s != confirmar_s:
                st.error("As senhas não coincidem.")
            elif len(novo_u) < 3 or len(novo_s) < 3:
                st.error("Usuário e senha devem ter pelo menos 3 caracteres.")
            else:
                # Salva o novo usuário no arquivo CSV
                novo_registro = pd.DataFrame([{"usuario": novo_u, "senha": str(novo_s)}])
                df_atualizado = pd.concat([df_usuarios, novo_registro], ignore_index=True)
                df_atualizado.to_csv(ARQUIVO_USUARIOS, index=False)
                st.success("Conta criada com sucesso! Vá para a aba de Login.")

# --- 3. ÁREA DA CALCULADORA (SÓ ACESSA QUEM LOGAR) ---
if st.session_state.logado:
    st.sidebar.title(f"👤 {st.session_state.usuario_atual}")
    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.rerun()

    st.title(f"📊 Painel de Ganhos: {st.session_state.usuario_atual.capitalize()}")
    
    # Arquivo de dados individual para o usuário logado
    ARQUIVO_DADOS = f"dados_{st.session_state.usuario_atual}.csv"

    if os.path.exists(ARQUIVO_DADOS):
        df_dados = pd.read_csv(ARQUIVO_DADOS)
    else:
        df_dados = pd.DataFrame(columns=["Data", "Ganho", "Gasto"])

    # Lançamentos
    with st.form("form_lancamento"):
        c1, c2 = st.columns(2)
        g = c1.number_input("Quanto ganhou hoje? (R$)", min_value=0.0)
        p = c2.number_input("Quanto gastou hoje? (R$)", min_value=0.0)
        if st.form_submit_button("Salvar no meu Diário"):
            nova_linha = pd.DataFrame({"Data": [date.today().strftime("%d/%m/%Y")], "Ganho": [g], "Gasto": [p]})
            df_dados = pd.concat([df_dados, nova_linha], ignore_index=True)
            df_dados.to_csv(ARQUIVO_DADOS, index=False)
            st.success("Dados gravados!")
            st.rerun()

    # Visualização
    if not df_dados.empty:
        lucro = df_dados['Ganho'].sum() - df_dados['Gasto'].sum()
        st.metric("Meu Lucro Acumulado", f"R$ {lucro:.2f}")
        st.dataframe(df_dados, use_container_width=True)
    else:
        st.info("Sua calculadora está limpa. Comece a lançar seus ganhos!")

else:
    tela_acesso()
                                
