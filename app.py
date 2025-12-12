import streamlit as st
from src.ui.components import *

# 1. Configuração (Sempre a primeira linha)
st.set_page_config(
    page_title="Telemetria Saneamento",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Ocultar menu hambúrguer, rodapé e cabeçalho
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# 2. Carregar o CSS (A mágica do design)
load_css()


def main():
    # --- Sidebar ---
    with st.sidebar:
        try:
            # Ajuste o nome do arquivo se necessário (logo.png ou logo_prefeitura.png)
            st.image("assets/img/logo.png", width="stretch")
        except:
            st.warning("Logo não encontrado")

        st.markdown("---")
        st.caption("© 2025 Prefeitura Municipal de Rancharia")

    st.title("📊 Visão Geral do Saneamento")
    st.markdown("---")

    # GRID LAYOUT (3 Colunas)
    col1, col2, col3 = st.columns(3)

    with col1:
        render_card_reservatorio("Caixa da Lavadeira", 50, "Esvaziando")  # Nível baixo

    with col2:
        render_card_reservatorio("Caixa da Lavadeira", 50, "Estavel")  # Nível médio

    with col3:
        render_card_reservatorio("Caixa da Lavadeira", 50, "Enchendo")  # Nível médio


if __name__ == "__main__":
    main()
