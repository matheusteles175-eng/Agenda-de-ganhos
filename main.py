def tela_acesso():
    st.title("🚖 Sistema de Ganhos")
    aba1, aba2 = st.tabs(["Entrar", "Criar Conta"])
    
    # Recarrega sempre para garantir que pegou o usuário novo
    df_usuarios = carregar_usuarios()

    with aba1:
        # Removi o .lower() direto no input para evitar conflito visual
        u = st.text_input("Usuário").strip()
        s = st.text_input("Senha", type="password").strip()
        
        if st.button("Login"):
            # Comparamos tudo em minúsculo (.str.lower()) para não ter erro de digitação
            user_match = df_usuarios[
                (df_usuarios['usuario'].str.lower() == u.lower()) & 
                (df_usuarios['senha'].astype(str) == str(s))
            ]
            
            if not user_match.empty:
                st.session_state.logado = True
                # Salvamos o nome original que está no banco
                st.session_state.usuario_atual = user_match.iloc[0]['usuario']
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")

    with aba2:
        novo_u = st.text_input("Novo Usuário").strip()
        novo_s = st.text_input("Nova Senha", type="password").strip()
        
        if st.button("Cadastrar"):
            if novo_u.lower() in df_usuarios['usuario'].str.lower().values:
                st.error("Usuário já existe!")
            elif novo_u == "" or novo_s == "":
                st.error("Preencha todos os campos!")
            else:
                novo_reg = pd.DataFrame([{"usuario": novo_u, "senha": str(novo_s)}])
                # Salva e força a atualização do arquivo
                df_atualizado = pd.concat([df_usuarios, novo_reg], ignore_index=True)
                df_atualizado.to_csv(ARQUIVO_USUARIOS, index=False)
                st.success("Conta criada! Agora faça login.")
                
