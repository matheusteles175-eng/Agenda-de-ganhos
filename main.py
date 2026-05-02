import streamlit as st
import pandas as pd
import json
import os
import hashlib
import re
from datetime import datetime, date, timedelta

# --- CONFIGURAÇÕES INICIAIS ---
st.set_page_config(page_title="Renda Organizada", page_icon="💰")

PASTA = "data"
if not os.path.exists(PASTA):
    os.makedirs(PASTA)

USERS_FILE = os.path.join(PASTA, "users.json")
CALC_HIST_FILE = os.path.join(PASTA, "calc_hist.json")
NOTAS_FILE = os.path.join(PASTA, "notas.json")

# --- FUNÇÕES DE DADOS ---
def hash_senha(s):
    return hashlib.sha256(s.encode()).hexdigest()

def salvar(arq, dados):
    with open(arq, "w") as f:
        json.dump(dados, f)

def carregar(arq, default):
    if os.path.exists(arq):
        try:
            with open(arq, "r") as f: return json.load(f)
        except: return default
    return default

# --- ESTADO DA SESSÃO ---
if 'logado' not in st.session_state:
    st.session_state.logado = False
if 'user' not in st.session_state:
    st.session_state.user = None

# --- TELA DE LOGIN ---
if not st.session_state.logado:
    st.title("Controle de Ganhos")
    tab1, tab2 = st.tabs(["Entrar", "Cadastrar"])

    with tab1:
        u_login = st.text_input("Usuário", key="u_login")
        s_login = st.text_input("Senha", type="password", key="s_login")
        if st.button("ENTRAR"):
            users = carregar(USERS_FILE, {})
            if u_login in users and users[u_login] == hash_senha(s_login):
                st.session_state.logado = True
                st.session_state.user = u_login
                st.rerun()
            else:
                st.error("Login inválido")

    with tab2:
        u_cad = st.text_input("Novo Usuário", key="u_cad")
        s_cad = st.text_input("Nova Senha", type="password", key="s_cad")
        if st.button("CADASTRAR"):
            if u_cad and s_cad:
                users = carregar(USERS_FILE, {})
                users[u_cad] = hash_senha(s_cad)
                salvar(USERS_FILE, users)
                st.success("Cadastrado com sucesso! Vá para a aba Entrar.")

# --- INTERFACE PRINCIPAL ---
else:
    user = st.session_state.user
    file_user = os.path.join(PASTA, f"dados_{user}.json")
    dados_user = carregar(file_user, {})

    # Barra Lateral (Menu)
    st.sidebar.title(f"👤 {user}")
    menu = st.sidebar.radio("Navegação", ["Ganhos", "Calculadora", "Notas", "Histórico"])
    
    if st.sidebar.button("SAIR"):
        st.session_state.logado = False
        st.rerun()

    if menu == "Ganhos":
        st.header("📊 Registro de Ganhos")
        
        with st.container(border=True):
            meta = st.number_input("Meta (Líquido):", value=0.0)
            col1, col2 = st.columns(2)
            ini = col1.text_input("Início (Ex: 08:00):", "00:00")
            fim = col2.text_input("Fim (Ex: 18:00):", "00:00")
            
            bruto = st.number_input("Valor Bruto:", min_value=0.0)
            gastos = st.number_input("Gastos:", min_value=0.0)
            km = st.number_input("KM Rodados:", min_value=1.0)

            if st.button("CALCULAR E SALVAR", use_container_width=True):
                try:
                    # Lógica de Horas
                    t1 = datetime.strptime(ini, "%H:%M")
                    t2 = datetime.strptime(fim, "%H:%M")
                    if t2 < t1: t2 += timedelta(days=1)
                    horas = (t2 - t1).total_seconds() / 3600
                    
                    liquido = bruto - gastos
                    dif = liquido - meta
                    r_km = bruto / km
                    r_hora = bruto / horas if horas > 0 else 0
                    
                    if dif >= 0:
                        st.success(f"PARABÉNS! Superou a meta em + R$ {dif:.2f}")
                    else:
                        st.error(f"DÉFICIT! Abaixo da meta em - R$ {abs(dif):.2f}")
                    
                    st.info(f"Líquido: R$ {liquido:.2f} | Bruto: R$ {bruto:.2f}\n\n"
                            f"KM: R$ {r_km:.2f}/km | Hora: R$ {r_hora:.2f}/h")
                    
                    # Salvar
                    hoje = str(date.today())
                    dados_user[hoje] = {
                        "liquido": liquido, "bruto": bruto, "gastos": gastos, 
                        "meta": meta, "km": km, "hora_bruta": r_hora, "km_bruto": r_km,
                        "horas_trab": horas, "dif": dif
                    }
                    salvar(file_user, dados_user)
                except Exception as e:
                    st.error(f"Erro no formato: {e}")

    elif menu == "Calculadora":
        st.header("🧮 Calculadora de Somas")
        txt_calc = st.text_area("Digite ou cole os valores (ex: 10,50 + 20):")
        nums = re.findall(r'\d+[.,]?\d*', txt_calc)
        total = sum(float(n.replace(",", ".")) for n in nums)
        
        st.subheader(f"SOMA: R$ {total:.2f}")
        
        if st.button("Salvar Soma"):
            h = carregar(CALC_HIST_FILE, [])
            h.append({"id": datetime.now().timestamp(), "val": f"R$ {total:.2f}", "data": datetime.now().strftime("%H:%M")})
            salvar(CALC_HIST_FILE, h)
            st.rerun()

        st.divider()
        st.write("Histórico da Calculadora:")
        calc_hist = carregar(CALC_HIST_FILE, [])
        for item in reversed(calc_hist):
            col_h1, col_h2 = st.columns([4, 1])
            col_h1.write(f"🕒 {item['data']} | {item['val']}")
            if col_h2.button("🗑️", key=f"del_calc_{item['id']}"):
                novo_h = [i for i in calc_hist if i['id'] != item['id']]
                salvar(CALC_HIST_FILE, novo_h)
                st.rerun()

    elif menu == "Notas":
        st.header("📝 Bloco de Notas")
        txt_nota = st.text_area("Anotar algo...")
        if st.button("Salvar Nota"):
            n = carregar(NOTAS_FILE, [])
            n.append({"id": datetime.now().timestamp(), "data": datetime.now().strftime("%d/%m %H:%M"), "txt": txt_nota})
            salvar(NOTAS_FILE, n)
            st.rerun()
            
        st.divider()
        notas = carregar(NOTAS_FILE, [])
        for nota in reversed(notas):
            with st.expander(f"Nota {nota['data']}"):
                st.write(nota['txt'])
                if st.button("Apagar Nota", key=f"del_n_{nota['id']}"):
                    nova_n = [i for i in notas if i['id'] != nota['id']]
                    salvar(NOTAS_FILE, nova_n)
                    st.rerun()

    elif menu == "Histórico":
        st.header("📜 Histórico de Rendimento")
        if not dados_user:
            st.warning("Nenhum dado registrado.")
        else:
            for dia, d in sorted(dados_user.items(), reverse=True):
                with st.container(border=True):
                    col_d1, col_d2 = st.columns([4, 1])
                    cor = "green" if d['dif'] >= 0 else "red"
                    col_d1.markdown(f"### :{cor}[{dia}]")
                    if col_d2.button("🗑️", key=f"del_dia_{dia}"):
                        del dados_user[dia]
                        salvar(file_user, dados_user)
                        st.rerun()
                    
                    st.write(f"**Líquido:** R$ {d['liquido']:.2f} | **Meta:** R$ {d['meta']:.2f}")
                    st.write(f"Bruto: R$ {d['bruto']:.2f} | Gastos: R$ {d['gastos']:.2f}")
                    st.write(f"KM: R$ {d['km_bruto']:.2f}/km | Hora: R$ {d['hora_bruta']:.2f}/h")

    # Botão de Reset Geral na Sidebar
    st.sidebar.divider()
    if st.sidebar.button("⚠️ ZERAR TODOS OS DADOS"):
        if os.path.exists(file_user): os.remove(file_user)
        st.sidebar.success("Dados limpos!")
        st.rerun()
