import streamlit as st
import os
import extra_streamlit_components as stx
import time

# Imports do seu projeto
from src.ui.components import render_layout, load_css
from src.Pages import home_telemetria, login
from src.controllers.Sensor import Sensor
from src.controllers.Rele import Rele
from dotenv import load_dotenv

# Carregando variaveis sigilosas
load_dotenv()

# 1. Configuração da Página
st.set_page_config(page_title="Telemetria", page_icon="💧", layout="wide")


# 2. Inicializa Hardware (Cache)
# @st.cache_resource
def get_hardware():
    endereco = os.getenv("RELE_IE", "ID_PADRAO")

    rele = Rele(endereco)
    sensor = Sensor()
    return sensor, rele


sensor, rele = get_hardware()

# 3. Inicializa Gerenciador de Cookies (APENAS UMA VEZ)
# O key é importante para não recriar o componente
cookie_manager = stx.CookieManager(key="auth_cookie_manager")

# --- LÓGICA DE AUTENTICAÇÃO ---

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if "just_logged_out" not in st.session_state:
    st.session_state["just_logged_out"] = False

# 1. Tenta pegar o cookie
cookie_auth = cookie_manager.get(cookie="sae_auth")

# 2. Lógica de decisão
if st.session_state["just_logged_out"]:
    # Se acabou de sair, ignora o cookie antigo até que ele seja deletado
    st.session_state["logged_in"] = False
    st.session_state["just_logged_out"] = False
else:
    # Se o cookie diz conectado, confia nele
    if cookie_auth == "conectado":
        st.session_state["logged_in"] = True

# --- RENDERIZAÇÃO ---

# 1. Carrega CSS
load_css()

# 2. Roteamento (Login vs Home)
if not st.session_state["logged_in"]:
    # Se não tem cookie e não está logado, dá um tempinho para o cookie manager carregar
    if cookie_auth is None:
        time.sleep(0.5)

    login.show(cookie_manager)

else:
    # --- ÁREA RESTRITA (LOGADO) ---
    with st.sidebar:
        st.write("👤 Usuário: **Admin**")

        if st.button("Sair / Logout 🚪", type="primary"):
            try:
                cookie_manager.delete("sae_auth")
            except KeyError:
                pass

            st.session_state["logged_in"] = False
            st.session_state["just_logged_out"] = True
            time.sleep(0.5)
            st.rerun()

    # Renderiza o cabeçalho padrão
    render_layout()

    # Chama a página principal e passa o hardware
    home_telemetria.show(sensor, rele)
