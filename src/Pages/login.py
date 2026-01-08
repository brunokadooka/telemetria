import streamlit as st
import time
import datetime
import base64
import os
from dotenv import load_dotenv


def get_img_as_base64(file_path):
    try:
        with open(file_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except Exception:
        return None


def show(cookie_manager):
    logo = get_img_as_base64("assets/img/logo-dark-rancharia.svg")

    col1, col2, col3 = st.columns([1, 1.5, 1])

    load_dotenv()

    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)

        with st.container(border=True):
            if logo:
                st.markdown(
                    f"""
                    <div style="display: flex; justify-content: center; margin-bottom: 20px;">
                        <img src="data:image/svg+xml;base64,{logo}" style="width: 180px;">
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown("## 🔐 SAE Rancharia")

            st.markdown(
                "<h4 style='text-align: center; color: #888;'>Acesso Restrito</h4>",
                unsafe_allow_html=True,
            )

            # --- AQUI COMEÇA A MUDANÇA (FORMULÁRIO) ---
            # O 'clear_on_submit=False' impede que apague o texto se errar a senha
            with st.form(key="login_form", clear_on_submit=False):
                usuario = st.text_input("Usuário")
                senha = st.text_input("Senha", type="password")

                st.markdown("<br>", unsafe_allow_html=True)

                # Botão especial de formulário (Reage ao ENTER)
                submit_button = st.form_submit_button(
                    "Entrar", type="primary", use_container_width=True
                )

                if submit_button:
                    user_env = os.getenv("ACESSO_USUARIO")
                    pass_env = os.getenv("ACESSO_PASSWORD")
                    if usuario == user_env and senha == pass_env:
                        cookie_manager.set(
                            "sae_auth",
                            "conectado",
                            expires_at=datetime.datetime.now()
                            + datetime.timedelta(days=1),
                        )
                        st.session_state["logged_in"] = True
                        st.success("Login realizado!")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("Usuário ou senha incorretos")
