import streamlit as st


def load_css():
    """Lê o arquivo CSS e injeta no Streamlit"""
    with open("assets/css/style.css", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def render_card_reservatorio(
    titulo, nivel_atual, vl_mA, estado_reservatorio="Estavel", tempo_decorrido="--"
):
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

    # Lógica do ícone do timer
    icone_tempo = "⏳" if estado_reservatorio != "Estavel" else "⏱️"

    html_card = f"""
    <div class="card-dashboard">
        <div class="card-title">{titulo}</div>
        <div class="tanque-moderno">
            <div class="{class_estado_reservatorio} {color_estado_reservatorio}" style="height: {altura_visual}%;"></div>
            <div class="texto-porcentagem-moderno">{nivel_texto}%</div>
            <div class="texto-moderno">{vl_mA} mA</div>
        </div>
        <div style="margin-top: 15px; font-weight: bold; color: #495057;">
            {estado_reservatorio}
        </div>
        <div class="timer-badge">
            <span class="icon-clock">{icone_tempo}</span> {tempo_decorrido}
        </div>
        <div style="font-size: 0.8rem; color: #adb5bd; margin-top: 5px;">
            Leitura: Normal
        </div>
    </div>
    """

    st.markdown(html_card, unsafe_allow_html=True)


def render_card_bomba(nome, status_ligado=False):
    """
    Renderiza um card horizontal para controle de bomba.
    status_ligado: True (Ligado/Verde) ou False (Desligado/Vermelho)
    """

    # Define classes CSS baseadas no estado
    if status_ligado:
        texto_status = "LIGADA"
        classe_status = "status-on"
        class_btn_on = "btn-toggle btn-active-on"
        class_btn_off = "btn-toggle btn-inactive"
    else:
        texto_status = "DESLIGADA"
        classe_status = "status-off"
        class_btn_on = "btn-toggle btn-inactive"
        class_btn_off = "btn-toggle btn-active-off"

    html_bomba = f"""
    <div class="card-bomba">
        <div>
            <div class="bomba-titulo">⚡ {nome}</div>
            <div class="bomba-status {classe_status}">
                ● {texto_status}
            </div>
        </div>
        <div class="toggle-container">
            <button class="{class_btn_on}">ON</button>
            <button class="{class_btn_off}">OFF</button>
        </div>
    </div>
    """
    st.markdown(html_bomba, unsafe_allow_html=True)
