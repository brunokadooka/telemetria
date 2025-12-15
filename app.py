import streamlit as st
import time
from datetime import datetime
from src.ui.components import *
from src.controllers.Sensor import Sensor

# --- 1. Configuração (Sempre a primeira linha) ---
st.set_page_config(
    page_title="Telemetria Saneamento",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- 2. Inicialização de Memória (Session State) ---
# Isso garante que o sistema lembre o estado das bombas e o tempo do status
if "bombas" not in st.session_state:
    st.session_state["bombas"] = {
        "Bomba 8 Polegadas": True,  # Começa ligada (exemplo)
        "Bomba 12 Polegadas": False,
        "Bomba Auxiliar": False,
    }

if "monitor_status" not in st.session_state:
    st.session_state["monitor_status"] = {
        "ultimo_status": None,
        "data_inicio": datetime.now(),
    }

# --- 3. Instância do Sensor ---
sensor = Sensor()

# Ocultar menu padrão
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# Carregar CSS
load_css()

# --- 4. Funções Auxiliares (Modal e Lógica de Tempo) ---


@st.dialog("⚠️ Confirmação de Segurança")
def modal_confirmacao(nome_bomba, acao, estado_atual):
    """
    Modal que bloqueia a tela e pede confirmação antes de ligar/desligar.
    """
    cor = "green" if acao == "LIGAR" else "red"
    icone = "⚡" if acao == "LIGAR" else "🛑"

    st.markdown(f"Você está prestes a **:{cor}[{acao}]** a **{nome_bomba}**.")
    st.caption("Esta ação enviará um comando físico para o CLP na estação remota.")

    col_btn1, col_btn2 = st.columns(2)

    with col_btn1:
        if st.button(
            f"{icone} Confirmar {acao}", type="primary", use_container_width=True
        ):
            # AQUI ENTRARIA O COMANDO PARA O SENSOR/CLP
            # Ex: sensor.enviar_comando(nome_bomba, acao)

            # Atualiza o estado visual na memória
            st.session_state["bombas"][nome_bomba] = not estado_atual

            st.success(f"Comando enviado com sucesso!")
            time.sleep(1)  # Pausa dramática para leitura
            st.rerun()  # Recarrega a página para atualizar o botão

    with col_btn2:
        if st.button("Cancelar", use_container_width=True):
            st.rerun()


def calcular_tempo_status(status_atual):
    """
    Verifica se o status mudou. Se mudou, zera o cronômetro.
    Se não, retorna o tempo formatado.
    """
    memoria = st.session_state["monitor_status"]

    # Se o status mudou desde a última renderização
    if status_atual != memoria["ultimo_status"]:
        memoria["ultimo_status"] = status_atual
        memoria["data_inicio"] = datetime.now()
        st.session_state["monitor_status"] = memoria  # Salva
        return "Há instantes"

    # Se o status é o mesmo, calcula a diferença
    delta = datetime.now() - memoria["data_inicio"]
    segundos = int(delta.total_seconds())

    horas, resto = divmod(segundos, 3600)
    minutos, _ = divmod(resto, 60)

    if horas > 0:
        return f"Há {horas}h {minutos}min"
    elif minutos > 0:
        return f"Há {minutos} min"
    else:
        return "Há instantes"


def render_controle_bomba_seguro(nome_bomba):
    """
    Substitui o render_card_bomba antigo para adicionar interatividade.
    """
    esta_ligada = st.session_state["bombas"][nome_bomba]

    # Define visual baseado no estado
    status_txt = "LIGADA" if esta_ligada else "DESLIGADA"
    status_cor = "🟢" if esta_ligada else "🔴"
    acao_botao = "DESLIGAR" if esta_ligada else "LIGAR"
    tipo_botao = "secondary" if esta_ligada else "primary"  # Destaca o LIGAR

    # Container para agrupar visualmente (Card)
    with st.container(border=True):
        c1, c2 = st.columns([3, 1.5])

        with c1:
            st.markdown(f"**⚡ {nome_bomba}**")
            st.caption(f"{status_cor} {status_txt}")

        with c2:
            # Botão que aciona o Modal
            if st.button(
                acao_botao,
                key=f"btn_{nome_bomba}",
                type=tipo_botao,
                use_container_width=True,
            ):
                modal_confirmacao(nome_bomba, acao_botao, esta_ligada)


# --- 5. Função Principal ---
def main():
    # --- Sidebar ---
    with st.sidebar:
        try:
            st.image("assets/img/logo.png")
        except:
            st.warning("Logo não encontrado")

        st.markdown("---")
        st.caption("© 2025 Prefeitura Municipal de Rancharia")

    # --- Lógica do Sensor e Tempo ---
    # Precisamos pegar os dados ANTES de desenhar para calcular o tempo
    # Assumindo que seu Sensor retorna (media, status) na função get_status_reservatorio
    # Se retornar só string, ajuste a linha abaixo.

    # IMPORTANTE: Estou assumindo que get_status_reservatorio retorna TUPLA ou STRING.
    # Ajustei para ser robusto:
    dados_sensor = sensor.get_status_reservatorio()

    # Tratamento caso venha tupla (media, status) ou só string
    if isinstance(dados_sensor, tuple):
        status_atual_texto = dados_sensor[1]
    else:
        status_atual_texto = str(dados_sensor)

    # Calcula o tempo baseado na memória
    tempo_decorrido = calcular_tempo_status(status_atual_texto)

    # --- Header ---
    st.title("📊 Visão Geral do Saneamento")
    st.write(f"⏰ Telemetria Capturada: {sensor.get_tempo_pin()}")
    st.markdown("---")

    # --- GRID LAYOUT ---
    col_tanque, col_bombas = st.columns([1, 1.2])

    with col_tanque:
        # CORREÇÃO: Passando os argumentos por posição (na ordem) e removendo os nomes (keywords)
        render_card_reservatorio(
            sensor.get_local(),  # 1º: Local
            sensor.get_vl_percentual(),  # 2º: Percentual
            sensor.get_vl_mA(),  # 3º: Valor em mA
            status_atual_texto,  # 4º: Status (Texto)
            "~ 15min",  # 5º: Tempo (Onde antes você passava o status repetido)
        )

    with col_bombas:
        st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
        st.subheader("⚙️ Controle de Bombas")

        # Renderiza as bombas ITERATIVAMENTE usando o estado seguro
        for nome_bomba in st.session_state["bombas"].keys():
            render_controle_bomba_seguro(nome_bomba)


if __name__ == "__main__":
    main()
