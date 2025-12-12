import streamlit as st


def load_css():
    """Lê o arquivo CSS e injeta no Streamlit"""
    with open("assets/css/style.css", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def render_card_reservatorio(titulo, nivel_atual, estado_reservatorio="Estavel"):
    nivel_safe = max(0, min(100, nivel_atual))
    nivel_texto = int(nivel_safe)
    altura_visual = max(5, nivel_safe) if nivel_safe > 0 else 0

    class_estado_reservatorio = (
        "agua-estavel" if estado_reservatorio == "Estavel" else "agua-animada"
    )

    color_estado_reservatorio = (
        "agua-azul-estavel"
        if estado_reservatorio == "Estavel"
        else "agua-azul" if estado_reservatorio == "Enchendo" else "agua-vermelha"
    )

    html_card = f"""
    <div class="card-dashboard">
        <div class="card-title">{titulo}</div>
        <div class="tanque-moderno">
            <div class="{class_estado_reservatorio} {color_estado_reservatorio}" style="height: {altura_visual}%;"></div>
            <div class="texto-porcentagem-moderno">{nivel_texto}%</div>
        </div>
        <div class="text-left">Condição Leitura: Normal</div>
        <div class="text-left">Estado Reservatório: {estado_reservatorio}</div>
    </div>
    """

    st.markdown(html_card, unsafe_allow_html=True)


def render_medidor_caixa(nivel_atual):
    """
    Renderiza o componente visual de caixa d'água.
    """
    # Garante limites entre 0 e 100
    nivel = max(0, min(100, nivel_atual))

    html_caixa = f"""
    <div class="caixa-reservatorio">
        <div class="agua-nivel" style="height: {nivel}%;"></div>
        <div class="texto-porcentagem">{nivel}%</div>
    </div>
    """

    st.markdown(html_caixa, unsafe_allow_html=True)


def render_medidor_caixa_moderno(nivel_atual):
    """
    Renderiza o tanque de vidro moderno com água animada.
    """
    # Garante limites e converte para inteiro para o texto
    nivel_safe = max(0, min(100, nivel_atual))
    nivel_texto = int(nivel_safe)

    # Altura mínima visual para a água não sumir totalmente se for 1% ou 2%
    altura_visual = max(5, nivel_safe) if nivel_safe > 0 else 0

    html_caixa = f"""
    <div class="tanque-moderno">
        <div class="agua-animada" style="height: {altura_visual}%;"></div>
        <div class="texto-porcentagem-moderno">{nivel_texto}%</div>
    </div>
    """

    st.markdown(html_caixa, unsafe_allow_html=True)
