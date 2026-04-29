import streamlit as st
import pandas as pd
import os
from datetime import date, datetime, timedelta

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Driver Pro Mateus 🚖", page_icon="🚖", layout="centered")

# --- ARQUIVOS DE DADOS ---
ARQUIVO_USUARIOS = "usuarios.csv"

def carregar_usuarios():
    if os.path.exists(ARQUIVO_USUARIOS):
        return pd.read_csv(ARQUIVO_USUARIOS, dtype=str)
    return pd.DataFrame([{"usuario": "matheus", "senha": "123"}])

if "logado" not in st.session_state:
    st.session_state.logado = False

# --- TELA DE ACESSO (IGUAL A SUA ORIGINAL) ---
def tela_acesso():
    st.markdown("<h1 style='text-align: center; color: #FFD700;'>🚖 Sistema Driver Pro</h1>", unsafe_allow_html=True)
    aba1, aba2 = st.tabs(["Entrar", "Criar Conta"])
    df_usuarios = carregar_usuarios()

    with aba1:
        u = st.text_input("Usuário", key="login_user").strip().lower()
        s = st.text_input("Senha", type="password", key="login_pass").strip()
        if st.button("Entrar no Painel", use_container_width=True):
            if any((df_usuarios['usuario'].str.lower() == u) & (df_usuarios['senha'] == s)):
                st.session_state.logado = True
                st.session_state.usuario_atual = u
                st.rerun()
            else: st.error("Usuário ou senha incorretos.")

    with aba2:
        novo_u = st.text_input("Novo Usuário", key="cad_user").strip()
        novo_s = st.text_input("Nova Senha", type="password", key="cad_pass").strip()
        if st.button("Criar Minha Conta", use_container_width=True):
            if novo_u and novo_s:
                if novo_u.lower() in df_usuarios['usuario'].str.lower().values: st.error("Usuário existe!")
                else:
                    novo_reg = pd.DataFrame([{"usuario": novo_u, "senha": str(novo_s)}])
                    pd.concat([df_usuarios, novo_reg], ignore_index=True).to_csv(ARQUIVO_USUARIOS, index=False)
                    st.success("Conta criada!")
            else: st.error("Preencha tudo!")

if st.session_state.logado:
    user_path = st.session_state.usuario_atual.lower()
    arq_dados = f"dados_{user_path}.csv"
    arq_meta = f"meta_{user_path}.txt"
    arq_carro = f"carro_{user_path}.csv"
    arq_sonhos = f"sonhos_{user_path}.csv"

    # --- INICIALIZAR ARQUIVOS SE NÃO EXISTIREM ---
    for arq, colunas in {arq_dados: ["Data", "Ganho", "Gasto", "KM", "Inicio", "Fim"], 
                         arq_sonhos: ["Item", "Valor", "DataAlvo"],
                         arq_carro: ["Fipe", "KM_Atual", "KM_Oleo"]}.items():
        if not os.path.exists(arq): pd.DataFrame(columns=colunas).to_csv(arq, index=False)

    # --- SIDEBAR ---
    st.sidebar.write(f"👤 Motorista: **{st.session_state.usuario_atual.capitalize()}**")
    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.rerun()

    # --- CABEÇALHO INTELIGENTE (CARRO E IPVA) ---
    df_carro = pd.read_csv(arq_carro)
    if df_carro.empty:
        with st.expander("🚗 CONFIGURAÇÃO INICIAL DO VEÍCULO", expanded=True):
            with st.form("set_car"):
                f1 = st.number_input("Valor FIPE", value=40000.0)
                f2 = st.number_input("KM Atual", value=100000.0)
                f3 = st.number_input("KM Próxima Troca Óleo", value=110000.0)
                if st.form_submit_button("Salvar Veículo"):
                    pd.DataFrame([{"Fipe": f1, "KM_Atual": f2, "KM_Oleo": f3}]).to_csv(arq_carro, index=False)
                    st.rerun()
    else:
        # Cálculos Automáticos baseados no Histórico
        df_dados = pd.read_csv(arq_dados)
        km_rodado_total = df_dados['KM'].sum() if not df_dados.empty else 0
        km_atual = df_carro.iloc[0]['KM_Atual'] + km_rodado_total
        km_restante_oleo = df_carro.iloc[0]['KM_Oleo'] - km_atual
        v_ipva = df_carro.iloc[0]['Fipe'] * 0.04
        
        c1, c2, c3 = st.columns(3)
        c1.metric("KM Painel", f"{km_atual:.0f}")
        c2.metric("Troca de Óleo", f"{km_restante_oleo:.0f} km", delta_color="inverse")
        c3.metric("IPVA/Mês", f"R$ {v_ipva/12:.2f}")

    # --- FORMULÁRIO DE LANÇAMENTO (EVOLUÍDO) ---
    with st.container(border=True):
        st.subheader("🎯 Registro de Jornada")
        
        # Meta Diária
        try: 
            with open(arq_meta, "r") as f: meta_atual = float(f.read())
        except: meta_atual = 0.0
            
        nova_meta = st.number_input("Sua Meta Diária (R$)", value=meta_atual, step=10.0)
        if nova_meta != meta_atual:
            with open(arq_meta, "w") as f: f.write(str(nova_meta))
            st.rerun()

        st.markdown("---")
        col_h1, col_h2 = st.columns(2)
        h_ini = col_h1.text_input("Horário Início", placeholder="08:00")
        h_fim = col_h2.text_input("Horário Fim", placeholder="19:00")
        
        c_g, c_p, c_km = st.columns(3)
        g = c_g.number_input("Ganho Bruto (R$)", value=None, placeholder="0.00")
        p = c_p.number_input("Gasto/Comb. (R$)", value=None, placeholder="0.00")
        km = c_km.number_input("KM Rodado", value=None, placeholder="0")
        
        if st.button("➕ SALVAR E ATUALIZAR TUDO", use_container_width=True, type="primary"):
            if g is not None:
                hoje_str = date.today().strftime("%d/%m/%Y")
                nova_linha = pd.DataFrame({"Data": [hoje_str], "Ganho": [g], "Gasto": [p or 0], "KM": [km or 0], "Inicio": [h_ini], "Fim": [h_fim]})
                df_dados = pd.concat([pd.read_csv(arq_dados), nova_linha], ignore_index=True)
                df_dados.to_csv(arq_dados, index=False)
                st.success("Dados gravados! O KM do carro foi atualizado.")
                st.rerun()

    # --- CARD DE STATUS (O QUE VOCÊ GOSTA) ---
    df_dados = pd.read_csv(arq_dados)
    hoje_str = date.today().strftime("%d/%m/%Y")
    df_hoje = df_dados[df_dados['Data'] == hoje_str]
    saldo_hoje = df_hoje['Ganho'].sum() - df_hoje['Gasto'].sum()

    if nova_meta > 0:
        cor, txt = ("#28a745", "✅ META BATIDA!") if saldo_hoje >= nova_meta else ("#dc3545", "❌ FALTA PARA A META")
    else: cor, txt = ("#444444", "🎯 DEFINA UMA META")

    st.markdown(f"""
        <div style="background-color: {cor}; padding: 20px; border-radius: 15px; text-align: center; color: white;">
            <p style="margin: 0; opacity: 0.8;">Saldo Líquido de Hoje</p>
            <h1 style="margin: 0;">R$ {saldo_hoje:.2f}</h1>
            <p style="font-weight: bold;">{txt}</p>
        </div>
    """, unsafe_allow_html=True)

    # --- HISTÓRICO COM LIXEIRA ---
    st.markdown("### 📜 Histórico & Horários")
    for i, row in df_dados.iloc[::-1].head(5).iterrows():
        with st.container(border=True):
            c_d, c_h, c_l, c_del = st.columns([1, 1.2, 1, 0.4])
            c_d.write(f"📅 {row['Data']}")
            c_h.write(f"⏰ {row['Inicio']} - {row['Fim']}")
            c_l.write(f"💰 **R$ {row['Ganho'] - row['Gasto']:.2f}**")
            if c_del.button("🗑️", key=f"del_{i}"):
                df_dados.drop(i).to_csv(arq_dados, index=False)
                st.rerun()

    # --- SEÇÃO DAS CAIXINHAS (SONHOS) ---
    st.divider()
    st.subheader("🎯 Caixinhas de Sonhos")
    with st.expander("Adicionar Novo Sonho"):
        with st.form("new_dream"):
            it = st.text_input("O que quer conquistar?"); val = st.number_input("Valor R$"); dat = st.date_input("Até quando?")
            if st.form_submit_button("Criar Caixinha"):
                df_s = pd.concat([pd.read_csv(arq_sonhos), pd.DataFrame([{"Item": it, "Valor": val, "DataAlvo": dat}])], ignore_index=True)
                df_s.to_csv(arq_sonhos, index=False); st.rerun()

    # Mostrar as Caixinhas
    df_s = pd.read_csv(arq_sonhos)
    for _, s in df_s.iterrows():
        with st.container(border=True):
            st.write(f"🚀 **{s['Item']}** - Total: R$ {s['Valor']}")
            st.info(f"Mateus, não desiste! Seu sonho está em jogo. Vamos bater o verde hoje!")

else: tela_acesso()
