import streamlit as st
import os
from datetime import datetime, timedelta
import time
import pytz
import base64
import src.ui.dashboards as dashboards

# Seus módulos
from src.controllers.Sensor import Sensor
from src.controllers.Rele import Rele
from src.ui.components import (
    load_css,
    render_card_reservatorio_topo,
    render_header_telemetria,
)

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="Telemetria", page_icon="💧", layout="wide")
BRAZIL_TZ = pytz.timezone("America/Sao_Paulo")
INTERVALO_ATUALIZACAO_SEG = 190  # 3 minutos

# Rele IE Tecnologia
id_rele = os.getenv("RELE_IE")
rele = Rele(id_rele)

# Instancia sensor e carrega CSS
sensor = Sensor()
load_css()


# FUNÇÃO AUXILIAR PARA LER A LOGO
def get_img_as_base64(file_path):
    try:
        with open(file_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except Exception as e:
        return None


logo_b64 = get_img_as_base64("assets/img/logo-dark-rancharia.svg")

# CSS e Header
st.markdown(
    """
    <style>
        .block-container { padding-top: 3.5rem; padding-bottom: 3rem; }
        #MainMenu {visibility: hidden;}
    </style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div style="
        display: flex; align-items: center; gap: 20px; margin-bottom: 25px; 
        background-color: #262A3B; padding: 10px 20px; border-radius: 12px; 
        border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    ">
        <img src="data:image/svg+xml;base64,{logo_b64}" 
            style="width: 150px; height: 100; filter: drop-shadow(0px 0px 2px rgba(255,255,255,0.3));">
        <div style="line-height: 1.2; border-left: 1px solid #444; padding-left: 20px;">
            <h3 style="margin: 0; font-size: 1.5rem; font-weight: 700; color: #E0E6ED;">
                Telemetria do SAE
            </h3>
            <span style="font-size: 1rem; color: #00ADB5; font-weight: 500;">
                Rancharia/SP
            </span>
        </div>
    </div>
""",
    unsafe_allow_html=True,
)

# --- ESTADOS GLOBAIS ---
if "config_bombas" not in st.session_state:
    # IMPORTANTE: Na inicialização (F5), lemos o hardware real.
    # Depois disso, confiamos na memória para ser rápido.
    st.session_state["config_bombas"] = {
        "bomba_principal": {"nome": "Bomba Principal (Simulação)", "ligada": False},
        "bomba_12": {
            "nome": "Bomba 12 Polegadas",
            "ligada": rele.get_status_bomba(),
        },
        "bomba_12_reserva": {"nome": "Bomba 12 Pol (Reserva)", "ligada": False},
    }

if "confirmacao_pendente" not in st.session_state:
    st.session_state["confirmacao_pendente"] = None

# --- ESTADOS DE FILTRO ---
if "data_inicio_padrao" not in st.session_state:
    st.session_state["data_inicio_padrao"] = datetime.now(BRAZIL_TZ) - timedelta(days=1)
if "data_final_padrao" not in st.session_state:
    st.session_state["data_final_padrao"] = datetime.now(BRAZIL_TZ)


# --- FRAGMENTO AUTOMÁTICO ---
@st.fragment(run_every=INTERVALO_ATUALIZACAO_SEG)
def painel_telemetria_auto_update():

    # 1. Leitura de Sensores (Reservatório)
    perc, status = sensor.get_status_reservatorio()
    data_base = sensor.get_tempo_pin()
    data_base = datetime.strptime(data_base, "%d/%m/%Y %H:%M:%S")
    data_base = data_base.replace(tzinfo=BRAZIL_TZ)

    prox_atualizacao = (
        data_base + timedelta(seconds=INTERVALO_ATUALIZACAO_SEG)
    ).strftime("%H:%M:%S")

    dados = {
        "nivel": perc,
        "status": status,
        "mA": sensor.get_vl_mA(),
        "hora": sensor.get_tempo_pin(),
        "local": sensor.get_local(),
    }

    # Header do Painel
    st.markdown(
        f"""
        <div style="background-color:#1E1E1E; padding:15px; border-radius:10px; display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
            <span style="color:#FFF; font-size:1.2rem;">⏱️ Última Leitura: <b>{dados['hora']}</b></span>
            <span style="color:#00ADB5; font-size:1.0rem;">Próxima atualização: <b>{prox_atualizacao}</b></span>
        </div>
    """,
        unsafe_allow_html=True,
    )

    col_monitor, col_controle = st.columns([1, 2])

    # Coluna 1: Reservatório
    with col_monitor:
        with st.container(border=True):
            render_card_reservatorio_topo(
                f"Caixa da {dados['local']}",
                dados["nivel"],
                dados["mA"],
                dados["status"],
            )

    # Coluna 2: Bombas
    with col_controle:
        with st.container(border=True):
            st.markdown("##### ⚙️ Painel de Controle de Bombas")
            st.info("Clique para armar, clique novamente para confirmar.")

            chaves = list(st.session_state["config_bombas"].keys())

            for chave in chaves:
                bomba = st.session_state["config_bombas"][chave]

                with st.container(border=True):
                    c1, c2, c3 = st.columns([2, 1, 1])

                    # Nome
                    with c1:
                        st.markdown(
                            f"<div style='padding-top:5px; font-weight:bold;'>{bomba['nome']}</div>",
                            unsafe_allow_html=True,
                        )

                    # Luzinha (Status Visual)
                    with c2:
                        # Aqui usamos o session_state, que será atualizado INSTANTANEAMENTE pelo botão
                        is_ligada = bomba["ligada"]
                        cor = "#2ECC71" if is_ligada else "#FF6B6B"
                        txt = "LIGADA" if is_ligada else "PARADA"
                        st.markdown(
                            f"<div style='text-align:center; color:{cor}; font-weight:500; border:1px solid {cor}; border-radius:4px; padding:6px;'>● {txt}</div>",
                            unsafe_allow_html=True,
                        )

                    # Botão de Ação
                    with c3:
                        if st.session_state.get("confirmacao_pendente") == chave:
                            lbl = "CONFIRMAR?"
                            tp = "primary"
                        else:
                            lbl = "DESLIGAR" if is_ligada else "LIGAR"
                            tp = "secondary"

                        # --- CALLBACK OTIMISTA (A SOLUÇÃO) ---
                        def on_click_bomba(k=chave):
                            # Verifica confirmação
                            if st.session_state.get("confirmacao_pendente") == k:

                                # 1. Define o que queremos fazer (Inverter o estado atual)
                                estado_atual = st.session_state["config_bombas"][k][
                                    "ligada"
                                ]
                                novo_estado = not estado_atual

                                # 2. ATUALIZA A TELA IMEDIATAMENTE (Mentira do bem)
                                # O usuário vê a luz mudar na hora, sem esperar hardware.
                                st.session_state["config_bombas"][k][
                                    "ligada"
                                ] = novo_estado

                                # 3. ENVIA COMANDO AO HARDWARE EM BACKGROUND
                                if k == "bomba_12":
                                    if novo_estado:
                                        rele.LIGAR_BOMBA()
                                    else:
                                        rele.DESLIGAR_BOMBA()
                                    # Não lemos o retorno aqui para não travar.
                                    # Confiamos que o hardware funciona.
                                else:
                                    pass  # Simulação já foi atualizada no passo 2

                                st.session_state["confirmacao_pendente"] = None

                            else:
                                # Primeiro clique
                                st.session_state["confirmacao_pendente"] = k

                        st.button(
                            lbl,
                            key=f"btn_{chave}",
                            type=tp,
                            on_click=on_click_bomba,
                            use_container_width=True,
                        )


# --- CHAMADA PRINCIPAL ---

painel_telemetria_auto_update()

st.markdown("---")

# Dashboards (Filtros e Gráficos)
with st.container(border=True):
    col1_data, col2_data = st.columns(2)
    with col1_data:
        data_inicio = st.datetime_input(
            "Data de Inicio:",
            value=st.session_state["data_inicio_padrao"],
            key="input_data_inicio",
        )
    with col2_data:
        data_final = st.datetime_input(
            "Data Final:",
            value=st.session_state["data_final_padrao"],
            key="input_data_final",
        )

if data_inicio and data_final:
    if data_final < data_inicio:
        st.error("⚠️ Erro: A Data Final deve ser maior que a Data de Início.")
        st.stop()

with st.container(border=True):
    fig = dashboards.create_graph_line(data_inicio, data_final)
    st.plotly_chart(fig, width="stretch")

with st.container(border=True):
    fig_bar = dashboards.create_graph_bar(data_inicio, data_final)
    st.plotly_chart(fig_bar, width="stretch")
